"""Domain rules and threshold configuration."""

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
