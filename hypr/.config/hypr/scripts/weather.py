#!/usr/bin/env python3
import requests
import sys
import json

API_KEY = "9b4ed6ed426f922fdfd236c6003645e1"
UNITS = "metric"
LOCATION = "Sylhet,Bangladesh"
UNIT_SYMBOL = "C"
API_URL = f"https://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={API_KEY}&units={UNITS}"

def error_output(text=" --", tooltip="Script Error", class_="error"):
    print(json.dumps({"text": text, "tooltip": tooltip, "class": class_}))
    sys.exit(0)

try:
    response = requests.get(API_URL, timeout=5)
    response.raise_for_status()
    data = response.json()
except (requests.RequestException, ValueError):
    error_output(tooltip="Network Error")

# Validate expected data
try:
    temp = round(data["main"]["temp"])
    feels_like = round(data["main"]["feels_like"])
    humidity = data["main"]["humidity"]
    wind_speed = round(data["wind"]["speed"])
    wind_deg = data["wind"]["deg"]
    location_name = data["name"]
    condition = data["weather"][0]["description"].title()
    icon_code = data["weather"][0]["id"]
except (KeyError, TypeError, IndexError):
    error_output(tooltip="Invalid API Response")

# Convert wind degree to compass
def deg_to_dir(deg):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[int((deg + 11.25) / 22.5) % 16]

wind_dir = deg_to_dir(wind_deg)

# Weather icon map
icon_map = {
    range(200, 233): "⛈️",
    range(300, 322): "🌦️",
    (500,): "🌦️",
    (501,): "🌧️",
    (502, 503, 504): "🌧️",
    (511,): "🌨️",
    range(520, 532): "🌧️",
    range(600, 603): "❄️",
    range(611, 623): "🌨️",
    (701, 711, 721, 731, 741, 751, 761, 762): "🌫️",
    (771,): "🌬️",
    (781,): "🌪️",
    (800,): "☀️",
    (801,): "🌤️",
    (802,): "⛅",
    (803,): "🌥️",
    (804,): "☁️",
}

icon = "❔"
for key, val in icon_map.items():
    if isinstance(key, range) and icon_code in key:
        icon = val
        break
    elif icon_code in key:
        icon = val
        break

# Final output
print(json.dumps({
    "text": f"{icon} {temp}°{UNIT_SYMBOL}",
    "tooltip": f"Location: {location_name}\nCondition: {condition}\nTemperature: {temp}°{UNIT_SYMBOL}\n"
               f"Feels Like: {feels_like}°{UNIT_SYMBOL}\nHumidity: {humidity}%\nWind: {wind_speed} km/h {wind_dir}",
    "class": "weather"
}))

