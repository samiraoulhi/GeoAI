import os
import psycopg2
import matplotlib.pyplot as plt
import pandas as pd

from dotenv import load_dotenv
from pathlib import Path

# Charger la configuration
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# Connexion PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

# Récupérer les données
query = """
SELECT observation_time, temperature
FROM weather_data
ORDER BY observation_time;
"""

df = pd.read_sql_query(query, conn)

conn.close()

# Créer le graphique
df["observation_time"] = pd.to_datetime(df["observation_time"])

plt.figure(figsize=(12, 5))
plt.plot(
    df["observation_time"],
    df["temperature"],
    marker="o",
    label="Température"
)

plt.title("Évolution de la température à Toulouse")
plt.xlabel("Date et heure")
plt.ylabel("Température (°C)")
plt.grid(True)
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

# Sauvegarder le graphique
output_file = BASE_DIR / "data" / "temperature_toulouse.png"
plt.savefig(output_file, dpi=150)

plt.show()

print("Graphique enregistré :", output_file)