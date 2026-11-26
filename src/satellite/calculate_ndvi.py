import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# 1. CHEMINS
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data/satellite/raw/toulouse_sentinel2_bands.tif"

OUTPUT_DIR = BASE_DIR / "data/satellite/processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NDVI_TIF = OUTPUT_DIR / "toulouse_ndvi.tif"
NDVI_PNG = OUTPUT_DIR / "toulouse_ndvi.png"

# ==========================================
# 2. LECTURE DES BANDES
# ==========================================

print("\n========== LECTURE DES BANDES ==========")

with rasterio.open(INPUT_FILE) as src:

    red = src.read(1)    # B04 : rouge
    green = src.read(2)  # B03 : vert
    blue = src.read(3)   # B02 : bleu
    nir = src.read(4)    # B08 : proche infrarouge

    profile = src.profile.copy()

print("Image chargée :", red.shape)
print("Bande rouge : B04")
print("Bande infrarouge : B08")

# ==========================================
# 3. CALCUL DU NDVI
# ==========================================

print("\n========== CALCUL DU NDVI ==========")

denominator = nir + red

valid = (
    np.isfinite(nir)
    & np.isfinite(red)
    & (np.abs(denominator) > 1e-6)
)

ndvi = np.full(red.shape, -9999, dtype=np.float32)

np.divide(
    nir - red,
    denominator,
    out=ndvi,
    where=valid
)

print("NDVI minimum :", np.min(ndvi[valid]))
print("NDVI maximum :", np.max(ndvi[valid]))
print("NDVI moyen :", np.mean(ndvi[valid]))

# ==========================================
# 4. SAUVEGARDE GEOTIFF
# ==========================================

profile.update(
    count=1,
    dtype="float32",
    nodata=-9999
)

with rasterio.open(NDVI_TIF, "w", **profile) as dst:
    dst.write(ndvi, 1)

print("\nCarte NDVI sauvegardée :", NDVI_TIF)

# ==========================================
# 5. VISUALISATION
# ==========================================

ndvi_display = np.ma.masked_equal(ndvi, -9999)

plt.figure(figsize=(10, 8))

image = plt.imshow(
    ndvi_display,
    cmap="RdYlGn",
    vmin=-1,
    vmax=1
)

plt.colorbar(image, label="NDVI")
plt.title("Indice de végétation NDVI - Toulouse")
plt.axis("off")
plt.tight_layout()

plt.savefig(NDVI_PNG, dpi=200)
plt.show()

print("\nImage NDVI sauvegardée :", NDVI_PNG)
print("\n========== TRAITEMENT TERMINÉ ==========")
