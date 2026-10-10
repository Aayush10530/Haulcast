# Provider Spike Scripts (Phase P0 / F-000)

Throwaway evaluation scripts to verify routing, geocoding, and weather APIs before building production adapters.

## Contents

- `openmeteo_spike.py`: Tests Open-Meteo multi-coordinate requests, time offsets (`past_hours=3`, `forecast_hours=288`), hourly parameters (`wind_speed_10m`, `rain`, `showers`, `snowfall`), units (`mph`, `inch`, `unixtime`), and IANA timezone resolution. Requires no API key.
- `tomtom_spike.py`: Tests TomTom Routing API with `travelMode=truck`, `maxAlternatives=2`, polyline point count, legs/segments, via-waypoint fallback, and typeahead search. Requires `TOMTOM_API_KEY`.
- `here_spike.py`: Tests HERE Routing v8 with `transportMode=truck`, `alternatives=2`, and autocomplete. Requires `HERE_API_KEY`.

## Usage

```bash
# Open-Meteo (no key needed)
python backend/scripts/spike/openmeteo_spike.py

# TomTom (requires key)
$env:TOMTOM_API_KEY="your_key"
python backend/scripts/spike/tomtom_spike.py

# HERE (requires key)
$env:HERE_API_KEY="your_key"
python backend/scripts/spike/here_spike.py
```
