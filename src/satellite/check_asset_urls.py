import requests

STAC_URL = "https://stac.dataspace.copernicus.eu/v1"

IMAGE_ID = (
    "S2B_MSIL2A_20261031T105159_N0513_R051_"
    "T31TCJ_20261031T132327"
)

url = (
    f"{STAC_URL}/collections/"
    f"sentinel-2-l2a/items/{IMAGE_ID}"
)

response = requests.get(url, timeout=60)
response.raise_for_status()

item = response.json()

selected_assets = [
    "B02_10m",
    "B03_10m",
    "B04_10m",
    "B08_10m",
    "TCI_10m",
    "thumbnail"
]

print("\n==LIENS DES ASSETS ==")

for name in selected_assets:

    asset = item.get("assets", {}).get(name)

    if asset:
        print(f"\n{name}")
        print("URL :", asset.get("href"))
        print("Type :", asset.get("type"))
    else:
        print(f"\n{name} : indisponible")
