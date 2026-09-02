#!/usr/bin/env bash

CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/slstatus-weather.json"
LAST_GOOD="${XDG_CACHE_HOME:-$HOME/.cache}/slstatus-weather-last.txt"

die_offline() {
    echo "󰖑 offline"
    exit 0
}

fallback() {
    if [ -s "$LAST_GOOD" ]; then
        cat "$LAST_GOOD"
        exit 0
    fi
    die_offline
}

render() {
    jq -r '
  .current as $c |
  (
    $c.weather_code as $w |
    if   $w == 0                then "Clear"
    elif $w == 1                then "Mostly Clear"
    elif $w == 2                then "Partly Cloudy"
    elif $w == 3                then "Overcast"
    elif ($w == 45 or $w == 48) then "Foggy"
    elif $w >= 51 and $w <= 67  then "Rainy"
    elif $w >= 71 and $w <= 77  then "Snowy"
    elif $w >= 80 and $w <= 82  then "Rainy"
    elif $w >= 95 and $w <= 99  then "Stormy"
    else "Unknown" end
  ) as $desc |
  (($c.temperature_2m | floor) | tostring) as $temp |
  "\($desc) \($temp)°C"
' "$1"
}

# --- Set your location here --------------------------------------------------
LAT="5.28"
LON="115.24"

[ -n "$LAT" ] && [ -n "$LON" ] || fallback

# --- Use cache if less than 1 hour old -------------------------------------
if [ -f "$CACHE" ]; then
    age=$(( $(date +%s) - $(stat -c %Y "$CACHE") ))
    if [ "$age" -lt 3600 ] && jq -e '.current' "$CACHE" >/dev/null 2>&1; then
        OUT="$(render "$CACHE")"
        if [ -n "$OUT" ]; then
            echo "$OUT" > "$LAST_GOOD" 2>/dev/null || true
            echo "$OUT"
            exit 0
        fi
    fi
fi

# --- Fetch weather from Open-Meteo -----------------------------------------
if ! curl -s -m 8 -o "$CACHE" \
    "https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}&current=temperature_2m,weather_code&timezone=auto" 2>/dev/null; then
    fallback
fi

if ! jq -e '.current' "$CACHE" >/dev/null 2>&1; then
    fallback
fi

# --- Render ----------------------------------------------------------------
OUT="$(render "$CACHE")"
if [ -z "$OUT" ]; then
    fallback
fi

echo "$OUT" > "$LAST_GOOD" 2>/dev/null || true
echo "$OUT"
