import os
import json
import re

import psycopg2

from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv


# =====================================
# 1. CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

JSON_FILE = (
    BASE_DIR
    / "data"
    / "satellite"
    / "processed"
    / "toulouse"
    / "toulouse_ndvi_native_statistics.json"
)


# =====================================
# 2. LECTURE DES STATISTIQUES
# =====================================

with open(JSON_FILE, "r", encoding="utf-8") as file:
    stats = json.load(file)

print("\n========== STATISTIQUES NDVI NATIVES ==========")

print("Ville :", stats["city"])
print("Acquisition :", stats["acquisition_id"])
print("NDVI moyen :", stats["ndvi_mean"])


# =====================================
# 3. EXTRACTION DES INFORMATIONS
# =====================================

acquisition_id = stats["acquisition_id"]

# Extraction de la date depuis l'identifiant Sentinel-2
match = re.search(r"(\d{8}T\d{6})", acquisition_id)

if not match:
    raise ValueError("Impossible d'extraire la date de l'acquisition.")

acquisition_date = datetime.strptime(
    match.group(1),
    "%Y%m%dT%H%M%S"
).replace(tzinfo=timezone.utc)

retrieved_at = datetime.now(timezone.utc)

# Statistiques par classe SCL
classes = stats["classes"]

vegetation_pixels = classes["vegetation"]["pixels"]
bare_soil_pixels = classes["bare_soil"]["pixels"]
water_pixels = classes["water"]["pixels"]


# =====================================
# 4. CONNEXION POSTGRESQL
# =====================================

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()


try:

    # =====================================
    # 5. IDENTIFICATION DE LA VILLE
    # =====================================

    cursor.execute(
        """
        SELECT id
        FROM cities
        WHERE name = %s AND country = %s
        """,
        ("Toulouse", "France")
    )

    result = cursor.fetchone()

    if result is None:
        raise ValueError("Toulouse n'existe pas dans la table cities.")

    city_id = result[0]


    # =====================================
    # 6. INSERTION OU MISE A JOUR
    # =====================================

    cursor.execute(
        """
        INSERT INTO satellite_ndvi_statistics (
            city_id,
            retrieved_at,
            acquisition_id,
            acquisition_date,
            ndvi_mean,
            ndvi_min,
            ndvi_max,
            ndvi_std,
            valid_pixels,
            total_pixels,
            valid_percentage,
            vegetation_pixels_scl,
            bare_soil_pixels_scl,
            water_pixels_scl
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )

        ON CONFLICT (city_id, acquisition_id)

        DO UPDATE SET

            retrieved_at = EXCLUDED.retrieved_at,
            acquisition_date = EXCLUDED.acquisition_date,
            ndvi_mean = EXCLUDED.ndvi_mean,
            ndvi_min = EXCLUDED.ndvi_min,
            ndvi_max = EXCLUDED.ndvi_max,
            ndvi_std = EXCLUDED.ndvi_std,
            valid_pixels = EXCLUDED.valid_pixels,
            total_pixels = EXCLUDED.total_pixels,
            valid_percentage = EXCLUDED.valid_percentage,
            vegetation_pixels_scl = EXCLUDED.vegetation_pixels_scl,
            bare_soil_pixels_scl = EXCLUDED.bare_soil_pixels_scl,
            water_pixels_scl = EXCLUDED.water_pixels_scl

        RETURNING id;
        """,
        (
            city_id,
            retrieved_at,
            acquisition_id,
            acquisition_date,
            stats["ndvi_mean"],
            stats["ndvi_min"],
            stats["ndvi_max"],
            stats["ndvi_std"],
            stats["valid_pixels"],
            stats["total_pixels"],
            stats["valid_percentage"],
            vegetation_pixels,
            bare_soil_pixels,
            water_pixels
        )
    )

    result = cursor.fetchone()

    # =====================================
    # 7. VALIDATION
    # =====================================

    conn.commit()

    print("\n========== IMPORTATION NDVI ==========")

    print("Ville : Toulouse")
    print("City ID :", city_id)
    print("Acquisition ID :", acquisition_id)
    print("Identifiant de la ligne :", result[0])

    print("\nNDVI moyen :", stats["ndvi_mean"])
    print("NDVI minimum :", stats["ndvi_min"])
    print("NDVI maximum :", stats["ndvi_max"])

    print("\nPixels valides :", stats["valid_pixels"])
    print("Pixels totaux :", stats["total_pixels"])

    print("\nMise à jour ou insertion réussie !")


except Exception:

    conn.rollback()
    raise


finally:

    cursor.close()
    conn.close()