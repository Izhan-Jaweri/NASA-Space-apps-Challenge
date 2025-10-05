import requests
import pandas as pd

# Location: Canada example (Ottawa)
latitude = 45.4215
longitude = -75.6972

# Open-Meteo API
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"

response = requests.get(url)
if response.status_code == 200:
    data = response.json()

    # Convert to dataframe
    df = pd.DataFrame({
        "time": data["hourly"]["time"],
        "temperature_C": data["hourly"]["temperature_2m"],
        "humidity_%": data["hourly"]["relative_humidity_2m"],
        "wind_speed_m/s": data["hourly"]["wind_speed_10m"],
        "precipitation_mm": data["hourly"]["precipitation"]
    })

    print("First 10 rows of weather data:")
    print(df.head(10))
    df.to_csv("weather_data.csv", index=False)
    print("Weather data saved to weather_data.csv")
    df.to_csv("weather_data.csv", index=False)
else:
    print("Error:", response.status_code)
