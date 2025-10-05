import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("weather_data.csv")

# ✅ Ensure 'time' is datetime (for x-axis in graphs)
df["time"] = pd.to_datetime(df["time"])

# --- Temperature over time ---
plt.figure(figsize=(10, 5))
plt.plot(df["time"], df["temperature_C"], label="Temperature (°C)", color="red")
plt.xticks(rotation=45)
plt.xlabel("Time")
plt.ylabel("Temperature (°C)")
plt.title("Temperature Over Time")
plt.legend()
plt.tight_layout()
plt.show()

# --- Humidity over time ---
plt.figure(figsize=(10, 5))
plt.plot(df["time"], df["humidity_%"], label="Humidity (%)", color="blue")
plt.xticks(rotation=45)
plt.xlabel("Time")
plt.ylabel("Humidity (%)")
plt.title("Humidity Over Time")
plt.legend()
plt.tight_layout()
plt.show()

# --- Wind Speed over time ---
plt.figure(figsize=(10, 5))
plt.plot(df["time"], df["wind_speed_m/s"], label="Wind Speed (m/s)", color="purple")
plt.xticks(rotation=45)
plt.xlabel("Time")
plt.ylabel("Wind Speed (m/s)")
plt.title("Wind Speed Over Time")
plt.legend()
plt.tight_layout()
plt.show()

# --- Precipitation over time (bar chart) ---
plt.figure(figsize=(10, 5))
plt.bar(df["time"], df["precipitation_mm"], label="Precipitation (mm)", color="green")
plt.xticks(rotation=45)
plt.xlabel("Time")
plt.ylabel("Precipitation (mm)")
plt.title("Precipitation Over Time")
plt.legend()
plt.tight_layout()
plt.show()
