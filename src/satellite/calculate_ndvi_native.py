import json
import numpy as np
import rasterio
import matplotlib.pyplot as plt

from pathlib import Path

# 1. CONFIGURATION


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_DIR = (
    BASE_DIR / "data" / "satellite" / "processed" / "toulouse"
)

SELECTED_FILE = BASE_DIR / "data" / "sentinel2_selected.json"

METADATA_FILE = INPUT_DIR / "toulouse_processing_metadata.json"

RED_FILE = INPUT_DIR / "toulouse_B04_10m.tif"
NIR_FILE = INPUT_DIR / "toulouse_B08_10m.tif"
SCL_FILE = INPUT_DIR / "toulouse_SCL_10m.tif"

NDVI_FILE = INPUT_DIR / "toulouse_ndvi_native_masked.tif"
PNG_FILE = INPUT_DIR / "toulouse_ndvi_native_masked.png"
STATS_FILE = INPUT_DIR / "toulouse_ndvi_native_statistics.json"

VALID_CLASSES = [4, 5, 6]
NODATA_VALUE = -9999.0

# 2. VERIFICATION DES FICHIERS

required_files = [
    SELECTED_FILE,
    METADATA_FILE,
    RED_FILE,
    NIR_FILE,
    SCL_FILE
]

for filepath in required_files:

    if not filepath.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {filepath}"
        )

# 3. IDENTIFICATION DE L'ACQUISITION


with open(SELECTED_FILE, "r", encoding="utf-8") as file:
    selected_product = json.load(file)

with open(METADATA_FILE, "r", encoding="utf-8") as file:
    processing_metadata = json.load(file)

acquisition_id = selected_product["id"]

if acquisition_id != processing_metadata["acquisition_id"]:
    raise ValueError(
        "ERREUR : l'acquisition sélectionnée ne correspond "
        "pas aux images découpées."
    )

acquisition_date = selected_product["date"]

print("\n== CALCUL NDVI SENTINEL-2 ==")

print("Acquisition :", acquisition_id)
print("Date :", acquisition_date)
print("Couverture nuageuse :", selected_product.get("cloud_cover"), "%")

# 4. VERIFICATION DES METADONNEES


if processing_metadata["city"] != "Toulouse":
    raise ValueError("Ville incorrecte dans les métadonnées.")

if processing_metadata["crs"] != "EPSG:32631":
    raise ValueError("Projection inattendue.")

if processing_metadata["resolution_m"] != 10:
    raise ValueError("Résolution inattendue.")

expected_width = processing_metadata["width"]
expected_height = processing_metadata["height"]

print("\nMétadonnées du découpage : OK")

# 5. LECTURE DES IMAGES


with rasterio.open(RED_FILE) as src:

    red = src.read(1).astype(np.float32)

    profile = src.profile.copy()
    red_transform = src.transform
    red_crs = src.crs

    red_shape = src.shape

with rasterio.open(NIR_FILE) as src:

    nir = src.read(1).astype(np.float32)

    if src.shape != red_shape:
        raise ValueError("Dimensions B04 et B08 différentes.")

    if src.transform != red_transform:
        raise ValueError("Transformations B04 et B08 différentes.")

    if src.crs != red_crs:
        raise ValueError("Projections B04 et B08 différentes.")

with rasterio.open(SCL_FILE) as src:

    scl = src.read(1)

    if src.shape != red_shape:
        raise ValueError("Dimensions SCL et B04 différentes.")

    if src.transform != red_transform:
        raise ValueError("Transformations SCL et B04 différentes.")

    if src.crs != red_crs:
        raise ValueError("Projections SCL et B04 différentes.")


# Vérification avec les métadonnées du découpage

if red_shape != (expected_height, expected_width):
    raise ValueError(
        "Dimensions des rasters différentes des métadonnées."
    )

if red_crs.to_string() != processing_metadata["crs"]:
    raise ValueError("Projection différente des métadonnées.")

print("\n==VERIFICATION DES IMAGES ==")

print("Dimensions :", red.shape)
print("Projection :", red_crs)
print("Résolution :", profile["transform"].a, "m")

print("B04 : OK")
print("B08 : OK")
print("SCL : OK")

# 6. CREATION DU MASQUE SCL


valid_mask = np.isin(scl, VALID_CLASSES)

denominator = nir + red

valid_mask &= np.isfinite(red)
valid_mask &= np.isfinite(nir)
valid_mask &= np.isfinite(denominator)
valid_mask &= denominator != 0

total_pixels = int(red.size)

valid_pixels = int(np.count_nonzero(valid_mask))

invalid_pixels = total_pixels - valid_pixels

if valid_pixels == 0:
    raise ValueError("Aucun pixel valide.")

print("\n===MASQUE SCL ===")

print("Classes conservées :", VALID_CLASSES)
print("Pixels totaux :", total_pixels)
print("Pixels valides :", valid_pixels)
print("Pixels exclus :", invalid_pixels)
# 7. CALCUL DU NDVI

ndvi = np.full(
    red.shape,
    NODATA_VALUE,
    dtype=np.float32
)

ndvi[valid_mask] = (
    nir[valid_mask] - red[valid_mask]
) / denominator[valid_mask]

valid_values = ndvi[valid_mask]

ndvi_mean = float(valid_values.mean())
ndvi_min = float(valid_values.min())
ndvi_max = float(valid_values.max())
ndvi_std = float(valid_values.std())

print("\n===STATISTIQUES NDVI ===")

print("NDVI minimum :", ndvi_min)
print("NDVI maximum :", ndvi_max)
print("NDVI moyen :", ndvi_mean)
print("NDVI écart-type :", ndvi_std)

# 8. SAUVEGARDE DU RASTER NDVI

profile.update(
    driver="GTiff",
    dtype="float32",
    count=1,
    nodata=NODATA_VALUE,
    compress="deflate"
)

with rasterio.open(NDVI_FILE, "w", **profile) as dst:
    dst.write(ndvi, 1)

print("\nRaster NDVI créé :", NDVI_FILE.name)

# 9. VISUALISATION

ndvi_display = np.where(
    valid_mask,
    ndvi,
    np.nan
)

plt.figure(figsize=(10, 8))

image = plt.imshow(
    ndvi_display,
    cmap="RdYlGn",
    vmin=-1,
    vmax=1
)

plt.colorbar(image, label="NDVI")

plt.title(
    f"NDVI Sentinel-2 - Toulouse\n{acquisition_date}"
)

plt.axis("off")

plt.tight_layout()

plt.savefig(
    PNG_FILE,
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Carte NDVI créée :", PNG_FILE.name)

# 10. STATISTIQUES PAR CLASSE SCL

class_names = {
    4: "vegetation",
    5: "bare_soil",
    6: "water"
}

class_statistics = {}

for class_id, class_name in class_names.items():

    class_mask = (scl == class_id) & valid_mask

    values = ndvi[class_mask]

    class_statistics[class_name] = {
        "pixels": int(values.size),
        "ndvi_mean": float(values.mean()) if values.size else None,
        "ndvi_min": float(values.min()) if values.size else None,
        "ndvi_max": float(values.max()) if values.size else None
    }

# 11. STATISTIQUES GENERALES

statistics = {

    "city": "Toulouse",

    "acquisition_id": acquisition_id,

    "acquisition_date": acquisition_date,

    "cloud_cover": selected_product.get("cloud_cover"),

    "crs": red_crs.to_string(),

    "resolution_m": 10,

    "width": int(red.shape[1]),

    "height": int(red.shape[0]),

    "valid_scl_classes": VALID_CLASSES,

    "total_pixels": total_pixels,

    "valid_pixels": valid_pixels,

    "invalid_pixels": invalid_pixels,

    "valid_percentage": valid_pixels / total_pixels * 100,

    "ndvi_mean": ndvi_mean,

    "ndvi_min": ndvi_min,

    "ndvi_max": ndvi_max,

    "ndvi_std": ndvi_std,

    "classes": class_statistics
}


# 12. ENREGISTREMENT JSON


with open(STATS_FILE, "w", encoding="utf-8") as file:

    json.dump(
        statistics,
        file,
        indent=4,
        ensure_ascii=False
    )

print("\nStatistiques enregistrées :", STATS_FILE.name)

# 13. BILAN FINAL


print("\n===STATISTIQUES PAR CLASSE ===")

for class_name, values in class_statistics.items():

    print(f"\n{class_name} :")

    print("Pixels :", values["pixels"])

    print("NDVI moyen :", values["ndvi_mean"])


print("\n=== TRAITEMENT TERMINE AVEC SUCCES ===")

print("Acquisition :", acquisition_id)

print("NDVI moyen :", ndvi_mean)

print("Carte :", PNG_FILE)

print("Statistiques :", STATS_FILE)
