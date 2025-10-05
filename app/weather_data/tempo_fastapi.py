from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
import os

app = FastAPI(title="TEMPO NO2 + Weather API")

# ============================================================
# 1️⃣ TEMPO NO₂ DATA (Canada)
# ============================================================
file_paths = [
    r"C:\Users\aqsar\OneDrive\Desktop\heckathone_data\TEMPO_data\TEMPO_NO2_L3_V04_20250925T215959Z_S013.nc",
    r"C:\Users\aqsar\OneDrive\Desktop\heckathone_data\TEMPO_data\TEMPO_NO2_L3_V04_20250925T225959Z_S014.nc",
    r"C:\Users\aqsar\OneDrive\Desktop\heckathone_data\TEMPO_data\TEMPO_NO2_L3_V04_20250925T234007Z_S015.nc"
]

datasets = [xr.open_dataset(fp) for fp in file_paths]
no2_list = [ds["weight"] for ds in datasets]
no2_all = xr.concat(no2_list, dim="granule").mean(dim="granule")
no2_canada = no2_all.sel(latitude=slice(41, 83), longitude=slice(-141, -52))
no2_valid = no2_canada.where(~no2_canada.isnull(), drop=True)

# ============================================================
# 2️⃣ WEATHER CSV DATA
# ============================================================
csv_file = r"C:\Users\admin\Desktop\weather_data\weather_data.csv"
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
    df["time"] = pd.to_datetime(df["time"])
else:
    df = None

# ============================================================
# 3️⃣ API ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {"message": "TEMPO NO2 + Weather API is running!"}

# ---------- TEMPO ENDPOINTS ----------
@app.get("/tempo/stats")
def get_tempo_stats():
    """Return basic statistics for Canada NO2"""
    stats = {
        "mean_NO2": float(no2_valid.mean().values),
        "max_NO2": float(no2_valid.max().values),
        "min_NO2": float(no2_valid.min().values)
    }
    return JSONResponse(content=stats)

@app.get("/tempo/map")
def get_tempo_map():
    """Generate and return NO2 map as PNG"""
    output_file = "tempo_no2_canada.png"
    
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    no2_valid.plot(ax=ax, cmap="viridis", cbar_kwargs={"label": "NO₂ (molecules/cm²)"})
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.set_title("TEMPO NO₂ over Canada (Average of 3 granules)")
    
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    
    return FileResponse(output_file, media_type="image/png", filename=output_file)

# ---------- WEATHER ENDPOINTS ----------
@app.get("/weather/temperature")
def get_temperature_graph():
    if df is None:
        return {"error": "weather_data.csv not found!"}
    output_file = "temperature_over_time.png"
    
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["temperature_C"], label="Temperature (°C)", color="red")
    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.title("Temperature Over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    
    return FileResponse(output_file, media_type="image/png", filename=output_file)

@app.get("/weather/humidity")
def get_humidity_graph():
    if df is None:
        return {"error": "weather_data.csv not found!"}
    output_file = "humidity_over_time.png"
    
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["humidity_%"], label="Humidity (%)", color="blue")
    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plt.ylabel("Humidity (%)")
    plt.title("Humidity Over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    
    return FileResponse(output_file, media_type="image/png", filename=output_file)

@app.get("/weather/wind")
def get_wind_graph():
    if df is None:
        return {"error": "weather_data.csv not found!"}
    output_file = "wind_speed_over_time.png"
    
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["wind_speed_m/s"], label="Wind Speed (m/s)", color="purple")
    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plt.ylabel("Wind Speed (m/s)")
    plt.title("Wind Speed Over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    
    return FileResponse(output_file, media_type="image/png", filename=output_file)

@app.get("/weather/precipitation")
def get_precipitation_graph():
    if df is None:
        return {"error": "weather_data.csv not found!"}
    output_file = "precipitation_over_time.png"
    
    plt.figure(figsize=(10, 5))
    plt.bar(df["time"], df["precipitation_mm"], label="Precipitation (mm)", color="green")
    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plt.ylabel("Precipitation (mm)")
    plt.title("Precipitation Over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    
    return FileResponse(output_file, media_type="image/png", filename=output_file)



