import os
import json
import requests
import rasterio
import numpy as np

from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from rasterio.io import MemoryFile

# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)

PROCESS_URL = "https://sh.dataspace.copernicus.eu/process/v1"

BBOX = [
    1.4242,
    43.5845,
    1.4642,
    43.6245
]

WIDTH = 400
HEIGHT = 400

EXPECTED_BANDS = 5

SELECTED_FILE = BASE_DIR / "data" / "sentinel2_selected.json"

OUTPUT_DIR = BASE_DIR / "data" / "satellite" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "toulouse_sentinel2_bands_scl.tif"

# ==========================================
# 2. CHARGEMENT DE L'ACQUISITION
# ==========================================

print("\n========== ACQUISITION SELECTIONNEE ==========")

if not SELECTED_FILE.exists():
    raise FileNotFoundError(
        f"Fichier introuvable : {SELECTED_FILE}"
    )

with open(SELECTED_FILE, "r", encoding="utf-8") as file:
    selected_image = json.load(file)

if not selected_image.get("id") or not selected_image.get("date"):
    raise ValueError("Identifiant ou date STAC manquant.")

acquisition_date = datetime.fromisoformat(
    selected_image["date"].replace("Z", "+00:00")
)

acquisition_date = acquisition_date.astimezone(timezone.utc)

start_date = acquisition_date.replace(
    hour=0,
    minute=0,
    second=0,
    microsecond=0
)

end_date = start_date + timedelta(days=1)

print("ID :", selected_image["id"])
print("Date :", acquisition_date.isoformat())
print("Couverture nuageuse :", selected_image["cloud_cover"], "%")
print("Début UTC :", start_date.isoformat())
print("Fin UTC :", end_date.isoformat())

# ==========================================
# 3. AUTHENTIFICATION
# ==========================================

print("\n========== AUTHENTIFICATION ==========")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError(
        "Identifiants Copernicus absents du fichier .env"
    )

token_response = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    },
    timeout=30
)

token_response.raise_for_status()

access_token = token_response.json().get("access_token")

if not access_token:
    raise RuntimeError("Impossible de récupérer le token.")

print("Authentification réussie.")

# ==========================================
# 4. EVALSCRIPT SENTINEL-2
# ==========================================

evalscript = """
//VERSION=3

function setup() {
    return {
        input: [{
            bands: ["B04", "B03", "B02", "B08", "SCL"]
        }],
        output: {
            bands: 5,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(sample) {
    return [
        sample.B04,
        sample.B03,
        sample.B02,
        sample.B08,
        sample.SCL
    ];
}
"""

# ==========================================
# 5. PREPARATION DE LA REQUETE
# ==========================================

payload = {
    "input": {
        "bounds": {
            "bbox": BBOX,
            "properties": {
                "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
            }
        },
        "data": [{
            "type": "S2L2A",
            "dataFilter": {
                "timeRange": {
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat()
                },
                "mosaickingOrder": "leastCC"
            }
        }]
    },
    "output": {
        "width": WIDTH,
        "height": HEIGHT,
        "responses": [{
            "identifier": "default",
            "format": {
                "type": "image/tiff"
            }
        }]
    },
    "evalscript": evalscript
}

# ==========================================
# 6. TELECHARGEMENT
# ==========================================

print("\n========== TELECHARGEMENT SENTINEL-2 ==========")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.post(
    PROCESS_URL,
    headers=headers,
    json=payload,
    timeout=180
)

if not response.ok:
    print("Erreur HTTP :", response.status_code)
    print("Message :", response.text[:2000])
    response.raise_for_status()

if len(response.content) < 10000:
    raise RuntimeError(
        f"Réponse trop petite : {len(response.content)} octets. "
        "Fichier non enregistré."
    )

# ==========================================
# 7. VALIDATION DU TIFF EN MEMOIRE
# ==========================================

print("\n========== VALIDATION DU TIFF ==========")

try:
    with MemoryFile(response.content) as memory_file:

        with memory_file.open() as src:

            if src.count != EXPECTED_BANDS:
                raise ValueError(
                    f"Nombre de bandes incorrect : {src.count}"
                )

            if src.width != WIDTH or src.height != HEIGHT:
                raise ValueError(
                    f"Dimensions incorrectes : "
                    f"{src.width} x {src.height}"
                )

            data = src.read()

            for i in range(EXPECTED_BANDS):

                band = data[i]

                valid = band[
                    np.isfinite(band)
                ]

                if valid.size == 0:
                    raise ValueError(
                        f"Bande {i + 1} sans données."
                    )

                if np.count_nonzero(valid) == 0:
                    raise ValueError(
                        f"Bande {i + 1} entièrement nulle."
                    )

                print(
                    f"Bande {i + 1} : "
                    f"min={valid.min():.4f}, "
                    f"max={valid.max():.4f}, "
                    f"moyenne={valid.mean():.4f}"
                )

            scl_values = np.unique(data[4])

            print("Classes SCL :", scl_values)

            if not np.all(np.isfinite(scl_values)):
                raise ValueError("Valeurs SCL non finies.")

            if not np.all(np.isin(scl_values, np.arange(12))):
                raise ValueError("Valeurs SCL inattendues.")

except Exception as error:

    raise RuntimeError(
        f"Validation du TIFF échouée : {error}"
    ) from error

# ==========================================
# 8. SAUVEGARDE APRES VALIDATION
# ==========================================

with open(OUTPUT_FILE, "wb") as file:
    file.write(response.content)

print("\nImage téléchargée et validée !")
print("Fichier :", OUTPUT_FILE)
print("Taille :", round(OUTPUT_FILE.stat().st_size / 1024, 2), "Ko")
print("Dimensions :", WIDTH, "x", HEIGHT)
print("Nombre de bandes :", EXPECTED_BANDS)

print("\n========== FIN ==========")
