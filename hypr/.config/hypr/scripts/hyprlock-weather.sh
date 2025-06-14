#!/bin/bash
set -euo pipefail

API_KEY="9b4ed6ed426f922fdfd236c6003645e1"
UNITS="metric"
LOCATION="Sylhet,Bangladesh"
WEATHER_FILE="$HOME/.cache/hyprlock_weather.txt"
DETAILED_FILE="$HOME/.cache/hyprlock_weather_detailed.txt"

mkdir -p "$(dirname "$WEATHER_FILE")"

update_weather() {
  echo " -- Weather Unavailable" > "$WEATHER_FILE"
  
  WEATHER_JSON=$(curl -sf --max-time 5 "https://api.openweathermap.org/data/2.5/weather?q=$LOCATION&appid=$API_KEY&units=$UNITS") || {
    echo " -- Network Error" > "$WEATHER_FILE"
    return
  }

  if ! jq -e '.main.temp' <<<"$WEATHER_JSON" > /dev/null; then
    echo " -- Invalid API Response" > "$WEATHER_FILE"
    return
  fi

  TEMP=$(jq -r '.main.temp' <<<"$WEATHER_JSON" | awk '{printf "%.0f", $1}')
  FEELS_LIKE=$(jq -r '.main.feels_like' <<<"$WEATHER_JSON" | awk '{printf "%.0f", $1}')
  HUMIDITY=$(jq -r '.main.humidity' <<<"$WEATHER_JSON")
  WIND_SPEED=$(jq -r '.wind.speed' <<<"$WEATHER_JSON" | awk '{printf "%.0f", $1}')
  WIND_DIR=$(jq -r '.wind.deg' <<<"$WEATHER_JSON")

  deg_to_dir() {
    dirs=(N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW)
    echo "${dirs[$(( ($1 + 11) / 22 ))]}"
  }

  WIND_DIR=$(deg_to_dir $WIND_DIR)
  CONDITION=$(jq -r '.weather[0].description' <<<"$WEATHER_JSON" | sed 's/\b./\u&/g')
  ICON_CODE=$(jq -r '.weather[0].id' <<<"$WEATHER_JSON")

  case $ICON_CODE in
    200|201|202|210|211|212|221|230|231|232) ICON="⛈️" ;;
    300|301|302|310|311|312|313|314|321) ICON="🌦️" ;;
    500) ICON="🌦️" ;;
    501) ICON="🌧️" ;;
    502|503|504) ICON="🌧️" ;;
    511) ICON="🌨️" ;;
    520|521|522|531) ICON="🌧️" ;;
    600|601|602) ICON="❄️" ;;
    611|612|613|615|616|620|621|622) ICON="🌨️" ;;
    701|711|721|731|741|751|761|762) ICON="🌫️" ;;
    771) ICON="🌬️" ;;
    781) ICON="🌪️" ;;
    800) ICON="☀️" ;;
    801) ICON="🌤️" ;;
    802) ICON="⛅" ;;
    803) ICON="🌥️" ;;
    804) ICON="☁️" ;;
    *) ICON="❔" ;;
  esac

  echo "$ICON  $TEMP°C - $CONDITION" > "$WEATHER_FILE"

  cat > "$DETAILED_FILE" << EOF
$ICON  $TEMP°C
$CONDITION
Feels like: $FEELS_LIKE°C
Humidity: $HUMIDITY%
Wind: $WIND_SPEED km/h $WIND_DIR
EOF
}

# Run once immediately
update_weather

while true; do
  sleep 5
  update_weather
done

