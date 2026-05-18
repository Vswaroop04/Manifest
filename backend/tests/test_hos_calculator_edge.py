from decimal import Decimal
from datetime import datetime, timezone, timedelta

from apps.trips.services.hos_calculator import calculate, Waypoint

START = datetime(2026, 5, 18, 8, 0, tzinfo=timezone.utc)
MIDNIGHT = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)


def events_of(events, kind):
    return [e for e in events if e.event_type == kind]


def event_types(events):
    return [e.event_type for e in events]


def test_zero_miles_returns_empty():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("0"),
        total_drive_secs=0,
        waypoints=[],
    )
    assert events == []


def test_no_pre_departure_event_when_departing_at_midnight():
    events = calculate(
        departure_time=MIDNIGHT,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("100"),
        total_drive_secs=int(100 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("100"), "dropoff")],
    )
    assert events[0].event_type == "drive_start"


def test_pre_departure_off_duty_spans_midnight_to_departure():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("100"),
        total_drive_secs=int(100 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("100"), "dropoff")],
    )
    pre = events[0]
    assert pre.event_type == "off_duty"
    assert pre.start_time == MIDNIGHT
    assert pre.end_time == START
    assert pre.metadata["trigger"] == "pre_departure"


def test_post_arrival_off_duty_appended():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("100"),
        total_drive_secs=int(100 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("100"), "dropoff")],
    )
    last = events[-1]
    assert last.event_type == "off_duty"
    assert last.metadata["trigger"] == "post_arrival"


def test_post_arrival_off_duty_ends_at_end_of_day():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("100"),
        total_drive_secs=int(100 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("100"), "dropoff")],
    )
    last = events[-1]
    assert last.end_time is not None
    assert last.end_time.hour == 23
    assert last.end_time.minute == 59
    assert last.end_time.second == 59


def test_dropoff_stop_is_1_hour():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("200"),
        total_drive_secs=int(200 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("100"), "pickup"),
            Waypoint("Dropoff", Decimal("200"), "dropoff"),
        ],
    )
    dropoffs = events_of(events, "dropoff")
    assert len(dropoffs) == 1
    assert (dropoffs[0].end_time - dropoffs[0].start_time) == timedelta(hours=1)


def test_pickup_appears_before_dropoff():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("300"),
        total_drive_secs=int(300 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("100"), "pickup"),
            Waypoint("Dropoff", Decimal("300"), "dropoff"),
        ],
    )
    types = event_types(events)
    pickup_idx = next(i for i, t in enumerate(types) if t == "pickup")
    dropoff_idx = next(i for i, t in enumerate(types) if t == "dropoff")
    assert pickup_idx < dropoff_idx


def test_mile_markers_are_monotonically_non_decreasing():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("1500"),
        total_drive_secs=int(1500 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("300"), "pickup"),
            Waypoint("Dropoff", Decimal("1500"), "dropoff"),
        ],
    )
    markers = [e.mile_marker for e in events]
    assert markers == sorted(markers)


def test_every_drive_start_has_matching_drive_end():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("1500"),
        total_drive_secs=int(1500 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("1500"), "dropoff")],
    )
    starts = len(events_of(events, "drive_start"))
    ends = len(events_of(events, "drive_end"))
    assert starts == ends


def test_break_does_not_reset_11hr_driving_clock():
    # After the 8hr break the driver only has 3hrs left (11 - 8), not a fresh 11.
    # A 700-mile trip at 55mph needs a rest — confirms break didn't reset 11hr clock.
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("700"),
        total_drive_secs=int(700 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("700"), "dropoff")],
    )
    rests = events_of(events, "rest")
    assert len(rests) >= 1


def test_70hr_cycle_limit_triggers_rest():
    # 68hrs used, only 2hrs left on cycle — cycle rest fires before 11hr limit
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("68"),
        total_miles=Decimal("500"),
        total_drive_secs=int(500 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("500"), "dropoff")],
    )
    rests = events_of(events, "rest")
    assert len(rests) >= 1
    triggers = {r.metadata["trigger"] for r in rests}
    assert "70hr_cycle" in triggers


def test_full_cycle_hours_forces_immediate_rest():
    # 70hrs used — driver is at cycle limit, must rest before driving
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("70"),
        total_miles=Decimal("200"),
        total_drive_secs=int(200 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("200"), "dropoff")],
    )
    rests = events_of(events, "rest")
    assert len(rests) >= 1
    assert rests[0].metadata["trigger"] == "70hr_cycle"
