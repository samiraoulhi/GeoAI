import requests

STAC_URL = "https://stac.dataspace.copernicus.eu/v1"

# Deux images avec peu de nuages
image_ids = [
    "S2B_MSIL2A_20261031T105159_N0513_R051_T31TCJ_20261031T132327",
    "S2A_MSIL2A_20261028T105051_N0513_R051_T31TCJ_20261028T171310"
]

for image_id in image_ids:

    print("\n" + "=" * 60)
    print("IMAGE :", image_id)

    url = (
        f"{STAC_URL}/collections/"
        f"sentinel-2-l2a/items/{image_id}"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    item = response.json()

    print("\nDate :", item["properties"].get("datetime"))
    print("Couverture nuageuse :",
          item["properties"].get("eo:cloud_cover"), "%")

    print("\nFICHIERS DISPONIBLES :")

    for name, asset in item.get("assets", {}).items():

        print("\nNom :", name)
        print("Type :", asset.get("type"))
        print("Rôles :", asset.get("roles"))

print("\nInspection terminée.")