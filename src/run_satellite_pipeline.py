import subprocess
import sys
import os
import time

from pathlib import Path
from datetime import datetime

# 1. CONFIGURATION

BASE_DIR = Path(__file__).resolve().parents[1]

SCRIPTS = [
    "src/satellite/search_sentinel2.py",
    "src/satellite/get_sentinel2_product.py",
    "src/satellite/download_sentinel2_assets.py",
    "src/satellite/validate_sentinel2_assets.py",
    "src/satellite/crop_sentinel2_toulouse.py",
    "src/satellite/calculate_ndvi_native.py",
    "src/database/load_satellite_ndvi.py"
]

env = os.environ.copy()

# Éviter les fenêtres graphiques
env["MPLBACKEND"] = "Agg"

# Afficher les sorties Python immédiatement
env["PYTHONUNBUFFERED"] = "1"


# 2. DEMARRAGE


pipeline_start = time.perf_counter()

print("\n" + "=" * 55, flush=True)
print("          GEOAI - SATELLITE PIPELINE", flush=True)
print("=" * 55, flush=True)

print(
    "Début :",
    datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
    flush=True
)

print("\nNombre d'étapes :", len(SCRIPTS), flush=True)



# 3. EXECUTION DES SCRIPTS


for index, script in enumerate(SCRIPTS, start=1):

    script_path = BASE_DIR / script

    print("\n" + "-" * 55, flush=True)
    print(f"ETAPE {index}/{len(SCRIPTS)} : {script}", flush=True)
    print("-" * 55, flush=True)

    # Vérifier que le script existe
    if not script_path.exists():

        print(
            f"ERREUR : fichier introuvable : {script_path}",
            flush=True
        )

        sys.exit(1)

    step_start = time.perf_counter()

    try:

        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=BASE_DIR,
            env=env,
            check=True
        )

        step_duration = time.perf_counter() - step_start

        print("\nSUCCES :", script, flush=True)

        print(
            f"Durée : {step_duration:.2f} secondes",
            flush=True
        )

    except subprocess.CalledProcessError as error:

        print("\n" + "=" * 55, flush=True)
        print("ECHEC DU PIPELINE", flush=True)
        print("Script :", script, flush=True)
        print("Code erreur :", error.returncode, flush=True)

        print(
            "Le pipeline est arrêté pour éviter "
            "de poursuivre avec des données incorrectes.",
            flush=True
        )

        sys.exit(error.returncode)

    except KeyboardInterrupt:

        print("\nPipeline interrompu par l'utilisateur.", flush=True)

        sys.exit(130)



# 4. BILAN FINAL


total_duration = time.perf_counter() - pipeline_start

print("\n" + "=" * 55, flush=True)
print("          PIPELINE TERMINE AVEC SUCCES", flush=True)
print("=" * 55, flush=True)

print(
    "Fin :",
    datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
    flush=True
)

print(
    f"Durée totale : {total_duration / 60:.2f} minutes",
    flush=True
)

print("\nToutes les étapes ont été exécutées.", flush=True)
print("Les statistiques NDVI sont enregistrées dans PostgreSQL.", flush=True)
