from datetime import datetime
from decimal import Decimal

from rest_framework import serializers

from apps.trips.models import DayLog, Route, Trip, TripEvent


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=500)
    pickup_location = serializers.CharField(max_length=500)
    dropoff_location = serializers.CharField(max_length=500)
    cycle_hours_used = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("70")
    )
    departure_time = serializers.DateTimeField()

    def validate_departure_time(self, value: datetime) -> datetime:
        from django.utils import timezone

        if value < timezone.now():
            raise serializers.ValidationError("Departure time must be in the future.")
        return value


class TripEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripEvent
        fields = [
            "id",
            "event_type",
            "start_time",
            "end_time",
            "location_label",
            "coords",
            "mile_marker",
            "metadata",
        ]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = [
            "geometry",
            "total_miles",
            "total_drive_secs",
            "used_fallback",
        ]


class SegmentSerializer(serializers.Serializer):
    status = serializers.CharField()
    start_min = serializers.IntegerField()
    end_min = serializers.IntegerField()


class DayLogSerializer(serializers.ModelSerializer):
    segments = SegmentSerializer(many=True)

    class Meta:
        model = DayLog
        fields = [
            "day_number",
            "date",
            "segments",
            "total_driving",
            "total_on_duty_nd",
            "total_off_duty",
            "total_sleeper",
            "recap_70hr",
        ]


class TripSummarySerializer(serializers.ModelSerializer):
    pickup_location = serializers.CharField(source="request.pickup_location")
    dropoff_location = serializers.CharField(source="request.dropoff_location")
    departure_time = serializers.DateTimeField(source="request.departure_time")
    cycle_hours_used = serializers.DecimalField(
        source="request.cycle_hours_used",
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        model = Trip
        fields = [
            "id",
            "status",
            "pickup_location",
            "dropoff_location",
            "departure_time",
            "cycle_hours_used",
            "created",
        ]


class TripPlanResponseSerializer(serializers.ModelSerializer):
    request_id = serializers.IntegerField(source="request.id")
    pickup_location = serializers.CharField(source="request.pickup_location")
    dropoff_location = serializers.CharField(source="request.dropoff_location")
    departure_time = serializers.DateTimeField(source="request.departure_time")
    route = RouteSerializer(read_only=True)
    events = TripEventSerializer(many=True, read_only=True)
    day_logs = DayLogSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "status",
            "request_id",
            "pickup_location",
            "dropoff_location",
            "departure_time",
            "current_coords",
            "pickup_coords",
            "dropoff_coords",
            "route",
            "events",
            "day_logs",
            "created",
        ]
