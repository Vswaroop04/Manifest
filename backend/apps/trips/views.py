import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.trips.exceptions import GeocodingError, RoutingError
from apps.trips.models import DayLog, Route, Trip, TripEvent, TripRequest
from apps.trips.serializers import (
    TripPlanRequestSerializer,
    TripPlanResponseSerializer,
    TripSummarySerializer,
)
from apps.trips.services.geocoding import make_geocoder
from apps.trips.services.hos_calculator import Waypoint, calculate
from apps.trips.services.log_sheet_builder import build
from apps.trips.services.route_service import get_route

logger = logging.getLogger("app")


def _geocode_all(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
) -> tuple[
    tuple[float, float],
    tuple[float, float],
    tuple[float, float],
]:
    geocoder = make_geocoder()
    results: dict[str, tuple[float, float]] = {}
    queries = {
        "current": current_location,
        "pickup": pickup_location,
        "dropoff": dropoff_location,
    }

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


@api_view(["POST"])
def plan_trip(request: Request) -> Response:
    serializer = TripPlanRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # All external calls happen before opening the transaction
    try:
        current_coords, pickup_coords, dropoff_coords = _geocode_all(
            data["current_location"],
            data["pickup_location"],
            data["dropoff_location"],
        )
    except GeocodingError as exc:
        logger.warning("Geocoding failed", extra={"error": str(exc)})
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    waypoints_latlong = [current_coords, pickup_coords, dropoff_coords]
    try:
        route_result = get_route(waypoints_latlong)
    except RoutingError as exc:
        logger.warning("Routing failed", extra={"error": str(exc)})
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    # Mile markers: pickup is at the fraction of the route from current→pickup,
    # dropoff is at the end. We approximate using straight-line distance ratio
    # since the router doesn't return per-leg distances. A single driving-hgv
    # call with 3 waypoints gives a continuous route so we split proportionally.
    pickup_waypoint = Waypoint(
        label=data["pickup_location"],
        mile_marker=route_result.total_miles / Decimal("2"),
        event_type="pickup",
        coords=pickup_coords,
    )
    dropoff_waypoint = Waypoint(
        label=data["dropoff_location"],
        mile_marker=route_result.total_miles,
        event_type="dropoff",
        coords=dropoff_coords,
    )

    events = calculate(
        departure_time=data["departure_time"],
        cycle_hours_used=data["cycle_hours_used"],
        total_miles=route_result.total_miles,
        total_drive_secs=route_result.total_drive_secs,
        waypoints=[pickup_waypoint, dropoff_waypoint],
    )

    day_logs = build(events)

    with transaction.atomic():
        trip_request = TripRequest.objects.create(
            current_location=data["current_location"],
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
            cycle_hours_used=data["cycle_hours_used"],
            departure_time=data["departure_time"],
        )

        trip = Trip.objects.create(
            request=trip_request,
            status="completed",
            current_coords=list(current_coords),
            pickup_coords=list(pickup_coords),
            dropoff_coords=list(dropoff_coords),
        )

        Route.objects.create(
            trip=trip,
            geometry=route_result.geometry,
            total_miles=route_result.total_miles,
            total_drive_secs=route_result.total_drive_secs,
            used_fallback=route_result.used_fallback,
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
                for ev in events
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
                for dl in day_logs
            ]
        )

    trip_out = (
        Trip.objects.select_related("request", "route")
        .prefetch_related("events", "day_logs")
        .get(pk=trip.pk)
    )

    if route_result.used_fallback:
        logger.warning(
            "Trip planned with OSRM fallback — truck restrictions not applied",
            extra={"trip_id": str(trip.pk)},
        )

    return Response(
        TripPlanResponseSerializer(trip_out).data, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
def geocode_suggest(request: Request) -> Response:
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response(
            {"detail": "q parameter required."}, status=status.HTTP_400_BAD_REQUEST
        )

    suggestions = make_geocoder().suggest(query)
    return Response(suggestions)


@api_view(["GET"])
def trip_detail(request: Request, trip_id: str) -> Response:
    try:
        trip = (
            Trip.objects.select_related("request", "route")
            .prefetch_related("events", "day_logs")
            .get(pk=trip_id)
        )
    except Trip.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response(TripPlanResponseSerializer(trip).data)


@api_view(["GET"])
def trip_list(request: Request) -> Response:
    trips = Trip.objects.select_related("request").order_by("-created")
    return Response(TripSummarySerializer(trips, many=True).data)
