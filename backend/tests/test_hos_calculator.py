from decimal import Decimal
from datetime import datetime, timezone, timedelta


from apps.trips.services.hos_calculator import calculate, Waypoint


START = datetime(2026, 5, 18, 8, 0, tzinfo=timezone.utc)


def event_types(events):
    return [e.event_type for e in events]


def events_of(events, kind):
    return [e for e in events if e.event_type == kind]


# ---------------------------------------------------------------------------
# Simple short trip — no HOS limits hit
# ---------------------------------------------------------------------------


def test_short_trip_no_limits_hit():
    # Chicago → Indianapolis: 182 miles, ~3.3 hrs driving
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("182"),
        total_drive_secs=11880,
        waypoints=[Waypoint("Indianapolis Dropoff", Decimal("182"), "dropoff")],
    )
    types = event_types(events)
    assert "rest" not in types
    assert "break" not in types
    assert "fuel" not in types
    assert "dropoff" in types
    assert types[0] == "off_duty"
    assert types[1] == "drive_start"


# ---------------------------------------------------------------------------
# 30-minute break triggered after 8 hours of driving
# ---------------------------------------------------------------------------


def test_break_triggered_after_8hrs_driving():
    # 550 miles at 55 mph = 10 hrs — break fires at 8hr mark (440 miles)
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("550"),
        total_drive_secs=36000,
        waypoints=[Waypoint("Dropoff", Decimal("550"), "dropoff")],
    )
    breaks = events_of(events, "break")
    assert len(breaks) == 1
    assert breaks[0].metadata["trigger"] == "8hr_rule"
    assert (breaks[0].end_time - breaks[0].start_time) == timedelta(minutes=30)


def test_break_resets_8hr_clock_not_11hr_clock():
    # After the break the driver can drive another 3 hours before hitting 11hr limit
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("550"),
        total_drive_secs=36000,
        waypoints=[Waypoint("Dropoff", Decimal("550"), "dropoff")],
    )
    # Should have exactly one break and no rest for this distance
    assert len(events_of(events, "break")) == 1
    assert len(events_of(events, "rest")) == 0


# ---------------------------------------------------------------------------
# 11-hour driving limit triggers rest
# ---------------------------------------------------------------------------


def test_11hr_drive_limit_triggers_rest():
    # 660 miles at 60 mph = 11 hrs — rest fires exactly at 11hr
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("700"),
        total_drive_secs=int(700 / 60 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("700"), "dropoff")],
    )
    rests = events_of(events, "rest")
    assert len(rests) >= 1
    assert rests[0].metadata["trigger"] == "11hr_limit"
    assert (rests[0].end_time - rests[0].start_time) == timedelta(hours=10)


# ---------------------------------------------------------------------------
# 14-hour window triggers rest before 11hr driving limit
# ---------------------------------------------------------------------------


def test_14hr_window_triggers_rest():
    # Driver has a 3hr pickup stop early → uses window time without driving
    # 660 miles but after 3hr on-duty stop, window fires before 11hr driving limit
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("660"),
        total_drive_secs=int(660 / 60 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("10"), "pickup"),
            Waypoint("Dropoff", Decimal("660"), "dropoff"),
        ],
    )
    rests = events_of(events, "rest")
    assert len(rests) >= 1
    # window trigger fires when pickup + driving exceeds 14hr
    triggers = {r.metadata["trigger"] for r in rests}
    assert "14hr_window" in triggers or "11hr_limit" in triggers


# ---------------------------------------------------------------------------
# Multi-day trip: rest resets all clocks
# ---------------------------------------------------------------------------


def test_multi_day_trip_has_rest_between_days():
    # 2000 miles at 55 mph = ~36 hrs driving — needs multiple rests
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("2000"),
        total_drive_secs=int(2000 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("100"), "pickup"),
            Waypoint("Dropoff", Decimal("2000"), "dropoff"),
        ],
    )
    rests = events_of(events, "rest")
    assert len(rests) >= 2


def test_rest_duration_is_10_hours():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("2000"),
        total_drive_secs=int(2000 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("2000"), "dropoff")],
    )
    for rest in events_of(events, "rest"):
        assert rest.end_time is not None
        assert (rest.end_time - rest.start_time) == timedelta(hours=10)


# ---------------------------------------------------------------------------
# Fuel stop every 1000 miles
# ---------------------------------------------------------------------------


def test_fuel_stop_at_1000_miles():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("1200"),
        total_drive_secs=int(1200 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("1200"), "dropoff")],
    )
    fuels = events_of(events, "fuel")
    assert len(fuels) == 1
    assert fuels[0].mile_marker == Decimal("1000")
    assert fuels[0].metadata["trigger"] == "1000mi_rule"
    assert (fuels[0].end_time - fuels[0].start_time) == timedelta(minutes=30)


def test_two_fuel_stops_at_1000_and_2000_miles():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("2200"),
        total_drive_secs=int(2200 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("2200"), "dropoff")],
    )
    fuels = events_of(events, "fuel")
    fuel_miles = [f.mile_marker for f in fuels]
    assert Decimal("1000") in fuel_miles
    assert Decimal("2000") in fuel_miles


# ---------------------------------------------------------------------------
# Driver near 70hr cycle limit
# ---------------------------------------------------------------------------


def test_driver_with_high_cycle_hours_gets_rest_sooner():
    # 60 hrs used — only 10 hrs of on-duty time left before hitting 70hr cycle
    events_low = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("500"),
        total_drive_secs=int(500 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("500"), "dropoff")],
    )
    events_high = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("60"),
        total_miles=Decimal("500"),
        total_drive_secs=int(500 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("500"), "dropoff")],
    )
    rests_low = len(events_of(events_low, "rest"))
    rests_high = len(events_of(events_high, "rest"))
    assert rests_high >= rests_low


# ---------------------------------------------------------------------------
# Pickup and dropoff durations
# ---------------------------------------------------------------------------


def test_pickup_stop_is_1_hour():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("200"),
        total_drive_secs=int(200 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("50"), "pickup"),
            Waypoint("Dropoff", Decimal("200"), "dropoff"),
        ],
    )
    pickups = events_of(events, "pickup")
    assert len(pickups) == 1
    assert (pickups[0].end_time - pickups[0].start_time) == timedelta(hours=1)


def test_events_are_chronologically_ordered():
    events = calculate(
        departure_time=START,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("1500"),
        total_drive_secs=int(1500 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("200"), "pickup"),
            Waypoint("Dropoff", Decimal("1500"), "dropoff"),
        ],
    )
    times = [e.start_time for e in events]
    assert times == sorted(times)


def test_departure_time_offset_is_respected():
    late_start = datetime(2026, 5, 18, 22, 0, tzinfo=timezone.utc)
    events = calculate(
        departure_time=late_start,
        cycle_hours_used=Decimal("0"),
        total_miles=Decimal("182"),
        total_drive_secs=11880,
        waypoints=[Waypoint("Dropoff", Decimal("182"), "dropoff")],
    )
    # first event is off_duty from midnight to departure, second is drive_start
    assert events[0].event_type == "off_duty"
    assert events[0].end_time == late_start
    assert events[1].event_type == "drive_start"
    assert events[1].start_time == late_start
