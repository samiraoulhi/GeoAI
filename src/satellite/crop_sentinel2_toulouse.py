import json
import math

import rasterio

from pathlib import Path
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.crs import CRS


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

PRODUCT_FILE = BASE_DIR / "data" / "sentinel2_product.json"
SELECTED_FILE = BASE_DIR / "data" / "sentinel2_selected.json"

ASSETS_DIR = (
    BASE_DIR / "data" / "satellite" / "raw" / "sentinel2_assets"
)

OUTPUT_DIR = (
    BASE_DIR / "data" / "satellite" / "processed" / "toulouse"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Zone géographique de Toulouse en EPSG:4326
BBOX = [
    1.4242,
    43.5845,
    1.4642,
    43.6245
]

SOURCE_CRS = "EPSG:4326"
TARGET_CRS = "EPSG:32631"

BANDS_10M = [
    "B02_10m",
    "B03_10m",
    "B04_10m",
    "B08_10m"
]

SCL_BAND = "SCL_20m"

EXPECTED_OUTPUTS = [
    OUTPUT_DIR / f"toulouse_{band}.tif"
    for band in BANDS_10M
] + [
    OUTPUT_DIR / "toulouse_SCL_10m.tif"
]

METADATA_OUTPUT = OUTPUT_DIR / "toulouse_processing_metadata.json"


# ==========================================
# 2. FONCTIONS UTILITAIRES
# ==========================================

def get_acquisition_id(product, selected):

    acquisition_id = (
        product.get("id")
        or product.get("product_id")
        or selected.get("id")
        or selected.get("product_id")
    )

    if acquisition_id is None:
        raise ValueError(
            "Impossible de retrouver l'identifiant de l'acquisition."
        )

    return acquisition_id


def get_asset_file(product, band_name):

    if band_name not in product.get("assets", {}):
        raise ValueError(f"Asset absent des métadonnées : {band_name}")

    local_path = product["assets"][band_name].get("local_path")

    if not local_path:
        raise ValueError(f"Chemin local absent : {band_name}")

    filepath = ASSETS_DIR / Path(local_path).name

    if not filepath.exists():
        raise FileNotFoundError(
            f"Fichier Sentinel-2 introuvable : {filepath}"
        )

    return filepath


# ==========================================
# 3. CHARGEMENT DES METADONNEES
# ==========================================

print("\n========== CHARGEMENT DES METADONNEES ==========")

if not PRODUCT_FILE.exists():
    raise FileNotFoundError(PRODUCT_FILE)

if not SELECTED_FILE.exists():
    raise FileNotFoundError(SELECTED_FILE)

with open(PRODUCT_FILE, "r", encoding="utf-8") as file:
    product = json.load(file)

with open(SELECTED_FILE, "r", encoding="utf-8") as file:
    selected = json.load(file)

acquisition_id = get_acquisition_id(product, selected)

print("Acquisition :", acquisition_id)

# Vérification des cinq fichiers sources
for band in BANDS_10M + [SCL_BAND]:
    filepath = get_asset_file(product, band)
    print(f"{band} : OK - {filepath.name}")


# ==========================================
# 4. NETTOYAGE DES ANCIENS RESULTATS
# ==========================================

print("\n========== NETTOYAGE DES ANCIENS RESULTATS ==========")

for filepath in EXPECTED_OUTPUTS + [METADATA_OUTPUT]:

    if filepath.exists():
        filepath.unlink()
        print("Ancien fichier supprimé :", filepath.name)


# ==========================================
# 5. CONVERSION DES COORDONNEES
# ==========================================

projected_bounds = transform_bounds(
    SOURCE_CRS,
    TARGET_CRS,
    *BBOX,
    densify_pts=21
)

print("\n========== DECOUPAGE SENTINEL-2 ==========")

print("\nEmprise Toulouse en EPSG:32631 :")
print(projected_bounds)


# ==========================================
# 6. CALCUL DE LA FENETRE DE DECOUPAGE
# ==========================================

reference_file = get_asset_file(product, "B04_10m")

with rasterio.open(reference_file) as src:

    if src.crs is None:
        raise ValueError("Projection absente sur B04.")

    if src.crs != CRS.from_string(TARGET_CRS):
        raise ValueError("Projection B04 inattendue.")

    if src.count != 1:
        raise ValueError("B04 doit contenir une seule bande.")

    raw_window = from_bounds(
        *projected_bounds,
        transform=src.transform
    )

    col_start = math.floor(raw_window.col_off)
    row_start = math.floor(raw_window.row_off)

    col_stop = math.ceil(
        raw_window.col_off + raw_window.width
    )

    row_stop = math.ceil(
        raw_window.row_off + raw_window.height
    )

    # Limitation aux dimensions de l'image
    col_start = max(0, col_start)
    row_start = max(0, row_start)

    col_stop = min(src.width, col_stop)
    row_stop = min(src.height, row_stop)

    if col_stop <= col_start or row_stop <= row_start:
        raise ValueError(
            "La zone demandée ne recoupe pas l'image Sentinel-2."
        )

    crop_window = Window(
        col_start,
        row_start,
        col_stop - col_start,
        row_stop - row_start
    )

    reference_transform = src.window_transform(crop_window)

    reference_width = int(crop_window.width)
    reference_height = int(crop_window.height)

    reference_profile = src.profile.copy()

    reference_profile.update(
        driver="GTiff",
        width=reference_width,
        height=reference_height,
        count=1,
        transform=reference_transform,
        crs=TARGET_CRS,
        compress="deflate"
    )

print("\nDimensions de la zone découpée :")
print(reference_width, "x", reference_height)

print("Projection :", TARGET_CRS)


# ==========================================
# 7. DECOUPAGE DES BANDES SPECTRALES 10 M
# ==========================================

print("\n========== BANDES SPECTRALES 10 M ==========")

for band_name in BANDS_10M:

    input_file = get_asset_file(product, band_name)

    output_file = OUTPUT_DIR / f"toulouse_{band_name}.tif"

    print(f"\nTraitement : {band_name}")

    with rasterio.open(input_file) as src:

        if src.crs != CRS.from_string(TARGET_CRS):
            raise ValueError(
                f"Projection incorrecte : {band_name}"
            )

        

        # Vérification de l'alignement avec B04
        with rasterio.open(reference_file) as reference:

            if src.transform != reference.transform:
                raise ValueError(
                    f"Grille différente : {band_name}"
                )

            if src.width != reference.width:
                raise ValueError(
                    f"Largeur différente : {band_name}"
                )

            if src.height != reference.height:
                raise ValueError(
                    f"Hauteur différente : {band_name}"
                )

        data = src.read(1, window=crop_window)

        profile = reference_profile.copy()
        profile.update(dtype=src.dtypes[0])

        with rasterio.open(output_file, "w", **profile) as dst:
            dst.write(data, 1)

    print("Fichier créé :", output_file.name)
    print("Dimensions :", data.shape)


# ==========================================
# 8. REECHANTILLONNAGE DE SCL A 10 M
# ==========================================

print("\n========== TRAITEMENT SCL ==========")

scl_input = get_asset_file(product, SCL_BAND)

scl_output = OUTPUT_DIR / "toulouse_SCL_10m.tif"

scl_profile = reference_profile.copy()

scl_profile.update(
    driver="GTiff",
    dtype="uint8",
    count=1,
    nodata=0
)

with rasterio.open(scl_input) as src:

    if src.crs != CRS.from_string(TARGET_CRS):
        raise ValueError("Projection SCL incorrecte.")

    if src.count != 1:
        raise ValueError("SCL doit contenir une seule bande.")

    with rasterio.open(scl_output, "w", **scl_profile) as dst:

        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=reference_transform,
            dst_crs=TARGET_CRS,
            resampling=Resampling.nearest,
            dst_nodata=0,
            init_dest_nodata=True
        )

print("SCL rééchantillonnée à 10 m.")
print("Fichier créé :", scl_output.name)


# ==========================================
# 9. VERIFICATION FINALE
# ==========================================

print("\n========== VERIFICATION FINALE ==========")

for filepath in EXPECTED_OUTPUTS:

    if not filepath.exists():
        raise FileNotFoundError(
            f"Fichier de sortie absent : {filepath.name}"
        )

    with rasterio.open(filepath) as src:

        print(f"\n{filepath.name}")
        print("Dimensions :", src.width, "x", src.height)
        print("Résolution :", src.res)
        print("Projection :", src.crs)
        print("Type :", src.dtypes)

        if src.width != reference_width:
            raise ValueError("Largeur incorrecte après découpage.")

        if src.height != reference_height:
            raise ValueError("Hauteur incorrecte après découpage.")

        if src.crs != CRS.from_string(TARGET_CRS):
            raise ValueError("Projection incorrecte après découpage.")

        if src.transform != reference_transform:
            raise ValueError("Transformation incorrecte après découpage.")


# ==========================================
# 10. SAUVEGARDE DES METADONNEES
# ==========================================

metadata = {
    "acquisition_id": acquisition_id,
    "acquisition_date": (
        selected.get("date")
        or selected.get("datetime")
    ),
    "cloud_cover": selected.get("cloud_cover"),
    "city": "Toulouse",
    "bbox_epsg4326": BBOX,
    "crs": TARGET_CRS,
    "resolution_m": 10,
    "width": reference_width,
    "height": reference_height,
    "bands": BANDS_10M + ["SCL_10m"],
    "processed_files": [
        filepath.name for filepath in EXPECTED_OUTPUTS
    ]
}

with open(METADATA_OUTPUT, "w", encoding="utf-8") as file:
    json.dump(metadata, file, indent=4, ensure_ascii=False)

print("\nMétadonnées enregistrées :")
print(METADATA_OUTPUT)

print("\n========== DECOUPAGE TERMINE AVEC SUCCES ==========")