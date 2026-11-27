import json
import requests

from pathlib import Path

# 1. CONFIGURATION

BASE_DIR = Path(__file__).resolve().parents[2]

SELECTED_FILE = BASE_DIR / "data" / "sentinel2_selected.json"
OUTPUT_FILE = BASE_DIR / "data" / "sentinel2_product.json"

STAC_URL = (
    "https://stac.dataspace.copernicus.eu/v1/collections/"
    "sentinel-2-l2a/items/"
)

# 2. CHARGEMENT DE L'IDENTIFIANT

with open(SELECTED_FILE, "r", encoding="utf-8") as file:
    selected = json.load(file)

product_id = selected["id"]

print("Produit sélectionné :", product_id)

# 3. RECUPERATION DES METADONNEES


url = STAC_URL + product_id

response = requests.get(url, timeout=60)
response.raise_for_status()

product = response.json()

if product.get("id") != product_id:
    raise ValueError("L'identifiant du produit ne correspond pas.")

# 4. EXTRACTION DES ASSETS

required_assets = [
    "B02_10m",
    "B03_10m",
    "B04_10m",
    "B08_10m",
    "SCL_20m"
]

assets = product.get("assets", {})

result = {}

for asset_name in required_assets:

    if asset_name not in assets:
        raise ValueError(f"Asset introuvable : {asset_name}")

    asset = assets[asset_name]

    https_info = asset.get("alternate", {}).get("https", {})
    href = https_info.get("href")

    if not href:
        raise ValueError(
            f"Lien HTTPS introuvable pour {asset_name}"
        )

    result[asset_name] = {
        "href": href,
        "gsd": asset.get("gsd"),
        "type": asset.get("type"),
        "nodata": asset.get("nodata"),
        "size_bytes": asset.get("file:size"),
        "local_path": asset.get("file:local_path")
    }

# 5. SAUVEGARDE


output = {
    "id": product["id"],
    "collection": product["collection"],
    "acquisition_date": product["properties"]["datetime"],
    "cloud_cover": product["properties"]["eo:cloud_cover"],
    "crs": "EPSG:32631",
    "assets": result
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(output, file, indent=4, ensure_ascii=False)

# 6. AFFICHAGE DES INFORMATIONS


print("Identifiant :", output["id"])
print("Date d'acquisition :", output["acquisition_date"])
print("Couverture nuageuse :", output["cloud_cover"], "%")
print("Projection :", output["crs"])


total_size = 0

for name, info in result.items():

    print(f"\n{name}")
    print("-" * 40)

    print(f"Résolution : {info['gsd']} m")
    print(f"Type : {info['type']}")
    print(f"NoData : {info['nodata']}")

    size = info["size_bytes"]

    if size is not None:
        size_mb = size / (1024 ** 2)
        total_size += size

        print(f"Taille : {size_mb:.2f} Mo")
    else:
        print("Taille : non renseignée")

    print(f"Chemin produit : {info['local_path']}")


print(
    f"Taille totale des 5 assets : "
    f"{total_size / (1024 ** 2):.2f} Mo"
)

print("\nMétadonnées sauvegardées :", OUTPUT_FILE)
