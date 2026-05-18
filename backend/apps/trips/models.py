import uuid
from django.db import models
from model_utils.models import TimeStampedModel


class TripStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class EventType(models.TextChoices):
    DRIVE_START = "drive_start", "Drive Start"
    DRIVE_END = "drive_end", "Drive End"
    BREAK = "break", "Break"
    FUEL = "fuel", "Fuel Stop"
    PICKUP = "pickup", "Pickup"
    DROPOFF = "dropoff", "Dropoff"
    REST = "rest", "Rest"


class TripRequest(TimeStampedModel):
    current_location = models.CharField(max_length=500)
    pickup_location = models.CharField(max_length=500)
    dropoff_location = models.CharField(max_length=500)
    cycle_hours_used = models.DecimalField(max_digits=5, decimal_places=2)
    departure_time = models.DateTimeField()

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"{self.current_location} → {self.pickup_location} → {self.dropoff_location}"


class Trip(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.OneToOneField(TripRequest, on_delete=models.CASCADE, related_name="trip")
    status = models.CharField(max_length=20, choices=TripStatus.choices, default=TripStatus.PENDING)

    current_coords = models.JSONField(null=True, blank=True)
    pickup_coords = models.JSONField(null=True, blank=True)
    dropoff_coords = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Trip {self.id} [{self.status}]"


class Route(TimeStampedModel):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="route")
    geometry = models.JSONField()
    total_miles = models.DecimalField(max_digits=8, decimal_places=1)
    total_drive_secs = models.IntegerField()
    used_fallback = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Route for {self.trip_id} — {self.total_miles:.1f} mi"


class TripEvent(TimeStampedModel):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    location_label = models.CharField(max_length=500, blank=True)
    coords = models.JSONField(null=True, blank=True)
    mile_marker = models.DecimalField(max_digits=8, decimal_places=1)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["trip", "start_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.mile_marker:.0f} mi — {self.start_time}"


class DayLog(TimeStampedModel):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="day_logs")
    day_number = models.PositiveSmallIntegerField()
    date = models.DateField()
    segments = models.JSONField()
    total_driving = models.DecimalField(max_digits=5, decimal_places=2)
    total_on_duty_nd = models.DecimalField(max_digits=5, decimal_places=2)
    total_off_duty = models.DecimalField(max_digits=5, decimal_places=2)
    total_sleeper = models.DecimalField(max_digits=5, decimal_places=2)
    recap_70hr = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        ordering = ["day_number"]
        unique_together = [("trip", "day_number")]

    def __str__(self) -> str:
        return f"Day {self.day_number} log for trip {self.trip_id}"
