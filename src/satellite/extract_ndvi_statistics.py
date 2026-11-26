import rasterio
import numpy as np
import pandas as pd
import json

from pathlib import Path
from datetime import datetime

# =====================================
# 1. CHEMINS
# =====================================

BASE_DIR = Path(__file__).resolve().parents[2]

NDVI_FILE = BASE_DIR / "data/satellite/processed/toulouse_ndvi_masked.tif"
SCL_FILE = BASE_DIR / "data/satellite/raw/toulouse_sentinel2_bands_scl.tif"

SELECTED_FILE = BASE_DIR / "data/sentinel2_selected.json"

OUTPUT_FILE = BASE_DIR / "data/results/ndvi_statistics.csv"

# =====================================
# 2. INFORMATIONS SENTINEL-2
# =====================================

with open(SELECTED_FILE, "r", encoding="utf-8") as file:
    satellite_data = json.load(file)

acquisition_id = satellite_data["id"]
acquisition_date = satellite_data["date"]

# =====================================
# 3. LECTURE DES DONNEES
# =====================================

with rasterio.open(NDVI_FILE) as src:
    ndvi = src.read(1)
    nodata = src.nodata

with rasterio.open(SCL_FILE) as src:
    scl = src.read(5)

# =====================================
# 4. VALIDATION
# =====================================

valid_mask = np.isfinite(ndvi)

if nodata is not None:
    valid_mask &= ndvi != nodata

valid_mask &= (ndvi >= -1) & (ndvi <= 1)

valid_ndvi = ndvi[valid_mask]

if valid_ndvi.size == 0:
    raise ValueError("Aucun pixel NDVI valide.")

# =====================================
# 5. STATISTIQUES NDVI
# =====================================

stats = {
    "retrieved_at": datetime.now().astimezone().isoformat(),
    "city": "Toulouse",
    "acquisition_id": acquisition_id,
    "acquisition_date": acquisition_date,
    "ndvi_mean": float(np.mean(valid_ndvi)),
    "ndvi_min": float(np.min(valid_ndvi)),
    "ndvi_max": float(np.max(valid_ndvi)),
    "ndvi_std": float(np.std(valid_ndvi)),
    "valid_pixels": int(np.sum(valid_mask)),
    "total_pixels": int(ndvi.size),
    "valid_percentage": float(100 * np.mean(valid_mask)),
    "vegetation_pixels_scl": int(np.sum(scl == 4)),
    "bare_soil_pixels_scl": int(np.sum(scl == 5)),
    "water_pixels_scl": int(np.sum(scl == 6))
}

# =====================================
# 6. AFFICHAGE
# =====================================

print("\n========== STATISTIQUES NDVI ==========")

for key, value in stats.items():
    print(f"{key} : {value}")

# =====================================
# 7. SAUVEGARDE CSV
# =====================================

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame([stats])

if OUTPUT_FILE.exists():
    df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
else:
    df.to_csv(OUTPUT_FILE, index=False)

print("\nFichier sauvegardé :", OUTPUT_FILE)
print("\n========== TERMINÉ ==========")