import pandas as pd
from pathlib import Path
# 1. CONFIGURATION

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

# Variables numériques horaires
HOURLY_NUMERIC_COLUMNS = [
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
    "visibility",
    "latitude",
    "longitude"
]

# Variables numériques quotidiennes
DAILY_NUMERIC_COLUMNS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "uv_index_max",
    "precipitation_sum",
    "rain_sum",
    "showers_sum",
    "snowfall_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "shortwave_radiation_sum",
    "latitude",
    "longitude"
]

# Limites horaires
HOURLY_RULES = {
    "temperature_2m": (-90, 65),
    "relative_humidity_2m": (0, 100),
    "precipitation": (0, None),
    "rain": (0, None),
    "showers": (0, None),
    "snowfall": (0, None),
    "cloud_cover": (0, 100),
    "wind_speed_10m": (0, None),
    "wind_gusts_10m": (0, None),
    "wind_direction_10m": (0, 360),
    "pressure_msl": (800, 1100),
    "surface_pressure": (800, 1100),
    "visibility": (0, None)
}

# Limites quotidiennes
DAILY_RULES = {
    "temperature_2m_max": (-90, 65),
    "temperature_2m_min": (-90, 65),
    "apparent_temperature_max": (-100, 70),
    "apparent_temperature_min": (-100, 70),
    "precipitation_sum": (0, None),
    "rain_sum": (0, None),
    "showers_sum": (0, None),
    "snowfall_sum": (0, None),
    "precipitation_probability_max": (0, 100),
    "wind_speed_10m_max": (0, None),
    "wind_gusts_10m_max": (0, None),
    "wind_direction_10m_dominant": (0, 360),
    "uv_index_max": (0, None),
    "shortwave_radiation_sum": (0, None)
}

# 2. FONCTION DE NETTOYAGE


def clean_weather_file(
    input_name,
    output_name,
    numeric_columns,
    rules
):

    input_file = DATA_DIR / input_name
    output_file = DATA_DIR / output_name

    print("\n" + "=" * 50)
    print("NETTOYAGE :", input_name)
    print("=" * 50)

    # Vérifier l'existence du fichier
    if not input_file.exists():
        print("Fichier introuvable :", input_file)
        return

    # Charger les données
    df = pd.read_csv(input_file)

    print("Dimensions initiales :", df.shape)
    # CONVERSION DES DATES


    df["time"] = pd.to_datetime(
        df["time"],
        errors="coerce"
    )

    if "retrieved_at_utc" in df.columns:
        df["retrieved_at_utc"] = pd.to_datetime(
            df["retrieved_at_utc"],
            errors="coerce",
            utc=True
        )
    # CONVERSION NUMERIQUE

    for column in numeric_columns:

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )


    # SUPPRESSION DES DATES INVALIDES


    before = len(df)

    df = df.dropna(subset=["time"])

    print(
        "Dates invalides supprimées :",
        before - len(df)
    )

    # SUPPRESSION DES DOUBLONS
 

    before = len(df)

    df = df.drop_duplicates(subset=["time"])

    print(
        "Doublons supprimés :",
        before - len(df)
    )

    # CORRECTION DES VALEURS HORS LIMITES


    for column, limits in rules.items():

        if column not in df.columns:
            continue

        minimum, maximum = limits

        invalid = pd.Series(
            False,
            index=df.index
        )

        if minimum is not None:
            invalid |= df[column] < minimum

        if maximum is not None:
            invalid |= df[column] > maximum

        invalid_count = invalid.sum()

        if invalid_count > 0:
            print(
                f"{column} : {invalid_count} valeur(s) "
                "remplacée(s) par NaN"
            )

            df.loc[invalid, column] = float("nan")

    # TRI CHRONOLOGIQUE


    df = df.sort_values("time")


    # ENREGISTREMENT

    df.to_csv(output_file, index=False)

    print("\nDimensions finales :", df.shape)
    print("Valeurs manquantes restantes :", df.isnull().sum().sum())
    print("Fichier nettoyé :", output_file)
    print("Nettoyage terminé !")

# 3. NETTOYAGE DES DEUX FICHIERS


# Données horaires
clean_weather_file(
    "weather_toulouse.csv",
    "weather_toulouse_clean.csv",
    HOURLY_NUMERIC_COLUMNS,
    HOURLY_RULES
)

# Données quotidiennes
clean_weather_file(
    "weather_toulouse_daily.csv",
    "weather_toulouse_daily_clean.csv",
    DAILY_NUMERIC_COLUMNS,
    DAILY_RULES
)

print("\n========== NETTOYAGE GLOBAL TERMINE ==========")
