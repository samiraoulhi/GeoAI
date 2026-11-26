import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).resolve().parents[2]

input_file = BASE_DIR / "data/satellite/raw/toulouse_sentinel2_bands_scl.tif"
output_tif = BASE_DIR / "data/satellite/processed/toulouse_ndvi_masked.tif"
output_png = BASE_DIR / "data/satellite/processed/toulouse_ndvi_masked.png"

# Lecture
with rasterio.open(input_file) as src:
    red = src.read(1).astype("float32")
    nir = src.read(4).astype("float32")
    scl = src.read(5)
    profile = src.profile.copy()

# Classes SCL autorisées
valid_classes = [2, 4, 5, 6]

# Masque des pixels valides
valid_mask = np.isin(scl, valid_classes)

# Calcul NDVI
denominator = nir + red

valid_mask &= np.isfinite(red) & np.isfinite(nir)
valid_mask &= denominator > 1e-6

ndvi = np.full(red.shape, -9999, dtype="float32")

ndvi[valid_mask] = (
    (nir[valid_mask] - red[valid_mask])
    / denominator[valid_mask]
)

# Statistiques
print("\n========== NDVI AVEC MASQUE SCL ==========")
print("Pixels valides :", np.sum(valid_mask))
print("Pixels masqués :", np.sum(~valid_mask))
print("Pourcentage valide :", round(100 * np.mean(valid_mask), 2), "%")

if np.any(valid_mask):
    print("NDVI minimum :", np.min(ndvi[valid_mask]))
    print("NDVI maximum :", np.max(ndvi[valid_mask]))
    print("NDVI moyen :", np.mean(ndvi[valid_mask]))

# Sauvegarde GeoTIFF
profile.update(
    count=1,
    dtype="float32",
    nodata=-9999
)

with rasterio.open(output_tif, "w", **profile) as dst:
    dst.write(ndvi, 1)

# Visualisation
display_ndvi = np.ma.masked_where(ndvi == -9999, ndvi)

plt.figure(figsize=(9, 7))
plt.imshow(display_ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
plt.colorbar(label="NDVI")
plt.title("NDVI de Toulouse - Masquage SCL")
plt.axis("off")
plt.tight_layout()
plt.savefig(output_png, dpi=150)
plt.show()

print("\nCarte sauvegardée :", output_tif)
print("Image sauvegardée :", output_png)
print("\n========== TERMINÉ ==========")
