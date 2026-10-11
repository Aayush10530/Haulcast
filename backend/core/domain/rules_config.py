"""Domain rules and threshold configuration."""

# Geodetic constants
EARTH_RADIUS_MILES: float = 3958.8
METERS_PER_MILE: float = 1609.344

# Checkpoint intervals (miles)
INTERVAL_SHORT_MILES: int = 10
INTERVAL_MEDIUM_MILES: int = 25
INTERVAL_LONG_MILES: int = 50
ALLOWED_INTERVALS: tuple[int, ...] = (
    INTERVAL_SHORT_MILES,
    INTERVAL_MEDIUM_MILES,
    INTERVAL_LONG_MILES,
)
AUTO_INTERVAL_SHORT_MILES: int = INTERVAL_SHORT_MILES
AUTO_INTERVAL_MEDIUM_MILES: int = INTERVAL_MEDIUM_MILES
AUTO_INTERVAL_LONG_MILES: int = INTERVAL_LONG_MILES
AUTO_INTERVAL_SHORT_MAX_MILES: float = 250.0
AUTO_INTERVAL_MEDIUM_MAX_MILES: float = 800.0

# Wind thresholds (mph)
# Low: < 25.0
# Moderate: 25.0 <= w < 35.0
# High: 35.0 <= w < 45.0
# Severe: 45.0 <= w < 55.0
# No Travel: >= 55.0
WIND_MODERATE_MPH: float = 25.0
WIND_HIGH_MPH: float = 35.0
WIND_SEVERE_MPH: float = 45.0
WIND_NO_TRAVEL_MPH: float = 55.0

# Rain thresholds (in/hr)
# Low: < 0.10
# Moderate: 0.10 <= r < 0.25
# High: 0.25 <= r < 0.50
# Severe: 0.50 <= r <= 1.00
# No Travel: > 1.00 (strictly greater)
RAIN_MODERATE_IN_HR: float = 0.10
RAIN_HIGH_IN_HR: float = 0.25
RAIN_SEVERE_IN_HR: float = 0.50
RAIN_NO_TRAVEL_IN_HR: float = 1.00

# Snow thresholds (in/hr)
# Low: < 0.5
# Moderate: 0.5 <= s < 1.0
# High: 1.0 <= s < 2.0
# Severe: 2.0 <= s <= 3.0
# No Travel: > 3.0 (strictly greater)
SNOW_MODERATE_IN_HR: float = 0.5
SNOW_HIGH_IN_HR: float = 1.0
SNOW_SEVERE_IN_HR: float = 2.0
SNOW_NO_TRAVEL_IN_HR: float = 3.0

# Load rules (weight in pounds, lb)
# High wind band (35-44 mph) + load > 40,000 lb -> at least Severe
# Severe wind band (45-54 mph) + load > 30,000 lb -> No Travel
LOAD_RULE_SEVERE_OVER_LB: float = 40_000.0
LOAD_RULE_NO_TRAVEL_OVER_LB: float = 30_000.0

# Weather alignment constants
SECONDS_PER_HOUR: int = 3600
WIND_DECIMALS: int = 1
PRECIP_DECIMALS: int = 2

# Departure window limits
DEPARTURE_PAST_GRACE_HOURS: int = 1
DEPARTURE_MAX_DAYS_AHEAD: int = 7

# Routing provider constants
TRUCK_MAX_SPEED_KMH: int = 105

# Route selection and diversity
ROUTE_OVERLAP_MAX: float = 0.85
ROUTE_OVERLAP_TOLERANCE_MILES: float = 0.3
ROUTE_OVERLAP_SAMPLE_MILES: float = 1.0
ROUTE_MAX_DURATION_RATIO: float = 1.6
VIA_ANCHOR_FRACTIONS: tuple[float, float] = (0.33, 0.66)
VIA_OFFSET_FRACTION: float = 0.12
VIA_OFFSET_MIN_MILES: float = 15.0
VIA_OFFSET_MAX_MILES: float = 60.0
MAX_ROUTES: int = 3

# Open-Meteo weather provider constants
WEATHER_GRID_DEG: float = 0.1
WEATHER_CHUNK_SIZE: int = 100
WEATHER_PAST_HOURS: int = 3
WEATHER_FORECAST_HOURS: int = 288

# Corridor and Heatmap constants
CORRIDOR_MIN_SPACING_MILES: float = 20.0
CORRIDOR_HALF_WIDTH_MILES: float = 12.0
CORRIDOR_MAX_CELLS: int = 250
CORRIDOR_STATIONS_PER_ROUTE: int = 60
HEATMAP_HOURS: int = 48
