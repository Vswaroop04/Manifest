import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.trips.exceptions import GeocodingError, RoutingError
from apps.trips.models import Trip
from apps.trips.serializers import (
    TripPlanRequestSerializer,
    TripPlanResponseSerializer,
    TripSummarySerializer,
)
from apps.trips.services.geocoding import make_geocoder
from apps.trips.services.trip_planner import plan, save

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

    trip = save(
        current_location=data["current_location"],
        pickup_location=data["pickup_location"],
        dropoff_location=data["dropoff_location"],
        cycle_hours_used=data["cycle_hours_used"],
        departure_time=data["departure_time"],
        trip_plan=trip_plan,
    )

    if trip_plan.route.used_fallback:
        logger.warning(
            "Trip planned with OSRM fallback — truck restrictions not applied",
            extra={"trip_id": str(trip.pk)},
        )

    return Response(
        TripPlanResponseSerializer(trip).data, status=status.HTTP_201_CREATED
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
