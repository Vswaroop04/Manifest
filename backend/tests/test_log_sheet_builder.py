from decimal import Decimal
from datetime import datetime, timezone

from apps.trips.services.hos_calculator import calculate, Waypoint
from apps.trips.services.log_sheet_builder import build


START = datetime(2026, 5, 18, 8, 0, tzinfo=timezone.utc)


def _build_for(total_miles, total_drive_secs, waypoints=None, departure_time=START):
    waypoints = waypoints or [Waypoint("Dropoff", total_miles, "dropoff")]
    events = calculate(
        departure_time=departure_time,
        cycle_hours_used=Decimal("0"),
        total_miles=total_miles,
        total_drive_secs=total_drive_secs,
        waypoints=waypoints,
    )
    return build(events)


def test_build_empty_events_returns_empty():
    assert build([]) == []


def test_single_day_short_trip():
    logs = _build_for(Decimal("100"), int(100 / 55 * 3600))
    assert len(logs) == 1
    assert logs[0].day_number == 1


def test_segments_cover_full_24_hours():
    logs = _build_for(Decimal("100"), int(100 / 55 * 3600))
    total_mins = sum(s.end_min - s.start_min for s in logs[0].segments)
    assert total_mins == 1440


def test_segments_have_no_gaps():
    logs = _build_for(Decimal("100"), int(100 / 55 * 3600))
    segs = logs[0].segments
    for i in range(len(segs) - 1):
        assert segs[i].end_min == segs[i + 1].start_min


def test_segments_start_at_zero_and_end_at_1440():
    logs = _build_for(Decimal("100"), int(100 / 55 * 3600))
    segs = logs[0].segments
    assert segs[0].start_min == 0
    assert segs[-1].end_min == 1440


def test_driving_hours_match_expected():
    # 110 miles at 55mph = exactly 2.0 hours driving
    logs = _build_for(Decimal("110"), int(110 / 55 * 3600))
    assert logs[0].total_driving == Decimal("2.00")


def test_on_duty_nd_includes_pickup_and_dropoff():
    logs = _build_for(
        Decimal("200"),
        int(200 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("100"), "pickup"),
            Waypoint("Dropoff", Decimal("200"), "dropoff"),
        ],
    )
    total_on_duty_nd = sum(l.total_on_duty_nd for l in logs)
    assert total_on_duty_nd == Decimal("2.00")


def test_recap_70hr_accumulates_across_days():
    logs = _build_for(
        Decimal("2000"),
        int(2000 / 55 * 3600),
        waypoints=[
            Waypoint("Pickup", Decimal("100"), "pickup"),
            Waypoint("Dropoff", Decimal("2000"), "dropoff"),
        ],
    )
    assert len(logs) > 1
    for i in range(1, len(logs)):
        assert logs[i].recap_70hr >= logs[i - 1].recap_70hr


def test_recap_70hr_on_day1_equals_day1_on_duty():
    logs = _build_for(Decimal("100"), int(100 / 55 * 3600))
    day = logs[0]
    expected = (day.total_driving + day.total_on_duty_nd).quantize(Decimal("0.01"))
    assert day.recap_70hr == expected


def test_multi_day_trip_has_multiple_day_logs():
    logs = _build_for(
        Decimal("2000"),
        int(2000 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("2000"), "dropoff")],
    )
    assert len(logs) > 1


def test_day_numbers_are_sequential():
    logs = _build_for(
        Decimal("2000"),
        int(2000 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("2000"), "dropoff")],
    )
    for i, log in enumerate(logs, start=1):
        assert log.day_number == i


def test_each_day_covers_full_24_hours():
    logs = _build_for(
        Decimal("2000"),
        int(2000 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("2000"), "dropoff")],
    )
    for log in logs:
        total_mins = sum(s.end_min - s.start_min for s in log.segments)
        assert total_mins == 1440, f"Day {log.day_number} has {total_mins} mins, expected 1440"


def test_pre_departure_period_is_off_duty():
    logs = _build_for(Decimal("100"), int(100 / 55 * 3600))
    first_seg = logs[0].segments[0]
    assert first_seg.status == "off_duty"
    assert first_seg.start_min == 0


def test_rest_segments_are_off_duty():
    logs = _build_for(
        Decimal("700"),
        int(700 / 55 * 3600),
        waypoints=[Waypoint("Dropoff", Decimal("700"), "dropoff")],
    )
    all_statuses = {s.status for log in logs for s in log.segments}
    assert "off_duty" in all_statuses
