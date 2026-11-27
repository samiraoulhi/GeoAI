import requests
import pandas as pd

from pathlib import Path
from datetime import datetime, timezone

# 1. CONFIGURATION DE LA VILLE


CITY = "Toulouse"
COUNTRY = "France"

LATITUDE = 43.6045
LONGITUDE = 1.4442

URL = "https://api.open-meteo.com/v1/forecast"

# Dossier principal du projet
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# 2. VARIABLES METEOROLOGIQUES HORAIRES


hourly_variables = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "showers",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "shortwave_radiation",
    "visibility"
]


# 3. VARIABLES METEOROLOGIQUES QUOTIDIENNES


daily_variables = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "sunrise",
    "sunset",
    "uv_index_max",
    "precipitation_sum",
    "rain_sum",
    "showers_sum",
    "snowfall_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "shortwave_radiation_sum"
]



# 4. PARAMETRES DE LA REQUETE


params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "hourly": hourly_variables,
    "daily": daily_variables,
    "timezone": "Europe/Paris",
    "forecast_days": 10
}

# 5. RECUPERATION DES DONNEES


print("Connexion à Open-Meteo...")

try:

    response = requests.get(
        URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    retrieved_at = datetime.now(timezone.utc).isoformat()

    print("Données récupérées avec succès !")

    # 6. TRAITEMENT DES DONNEES HORAIRES
   
    

    df_hourly = pd.DataFrame(data["hourly"])

    df_hourly["city"] = CITY
    df_hourly["country"] = COUNTRY
    df_hourly["latitude"] = LATITUDE
    df_hourly["longitude"] = LONGITUDE
    df_hourly["retrieved_at_utc"] = retrieved_at

    hourly_file = DATA_DIR / "weather_toulouse.csv"

    df_hourly.to_csv(hourly_file, index=False)




    
    # 7. TRAITEMENT DES DONNEES QUOTIDIENNES
  
    

    df_daily = pd.DataFrame(data["daily"])

    df_daily["city"] = CITY
    df_daily["country"] = COUNTRY
    df_daily["latitude"] = LATITUDE
    df_daily["longitude"] = LONGITUDE
    df_daily["retrieved_at_utc"] = retrieved_at

    daily_file = DATA_DIR / "weather_toulouse_daily.csv"

    df_daily.to_csv(daily_file, index=False)
    # 8. AFFICHAGE DES RESULTATS
    

    

    print("\nDonnées horaires :")
    print(df_hourly.head())

    print("\nDonnées quotidiennes :")
    print(df_daily.head())

    print("\nNombre de mesures horaires :", len(df_hourly))
    print("Nombre de mesures quotidiennes :", len(df_daily))

    print("\nFichiers enregistrés :")
    print(hourly_file)
    print(daily_file)

    print("\nCollecte terminée avec succès !")


except requests.exceptions.RequestException as error:

    print("Erreur lors de la récupération des données :", error)

except (KeyError, ValueError) as error:

    print("Erreur lors du traitement des données :", error)
