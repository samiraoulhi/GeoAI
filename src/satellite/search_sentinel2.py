import requests
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

# CONFIGURATION



BASE_DIR = Path(__file__).resolve().parents[2]

STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

LATITUDE = 43.6045
LONGITUDE = 1.4442
DELTA = 0.10

MAX_CLOUD_COVER = 60

end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=30)

# RECHERCHE STAC

payload = {
    "collections": ["sentinel-2-l2a"],
    "datetime": (
        f"{start_date.isoformat()}/"
        f"{end_date.isoformat()}"
    ),
    "bbox": [
        LONGITUDE - DELTA,
        LATITUDE - DELTA,
        LONGITUDE + DELTA,
        LATITUDE + DELTA
    ],
    "limit": 100
}

print("Recherche des images Sentinel-2...")
print(f"Période : {start_date.date()} → {end_date.date()}")

response = requests.post(
    STAC_URL,
    json=payload,
    timeout=60
)

response.raise_for_status()

data = response.json()
features = data.get("features", [])

# FILTRAGE


images = []

for feature in features:

    properties = feature.get("properties", {})
    cloud_cover = properties.get("eo:cloud_cover")

    if cloud_cover is not None and cloud_cover <= MAX_CLOUD_COVER:

        images.append({
            "id": feature.get("id"),
            "date": properties.get("datetime"),
            "cloud_cover": cloud_cover,
            "collection": feature.get("collection")
        })

# SELECTION DE LA MEILLEURE IMAGE


images.sort(
    key=lambda x: x["cloud_cover"]
)

print("\n== RÉSULTATS ==")
print("Images trouvées :", len(features))
print("Images après filtrage :", len(images))

if not images:
    raise RuntimeError("Aucune image Sentinel-2 disponible.")

selected_image = images[0]

print("\n==IMAGE SÉLECTIONNÉE ==")
print("ID :", selected_image["id"])
print("Date :", selected_image["date"])
print("Nuages :", selected_image["cloud_cover"], "%")

# =====================================
# SAUVEGARDE
# =====================================

output_path = BASE_DIR / "data" / "sentinel2_selected.json"

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(
        selected_image,
        file,
        indent=4,
        ensure_ascii=False
    )

print("\nImage sélectionnée sauvegardée dans :")
print(output_path)
