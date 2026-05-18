from datetime import timedelta

import pytest
from django.utils import timezone

from apps.trips.serializers import TripPlanRequestSerializer


def future_dt(hours=1):
    return (timezone.now() + timedelta(hours=hours)).isoformat()


def valid_payload(**overrides):
    base = {
        "current_location": "Chicago, IL",
        "pickup_location": "Indianapolis, IN",
        "dropoff_location": "Columbus, OH",
        "cycle_hours_used": "0.00",
        "departure_time": future_dt(),
    }
    base.update(overrides)
    return base


def test_valid_payload_is_accepted():
    s = TripPlanRequestSerializer(data=valid_payload())
    assert s.is_valid(), s.errors


def test_cycle_hours_above_70_rejected():
    s = TripPlanRequestSerializer(data=valid_payload(cycle_hours_used="71"))
    assert not s.is_valid()
    assert "cycle_hours_used" in s.errors


def test_cycle_hours_exactly_70_accepted():
    s = TripPlanRequestSerializer(data=valid_payload(cycle_hours_used="70.00"))
    assert s.is_valid(), s.errors


def test_cycle_hours_negative_rejected():
    s = TripPlanRequestSerializer(data=valid_payload(cycle_hours_used="-1"))
    assert not s.is_valid()
    assert "cycle_hours_used" in s.errors


def test_cycle_hours_zero_accepted():
    s = TripPlanRequestSerializer(data=valid_payload(cycle_hours_used="0.00"))
    assert s.is_valid(), s.errors


def test_past_departure_time_rejected():
    past = (timezone.now() - timedelta(hours=1)).isoformat()
    s = TripPlanRequestSerializer(data=valid_payload(departure_time=past))
    assert not s.is_valid()
    assert "departure_time" in s.errors


def test_future_departure_time_accepted():
    s = TripPlanRequestSerializer(data=valid_payload(departure_time=future_dt(hours=2)))
    assert s.is_valid(), s.errors


@pytest.mark.parametrize("missing_field", [
    "current_location",
    "pickup_location",
    "dropoff_location",
    "cycle_hours_used",
    "departure_time",
])
def test_missing_required_field_rejected(missing_field):
    payload = valid_payload()
    del payload[missing_field]
    s = TripPlanRequestSerializer(data=payload)
    assert not s.is_valid()
    assert missing_field in s.errors


def test_location_exceeding_500_chars_rejected():
    s = TripPlanRequestSerializer(data=valid_payload(current_location="A" * 501))
    assert not s.is_valid()
    assert "current_location" in s.errors
