import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from apps.trips.exceptions import GeocodingError
from apps.trips.services.geocoding import make_geocoder
from apps.trips.services.hos_calculator import TripEventData, Waypoint, calculate
from apps.trips.services.log_sheet_builder import DayLogData, build
from apps.trips.services.route_service import RouteResult, get_route

logger = logging.getLogger("app")


@dataclass
class TripPlan:
    current_coords: tuple[float, float]
    pickup_coords: tuple[float, float]
    dropoff_coords: tuple[float, float]
    route: RouteResult
    events: list[TripEventData]
    day_logs: list[DayLogData]


def plan(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
    cycle_hours_used: Decimal,
    departure_time: datetime,
) -> TripPlan:
    current_coords, pickup_coords, dropoff_coords = _geocode_all(
        current_location, pickup_location, dropoff_location
    )

    route = get_route([current_coords, pickup_coords, dropoff_coords])

    pickup_waypoint = Waypoint(
        label=pickup_location,
        mile_marker=route.total_miles / Decimal("2"),
        event_type="pickup",
        coords=pickup_coords,
    )
    dropoff_waypoint = Waypoint(
        label=dropoff_location,
        mile_marker=route.total_miles,
        event_type="dropoff",
        coords=dropoff_coords,
    )

    events = calculate(
        departure_time=departure_time,
        cycle_hours_used=cycle_hours_used,
        total_miles=route.total_miles,
        total_drive_secs=route.total_drive_secs,
        waypoints=[pickup_waypoint, dropoff_waypoint],
    )

    day_logs = build(events)

    return TripPlan(
        current_coords=current_coords,
        pickup_coords=pickup_coords,
        dropoff_coords=dropoff_coords,
        route=route,
        events=events,
        day_logs=day_logs,
    )


def _geocode_all(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    geocoder = make_geocoder()
    queries = {
        "current": current_location,
        "pickup": pickup_location,
        "dropoff": dropoff_location,
    }
    results: dict[str, tuple[float, float]] = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(geocoder.geocode, q): key for key, q in queries.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            coords = future.result()
            if coords is None:
                raise GeocodingError(f"Could not geocode {key!r}: {queries[key]!r}")
            results[key] = coords

    return results["current"], results["pickup"], results["dropoff"]
