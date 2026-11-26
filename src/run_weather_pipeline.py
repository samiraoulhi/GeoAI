import subprocess
import sys
from pathlib import Path

# Chemin principal du projet
BASE_DIR = Path(__file__).resolve().parents[1]

# Étapes de la collecte météo
scripts = [
    "src/weather_api.py",
    "src/processing/validate_weather.py",
    "src/processing/clean_weather.py",
    "src/database/load_weather.py"
]

print("\n========== GEOAI WEATHER PIPELINE ==========\n")

for script in scripts:
    script_path = BASE_DIR / script

    print(f"\n>>> Exécution : {script}")

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
        check=True
    )

    print(f">>> Terminé : {script}")

print("\n========== PIPELINE TERMINÉ AVEC SUCCÈS ==========")