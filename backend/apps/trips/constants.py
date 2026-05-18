from datetime import timedelta
from decimal import Decimal

# US FMCSA Hours of Service — 49 CFR Part 395
# Federal law, not configuration values.
HOS_DRIVE_LIMIT = timedelta(hours=11)
HOS_WINDOW_LIMIT = timedelta(hours=14)
HOS_BREAK_TRIGGER = timedelta(hours=8)
HOS_BREAK_DURATION = timedelta(minutes=30)
HOS_REST_DURATION = timedelta(hours=10)
HOS_CYCLE_LIMIT = Decimal("70")

FUEL_INTERVAL_MILES = Decimal("1000")
STOP_DURATION = timedelta(hours=1)
FUEL_STOP_DURATION = timedelta(minutes=30)

# Unit conversions
METERS_PER_MILE = Decimal("1609.344")

# HTTP client config
HTTP_TIMEOUT = 10
HTTP_HEADERS = {"User-Agent": "ELD-TripPlanner/1.0"}

# Geocoding cache
GEOCODING_CACHE_TTL = 60 * 60 * 24  # 24 hours

# Event type groupings used by log sheet builder
ON_DUTY_ND_TYPES: frozenset[str] = frozenset({"fuel", "pickup", "dropoff"})
OFF_DUTY_TYPES: frozenset[str] = frozenset({"rest", "break"})
