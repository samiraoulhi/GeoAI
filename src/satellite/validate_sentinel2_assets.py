import json
import rasterio

from pathlib import Path

# 1. CONFIGURATION


BASE_DIR = Path(__file__).resolve().parents[2]

PRODUCT_FILE = BASE_DIR / "data" / "sentinel2_product.json"

ASSETS_DIR = (
    BASE_DIR / "data" / "satellite" / "raw" / "sentinel2_assets"
)

REQUIRED_ASSETS = [
    "B02_10m",
    "B03_10m",
    "B04_10m",
    "B08_10m",
    "SCL_20m"
]

EXPECTED_CRS = "EPSG:32631"

# 2. CHARGEMENT DES METADONNEES


if not PRODUCT_FILE.exists():
    raise FileNotFoundError(PRODUCT_FILE)

with open(PRODUCT_FILE, "r", encoding="utf-8") as file:
    product = json.load(file)

assets = product["assets"]

print("\n==VALIDATION SENTINEL-2 ==")
print("Produit :", product["id"])

# 3. VERIFICATION DES ASSETS


errors = []

for asset_name in REQUIRED_ASSETS:

    if asset_name not in assets:
        errors.append(f"Asset absent des métadonnées : {asset_name}")
        continue

    info = assets[asset_name]

    filename = Path(info["local_path"]).name
    filepath = ASSETS_DIR / filename

    print(f"\nAsset : {asset_name}")
    print("-" * 50)

    if not filepath.exists():
        errors.append(f"Fichier introuvable : {filename}")
        print("ERREUR : fichier introuvable")
        continue

    actual_size = filepath.stat().st_size
    expected_size = info.get("size_bytes")

    print(f"Taille : {actual_size / (1024 ** 2):.2f} Mo")

    if expected_size is not None and actual_size != expected_size:
        errors.append(
            f"Taille incorrecte pour {asset_name} : "
            f"{actual_size} au lieu de {expected_size}"
        )

    with rasterio.open(filepath) as src:

        print("Format :", src.driver)
        print("Dimensions :", src.width, "x", src.height)
        print("Nombre de bandes :", src.count)
        print("Résolution :", src.res)
        print("Projection :", src.crs)
        print("Type :", src.dtypes)
        print("Emprise :", src.bounds)

        if src.count != 1:
            errors.append(f"Nombre de bandes incorrect : {asset_name}")

        if src.crs is None:
            errors.append(f"Projection absente : {asset_name}")

        elif src.crs.to_string() != EXPECTED_CRS:
            errors.append(
                f"Projection incorrecte pour {asset_name} : {src.crs}"
            )

        if src.width <= 0 or src.height <= 0:
            errors.append(f"Dimensions invalides : {asset_name}")

    print("Validation individuelle terminée.")

# 4. BILAN


if errors:

    print("VALIDATION ÉCHOUÉE :")

    for error in errors:
        print("-", error)

    raise RuntimeError(
        f"{len(errors)} erreur(s) détectée(s) dans les assets Sentinel-2."
    )

print("Tous les assets sont valides.")
