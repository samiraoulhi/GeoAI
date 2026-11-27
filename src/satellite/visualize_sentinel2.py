import rasterio
import numpy as np
import matplotlib.pyplot as plt

IMAGE_PATH = "data/satellite/raw/toulouse_sentinel2_rgb.tif"

# Lecture de l'image
with rasterio.open(IMAGE_PATH) as src:
    red = src.read(1)
    green = src.read(2)
    blue = src.read(3)

print("=== INFORMATIONS IMAGE ===")

for name, band in [
    ("Rouge", red),
    ("Vert", green),
    ("Bleu", blue)
]:
    print(
        f"{name} : min={np.nanmin(band):.4f}, "
        f"max={np.nanmax(band):.4f}"
    )

# Composition RGB
rgb = np.dstack((red, green, blue))

# Amélioration du contraste pour l'affichage
rgb_display = np.zeros_like(rgb)

for i in range(3):
    p2, p98 = np.nanpercentile(rgb[:, :, i], [2, 98])

    if p98 > p2:
        rgb_display[:, :, i] = np.clip(
            (rgb[:, :, i] - p2) / (p98 - p2),
            0, 1
        )

# Affichage
plt.figure(figsize=(10, 10))
plt.imshow(rgb_display)
plt.title("Sentinel-2 - Toulouse - RGB")
plt.axis("off")
plt.tight_layout()
plt.show()
