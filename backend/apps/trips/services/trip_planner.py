import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from apps.trips.exceptions import GeocodingError
from apps.trips.models import DayLog, Route, Trip, TripEvent, TripRequest
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

    with ThreadPoolExecutor(max_workers=2) as ex:
        full_future = ex.submit(get_route, [current_coords, pickup_coords, dropoff_coords])
        pickup_segment_future = ex.submit(get_route, [current_coords, pickup_coords])

    route = full_future.result()
    pickup_miles = pickup_segment_future.result().total_miles

    pickup_waypoint = Waypoint(
        label=pickup_location,
        mile_marker=pickup_miles,
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

    return TripPlan(
        current_coords=current_coords,
        pickup_coords=pickup_coords,
        dropoff_coords=dropoff_coords,
        route=route,
        events=events,
        day_logs=build(events),
    )


def save(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
    cycle_hours_used: Decimal,
    departure_time: datetime,
    trip_plan: TripPlan,
) -> Trip:
    with transaction.atomic():
        trip_request = TripRequest.objects.create(
            current_location=current_location,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            cycle_hours_used=cycle_hours_used,
            departure_time=departure_time,
        )
        trip = Trip.objects.create(
            request=trip_request,
            status="completed",
            current_coords=list(trip_plan.current_coords),
            pickup_coords=list(trip_plan.pickup_coords),
            dropoff_coords=list(trip_plan.dropoff_coords),
        )
        Route.objects.create(
            trip=trip,
            geometry=trip_plan.route.geometry,
            total_miles=trip_plan.route.total_miles,
            total_drive_secs=trip_plan.route.total_drive_secs,
            used_fallback=trip_plan.route.used_fallback,
        )
        TripEvent.objects.bulk_create(
            [
                TripEvent(
                    trip=trip,
                    event_type=ev.event_type,
                    start_time=ev.start_time,
                    end_time=ev.end_time,
                    location_label=ev.location_label,
                    coords=list(ev.coords) if ev.coords else None,
                    mile_marker=ev.mile_marker,
                    metadata=ev.metadata,
                )
                for ev in trip_plan.events
            ]
        )
        DayLog.objects.bulk_create(
            [
                DayLog(
                    trip=trip,
                    day_number=dl.day_number,
                    date=dl.date,
                    segments=[
                        {
                            "status": s.status,
                            "start_min": s.start_min,
                            "end_min": s.end_min,
                        }
                        for s in dl.segments
                    ],
                    total_driving=dl.total_driving,
                    total_on_duty_nd=dl.total_on_duty_nd,
                    total_off_duty=dl.total_off_duty,
                    total_sleeper=dl.total_sleeper,
                    recap_70hr=dl.recap_70hr,
                )
                for dl in trip_plan.day_logs
            ]
        )

    return (
        Trip.objects.select_related("request", "route")
        .prefetch_related("events", "day_logs")
        .get(pk=trip.pk)
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
