import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Charger le fichier .env à la racine du projet
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)

print("\n========== TEST AUTHENTIFICATION COPERNICUS ==========\n")

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERREUR : identifiants absents du fichier .env")
    raise SystemExit(1)

try:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        },
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    access_token = data.get("access_token")

    if access_token:
        print("Authentification réussie !")
        print("Access Token obtenu.")
        print("Durée de validité :", data.get("expires_in"), "secondes")
    else:
        print("ERREUR : aucun token reçu.")

except requests.exceptions.HTTPError:
    print("Erreur HTTP :", response.status_code)
    print("Vérifie tes identifiants OAuth.")

except requests.exceptions.RequestException as error:
    print("Erreur de connexion :", error)

print("\n========== FIN DU TEST ==========")