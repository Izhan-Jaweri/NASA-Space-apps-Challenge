import requests
import pandas as pd

# Step 1: Location select karo (Toronto, Canada)
latitude = 43.7
longitude = -79.42

# Step 2: Open-Meteo API URL banao
url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={latitude}&longitude={longitude}"
    f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"
)

# Step 3: API request bhejo
response = requests.get(url)
data = response.json()

# Step 4: Hourly data ko pandas DataFrame me convert karo
hourly = data['hourly']
df = pd.DataFrame({
    "time": hourly["time"],
    "temperature_2m": hourly["temperature_2m"],
    "relative_humidity_2m": hourly["relative_humidity_2m"],
    "wind_speed_10m": hourly["wind_speed_10m"],
    "precipitation": hourly["precipitation"]
})

# Step 5: First 10 rows print karo
print(df.head(10))

# Optional: CSV me save karna ho to
df.to_csv("toronto_weather.csv", index=False)
print("Weather data saved to toronto_weather.csv")
