import os
from dotenv import load_dotenv

load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY", "")
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "")

# Test addresses — mix of simple cities, full addresses, and ambiguous queries
GEOCODING_TEST_CASES = [
    {
        "id": "chicago_simple",
        "query": "Chicago, IL",
        "expected_lat": 41.8781,
        "expected_lng": -87.6298,
    },
    {
        "id": "dallas_simple",
        "query": "Dallas, TX",
        "expected_lat": 32.7767,
        "expected_lng": -96.7970,
    },
    {
        "id": "los_angeles_simple",
        "query": "Los Angeles, CA",
        "expected_lat": 34.0522,
        "expected_lng": -118.2437,
    },
    {
        "id": "memphis_trucking_hub",
        "query": "Memphis, TN",
        "expected_lat": 35.1495,
        "expected_lng": -90.0490,
    },
    {
        "id": "full_street_address",
        "query": "350 Fifth Avenue, New York, NY 10118",
        "expected_lat": 40.7484,
        "expected_lng": -73.9857,
    },
    {
        "id": "highway_exit_style",
        "query": "I-40 Amarillo TX",
        "expected_lat": 35.2220,
        "expected_lng": -101.8313,
    },
    {
        "id": "zip_code_only",
        "query": "77001",
        "expected_lat": 29.7604,
        "expected_lng": -95.3698,
    },
    {
        "id": "ambiguous_city",
        "query": "Springfield",
        "expected_lat": None,  # ambiguous — testing what each provider returns
        "expected_lng": None,
    },
]

# Routes for routing benchmarks — (start_coords, end_coords, label, expected_miles_approx)
# Coords format: [lng, lat] — ORS convention
ROUTING_TEST_CASES = [
    {
        "id": "short_midwest",
        "label": "Chicago → Indianapolis",
        "start": [-87.6298, 41.8781],
        "end": [-86.1581, 39.7684],
        "expected_miles": 182,
        "tolerance_pct": 10,
    },
    {
        "id": "medium_south",
        "label": "Dallas → Memphis",
        "start": [-96.7970, 32.7767],
        "end": [-90.0490, 35.1495],
        "expected_miles": 470,
        "tolerance_pct": 10,
    },
    {
        "id": "long_cross_country",
        "label": "Chicago → Los Angeles",
        "start": [-87.6298, 41.8781],
        "end": [-118.2437, 34.0522],
        "expected_miles": 2020,
        "tolerance_pct": 10,
    },
    {
        "id": "very_long_coast_to_coast",
        "label": "New York → Los Angeles",
        "start": [-74.0060, 40.7128],
        "end": [-118.2437, 34.0522],
        "expected_miles": 2790,
        "tolerance_pct": 10,
    },
    {
        "id": "multi_waypoint",
        "label": "Chicago → Dallas → Los Angeles",
        "start": [-87.6298, 41.8781],
        "waypoint": [-96.7970, 32.7767],
        "end": [-118.2437, 34.0522],
        "expected_miles": 2940,
        "tolerance_pct": 10,
    },
]

# How many times to call each provider per test case (for statistical reliability)
BENCHMARK_RUNS = 5

# Seconds to wait between calls to the same provider (rate limit safety)
RATE_LIMIT_DELAY = 1.1
