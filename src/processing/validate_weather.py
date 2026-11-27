import pandas as pd
from pathlib import Path

# 1. CONFIGURATION

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


# Colonnes obligatoires pour chaque fichier
HOURLY_COLUMNS = [
    "time",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "city",
    "retrieved_at_utc"
]

DAILY_COLUMNS = [
    "time",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "city",
    "retrieved_at_utc"
]


# Limites acceptables pour les données horaires
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


# Limites acceptables pour les données quotidiennes
DAILY_RULES = {
    "temperature_2m_max": (-90, 65),
    "temperature_2m_min": (-90, 65),
    "apparent_temperature_max": (-100, 70),
    "apparent_temperature_min": (-100, 70),
    "relative_humidity_2m_mean": (0, 100),
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

# 2. FONCTION DE VALIDATION


def validate_file(filename, required_columns, rules):

    file_path = DATA_DIR / filename

    print("\n")
    print("=" * 55)
    print(f"CONTROLE DU FICHIER : {filename}")
    print("=" * 55)

    # Vérifier que le fichier existe
    if not file_path.exists():
        print("ERREUR : fichier introuvable !")
        return

    # Charger les données
    df = pd.read_csv(file_path)
    # DIMENSIONS

    print("\n1. DIMENSIONS")

    print("Nombre de lignes :", df.shape[0])
    print("Nombre de colonnes :", df.shape[1])
    # COLONNES OBLIGATOIRES

    print("\n2. VERIFICATION DES COLONNES")

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        print("Colonnes manquantes :", missing_columns)
    else:
        print("Toutes les colonnes indispensables sont présentes.")
    # VALEURS MANQUANTES

    print("\n3. VALEURS MANQUANTES")

    missing_values = df.isnull().sum()

    print(missing_values)

    print(
        "Total des valeurs manquantes :",
        missing_values.sum()
    )

    # DOUBLONS

    print("\n4. VERIFICATION DES DOUBLONS")

    print(
        "Lignes totalement identiques :",
        df.duplicated().sum()
    )

    if "time" in df.columns:

        print(
            "Dates dupliquées :",
            df["time"].duplicated().sum()
        )

    # VERIFICATION DES DATES

    print("\n5. VERIFICATION DES DATES")

    if "time" in df.columns:

        dates = pd.to_datetime(
            df["time"],
            errors="coerce"
        )

        invalid_dates = dates.isnull().sum()

        print("Dates invalides :", invalid_dates)

        if invalid_dates == 0:
            print("Première date :", dates.min())
            print("Dernière date :", dates.max())
            
    # VALEURS METEOROLOGIQUES


  

    for column, limits in rules.items():

        if column not in df.columns:
            continue

        minimum, maximum = limits

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        # Valeurs non numériques
        non_numeric = (
            df[column].notna() & values.isna()
        ).sum()

        # Valeurs en dehors des limites
        invalid = pd.Series(
            False,
            index=df.index
        )

        if minimum is not None:
            invalid |= values < minimum

        if maximum is not None:
            invalid |= values > maximum

        print(
            f"{column} : "
            f"{invalid.sum()} valeur(s) hors limites, "
            f"{non_numeric} valeur(s) non numérique(s)"
        )

    # COHERENCE ENTRE TEMPERATURES
  

    if (
        "temperature_2m_max" in df.columns
        and "temperature_2m_min" in df.columns
    ):

        maximum_temp = pd.to_numeric(
            df["temperature_2m_max"],
            errors="coerce"
        )

        minimum_temp = pd.to_numeric(
            df["temperature_2m_min"],
            errors="coerce"
        )

        inconsistent = (
            maximum_temp < minimum_temp
        ).sum()

        print(
            "\nTempérature maximale inférieure "
            "à la température minimale :",
            inconsistent
        )
    # STATISTIQUES
  

    print("\n7. STATISTIQUES DESCRIPTIVES")

    print(
        df.select_dtypes(include="number").describe()
    )

    # INFORMATIONS SUR LA COLLECTE
  

    print("\n8. INFORMATIONS SUR LA COLLECTE")

    if "city" in df.columns and not df.empty:
        print("Ville :", df["city"].iloc[0])

    if "retrieved_at_utc" in df.columns and not df.empty:
        print(
            "Date de récupération :",
            df["retrieved_at_utc"].iloc[0]
        )

    print("\nCONTROLE TERMINE POUR :", filename)


# 3. EXECUTION DES DEUX CONTROLES

print("\n= CONTROLE QUALITE METEO ==")

validate_file(
    "weather_toulouse.csv",
    HOURLY_COLUMNS,
    HOURLY_RULES
)

validate_file(
    "weather_toulouse_daily.csv",
    DAILY_COLUMNS,
    DAILY_RULES
)

print("\n===TOUS LES CONTROLES SONT TERMINES ===")
