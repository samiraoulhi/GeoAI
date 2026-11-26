import os
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)

USERNAME = os.getenv("CDSE_USERNAME")
PASSWORD = os.getenv("CDSE_PASSWORD")

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

response = requests.post(
    TOKEN_URL,
    data={
        "client_id": "cdse-public",
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    },
    timeout=60
)

print("========== AUTHENTIFICATION CDSE ==========")
print("Code HTTP :", response.status_code)

if response.status_code == 200:
    print("SUCCÈS : authentification API réussie !")
else:
    print("ÉCHEC :", response.text)