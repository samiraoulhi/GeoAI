# 🌍 GeoAI – Intelligent Earth Observation & Climate Analytics

### Satellite Imagery, Remote Sensing and Geospatial Intelligence

GeoAI is a geospatial intelligence project designed to explore and analyze environmental data by combining **satellite imagery, remote sensing, meteorological data and geospatial processing**.

The project focuses on extracting meaningful environmental information from Sentinel-2 satellite imagery and weather data, with an initial application on Toulouse, France.

The long-term objective is to develop an intelligent platform for Earth observation and climate analytics.

---

## 🎯 Project Objectives

- Acquire and process Sentinel-2 satellite imagery.
- Analyze vegetation using spectral indices such as NDVI.
- Integrate meteorological data from external APIs.
- Perform geospatial processing and raster analysis.
- Store and organize environmental data in PostgreSQL.
- Visualize satellite-derived indicators and weather information.
- Explore future GeoAI and machine learning applications.

## 🛰️ Satellite Imagery & Remote Sensing

The project uses **Sentinel-2 Level-2A imagery** from the Copernicus Data Space Ecosystem (CDSE).

The processing workflow includes:

1. Search for available Sentinel-2 products.
2. Select satellite imagery according to acquisition date and cloud coverage.
3. Download the required spectral bands.
4. Validate and preprocess satellite data.
5. Crop imagery to the study area.
6. Calculate vegetation indices.
7. Generate visualizations and statistical indicators.
8. Store processed results.

### Spectral Bands

The current workflow uses:

| Band | Description | Spatial Resolution |
|---|---|---|
| B02 | Blue | 10 m |
| B03 | Green | 10 m |
| B04 | Red | 10 m |
| B08 | Near Infrared (NIR) | 10 m |
| SCL | Scene Classification Layer | 20 m native resolution |

## 🌱 Vegetation Analysis – NDVI

The project calculates the Normalized Difference Vegetation Index (NDVI).

The NDVI is defined as:

\[
NDVI = \frac{NIR - Red}{NIR + Red}
\]

For Sentinel-2:

\[
NDVI = \frac{B08 - B04}{B08 + B04}
\]

The index provides information about vegetation density and photosynthetic activity.

The workflow also explores cloud and invalid-pixel masking using the Scene Classification Layer (SCL).

## 🌦️ Meteorological Data

Weather information is collected using the **Open-Meteo API**.

The project includes:

- Historical and forecast weather data.
- Hourly meteorological variables.
- Daily weather indicators.
- Data cleaning and validation.
- Weather visualization.

The initial study area is Toulouse, France.

## 🗄️ Geospatial Data Management

PostgreSQL is used to organize and store environmental information.

The database supports the integration of:

- Meteorological observations and forecasts.
- Satellite-derived indicators.
- NDVI statistics.
- Geospatial analysis results.

## 🏗️ Project Architecture

```text
GeoAI/
│
├── dashboard/
│   └── Interactive visualization
│
├── src/
│   ├── database/
│   │   ├── load_satellite_ndvi.py
│   │   └── load_weather.py
│   │
│   ├── processing/
│   │   ├── clean_weather.py
│   │   ├── plot_weather.py
│   │   └── validate_weather.py
│   │
│   ├── satellite/
│   │   ├── search_sentinel2.py
│   │   ├── download_sentinel2.py
│   │   ├── calculate_ndvi.py
│   │   ├── calculate_ndvi_masked.py
│   │   └── visualize_sentinel2.py
│   │
│   ├── run_satellite_pipeline.py
│   ├── run_weather_pipeline.py
│   └── weather_api.py
│
├── data/
│   ├── satellite/
│   ├── results/
│   └── weather/
│
├── notebooks/
├── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py
└── README.md
```

## 🛠️ Technologies & Tools

| Category | Technologies |
|---|---|
| Programming | Python |
| Geospatial Processing | Rasterio, GDAL |
| Satellite Data | Sentinel-2, Copernicus Data Space |
| Data Processing | NumPy, Pandas |
| Meteorological Data | Open-Meteo API |
| Database | PostgreSQL |
| Visualization | Matplotlib, Plotly |
| Development | Linux, Git, GitHub |

## 🔄 Processing Workflow

```text
Copernicus Data Space
          |
          v
   Sentinel-2 Imagery
          |
          v
  Download & Validation
          |
          v
  Geospatial Processing
          |
          v
    NDVI Calculation
          |
          v
   Vegetation Analysis
          |
          v
    PostgreSQL
          |
          v
   Visualization
```

In parallel:

```text
Open-Meteo API
       |
       v
Weather Data Collection
       |
       v
Data Cleaning & Validation
       |
       v
PostgreSQL
       |
       v
Weather Visualization
```

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/samiraoulhi/GeoAI.git
cd GeoAI
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

Update `.env` with your own Copernicus and PostgreSQL credentials.

**Never commit your `.env` file or expose your credentials.**

## 📊 Current Project Status

**Implemented:**
- Sentinel-2 product search and selection.
- Satellite data acquisition.
- Spectral band processing.
- NDVI calculation.
- SCL-based masking.
- NDVI visualization and statistical extraction.
- Open-Meteo weather data collection.
- Weather data cleaning and processing.
- PostgreSQL data integration.

**Future Development:**
- Extension to multiple geographical areas.
- Advanced environmental indicators.
- Machine learning for satellite image analysis.
- Integration of geospatial AI models.
- Intelligent agents for environmental data analysis.
- Advanced climate and vegetation monitoring.

## 🗺️ Study Area

The initial implementation focuses on Toulouse, France.

The project is designed to evolve towards multi-city and larger-scale geographical analysis.

## 👩‍💻 Author

**Samira OULHI**

M2 – Signal, Image and Machine Learning  
Université Toulouse III – Paul Sabatier

Engineering background in Embedded Systems.

GitHub: [@samiraoulhi](https://github.com/samiraoulhi)

Portfolio: [Samira OULHI – Portfolio](https://samiraoulhi.github.io/Portfolio-Samira-OULHI/)

---

*GeoAI – Transforming satellite and environmental data into meaningful geospatial intelligence.*