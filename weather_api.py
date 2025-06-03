
import requests

def fetch_weather_data(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=evapotranspiration_evaporation,precipitation_sum&timezone=Asia%2FTokyo"
        response = requests.get(url)
        data = response.json()
        et0 = float(data["daily"]["evapotranspiration_evaporation"][0])
        rain = float(data["daily"]["precipitation_sum"][0])
        return et0, rain
    except:
        return 4.5, 1.5
