import logging

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
from apps.trips.services.trip_planner import TripPlan, plan

logger = logging.getLogger("app")


@api_view(["POST"])
def plan_trip(request: Request) -> Response:
    serializer = TripPlanRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    try:
        trip_plan = plan(
            current_location=data["current_location"],
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
            cycle_hours_used=data["cycle_hours_used"],
            departure_time=data["departure_time"],
        )
    except GeocodingError as exc:
        logger.warning("Geocoding failed", extra={"error": str(exc)})
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    except RoutingError as exc:
        logger.warning("Routing failed", extra={"error": str(exc)})
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    trip = _save_trip(data, trip_plan)

    if trip_plan.route.used_fallback:
        logger.warning(
            "Trip planned with OSRM fallback — truck restrictions not applied",
            extra={"trip_id": str(trip.pk)},
        )

    return Response(
        TripPlanResponseSerializer(trip).data, status=status.HTTP_201_CREATED
    )


def _save_trip(data: dict, trip_plan: TripPlan) -> Trip:
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


@api_view(["GET"])
def geocode_suggest(request: Request) -> Response:
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response(
            {"detail": "q parameter required."}, status=status.HTTP_400_BAD_REQUEST
        )
    return Response(make_geocoder().suggest(query))


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
