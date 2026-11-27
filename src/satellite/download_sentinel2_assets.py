import os
import json
import requests

from pathlib import Path
from dotenv import load_dotenv

# 1. CONFIGURATION

BASE_DIR = Path(__file__).resolve().parents[2]

PRODUCT_FILE = BASE_DIR / "data" / "sentinel2_product.json"
OUTPUT_DIR = BASE_DIR / "data" / "satellite" / "raw" / "sentinel2_assets"

ENV_FILE = BASE_DIR / ".env"

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ENV_FILE, override=True)

USERNAME = os.getenv("CDSE_USERNAME")
PASSWORD = os.getenv("CDSE_PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError(
        "Identifiants du compte CDSE absents du fichier .env"
    )

# 2. CHARGEMENT DU PRODUIT

with open(PRODUCT_FILE, "r", encoding="utf-8") as file:
    product = json.load(file)

print("Produit :", product["id"])
print("Date :", product["acquisition_date"])

# 3. AUTHENTIFICATION ODATA CDSE

print("\nAuthentification OData CDSE...")

response = requests.post(
    TOKEN_URL,
    data={
        "client_id": "cdse-public",
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    },
    timeout=60
)

if not response.ok:
    print("\nERREUR AUTHENTIFICATION CDSE")
    print("Code HTTP :", response.status_code)
    print("Réponse :", response.text)
    response.raise_for_status()

token = response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

print("Authentification OData réussie !")
# 4. TELECHARGEMENT DES ASSETS

for asset_name, asset_info in product["assets"].items():

    url = asset_info["href"]

    filename = asset_info["local_path"].split("/")[-1]

    output_file = OUTPUT_DIR / filename

    expected_size = asset_info.get("size_bytes")

    print(f"\nTéléchargement : {asset_name}")
    print("Fichier :", filename)

    # Éviter de retélécharger un fichier déjà complet.
    if (
        output_file.exists()
        and expected_size is not None
        and output_file.stat().st_size == expected_size
    ):
        print("Fichier déjà téléchargé et vérifié.")
        continue

    temporary_file = output_file.with_suffix(
        output_file.suffix + ".part"
    )

    downloaded = 0

    with requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=(30, 180)
    ) as download_response:

        download_response.raise_for_status()

        with open(temporary_file, "wb") as file:

            for chunk in download_response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)

    # Vérification de la taille
    if (
        expected_size is not None
        and downloaded != expected_size
    ):
        temporary_file.unlink(missing_ok=True)

        raise ValueError(
            f"Taille incorrecte pour {asset_name} : "
            f"{downloaded} au lieu de {expected_size} octets"
        )

    temporary_file.replace(output_file)

    print(
        f"Téléchargement terminé : "
        f"{downloaded / (1024 ** 2):.2f} Mo"
    )

print("Dossier :", OUTPUT_DIR)
