from datetime import timedelta
from decimal import Decimal

# US FMCSA Hours of Service regulations — 49 CFR Part 395
# These are federal law, not configuration values.

HOS_DRIVE_LIMIT = timedelta(hours=11)
HOS_WINDOW_LIMIT = timedelta(hours=14)
HOS_BREAK_TRIGGER = timedelta(hours=8)
HOS_BREAK_DURATION = timedelta(minutes=30)
HOS_REST_DURATION = timedelta(hours=10)
HOS_CYCLE_LIMIT = Decimal("70")

FUEL_INTERVAL_MILES = Decimal("1000")
STOP_DURATION = timedelta(hours=1)
FUEL_STOP_DURATION = timedelta(minutes=30)
