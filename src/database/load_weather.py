import os
import pandas as pd
import psycopg2

from pathlib import Path
from dotenv import load_dotenv


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")


# Fichiers nettoyés
HOURLY_FILE = DATA_DIR / "weather_toulouse_clean.csv"
DAILY_FILE = DATA_DIR / "weather_toulouse_daily_clean.csv"


# ==========================================
# 2. CONNEXION POSTGRESQL
# ==========================================

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()

print("Connexion à PostgreSQL réussie !")


try:

    # ======================================
    # 3. RECUPERATION DE L'IDENTIFIANT VILLE
    # ======================================

    cursor.execute("""
        SELECT id
        FROM cities
        WHERE name = %s AND country = %s;
    """, ("Toulouse", "France"))

    result = cursor.fetchone()

    if result is None:
        raise ValueError("Toulouse n'existe pas dans la table cities.")

    city_id = result[0]

    print("Ville identifiée : Toulouse")
    print("City ID :", city_id)


    # ======================================
    # 4. FONCTION DE CONVERSION
    # ======================================

    def convert_value(value, integer=False):

        if pd.isna(value):
            return None

        if integer:
            return int(value)

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        return value


    # ======================================
    # 5. IMPORTATION DES PREVISIONS HORAIRES
    # ======================================

    print("\nImportation des prévisions horaires...")

    df_hourly = pd.read_csv(HOURLY_FILE)

    hourly_columns = [
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

    df_hourly["time"] = pd.to_datetime(df_hourly["time"])

    df_hourly["retrieved_at_utc"] = pd.to_datetime(
        df_hourly["retrieved_at_utc"],
        utc=True
    )

    hourly_query = """
        INSERT INTO weather_hourly_forecasts (
            city_id,
            forecast_time,
            retrieved_at,
            temperature_2m,
            relative_humidity_2m,
            dew_point_2m,
            apparent_temperature,
            precipitation,
            rain,
            showers,
            snowfall,
            weather_code,
            cloud_cover,
            pressure_msl,
            surface_pressure,
            wind_speed_10m,
            wind_direction_10m,
            wind_gusts_10m,
            shortwave_radiation,
            visibility
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (
            city_id,
            forecast_time,
            retrieved_at
        ) DO NOTHING;
    """

    hourly_rows = []

    for _, row in df_hourly.iterrows():

        values = [
            convert_value(row[col])
            for col in hourly_columns
        ]

        # weather_code est un entier
        values[8] = convert_value(row["weather_code"], integer=True)

        hourly_rows.append((
            city_id,
            convert_value(row["time"]),
            convert_value(row["retrieved_at_utc"]),
            *values
        ))

    cursor.executemany(hourly_query, hourly_rows)

    print("Lignes horaires traitées :", len(hourly_rows))
    print("Lignes horaires insérées :", cursor.rowcount)


    # ======================================
    # 6. IMPORTATION DES PREVISIONS QUOTIDIENNES
    # ======================================

    print("\nImportation des prévisions quotidiennes...")

    df_daily = pd.read_csv(DAILY_FILE)

    daily_columns = [
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

    df_daily["time"] = pd.to_datetime(df_daily["time"])

    df_daily["retrieved_at_utc"] = pd.to_datetime(
        df_daily["retrieved_at_utc"],
        utc=True
    )

    df_daily["sunrise"] = pd.to_datetime(
        df_daily["sunrise"],
        errors="coerce"
    )

    df_daily["sunset"] = pd.to_datetime(
        df_daily["sunset"],
        errors="coerce"
    )

    daily_query = """
        INSERT INTO weather_daily_forecasts (
            city_id,
            forecast_date,
            retrieved_at,
            weather_code,
            temperature_2m_max,
            temperature_2m_min,
            apparent_temperature_max,
            apparent_temperature_min,
            sunrise,
            sunset,
            uv_index_max,
            precipitation_sum,
            rain_sum,
            showers_sum,
            snowfall_sum,
            precipitation_probability_max,
            wind_speed_10m_max,
            wind_gusts_10m_max,
            wind_direction_10m_dominant,
            shortwave_radiation_sum
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (
            city_id,
            forecast_date,
            retrieved_at
        ) DO NOTHING;
    """

    daily_rows = []

    for _, row in df_daily.iterrows():

        values = [
            convert_value(row[col])
            for col in daily_columns
        ]

        # weather_code est un entier
        values[0] = convert_value(row["weather_code"], integer=True)

        daily_rows.append((
            city_id,
            row["time"].date(),
            convert_value(row["retrieved_at_utc"]),
            *values
        ))

    cursor.executemany(daily_query, daily_rows)

    print("Lignes quotidiennes traitées :", len(daily_rows))
    print("Lignes quotidiennes insérées :", cursor.rowcount)


    # ======================================
    # 7. VALIDATION
    # ======================================

    conn.commit()

    print("\nImportation terminée avec succès !")


except Exception as error:

    conn.rollback()

    print("\nERREUR pendant l'importation :")
    print(error)

    raise

finally:

    cursor.close()
    conn.close()

    print("\nConnexion PostgreSQL fermée.")