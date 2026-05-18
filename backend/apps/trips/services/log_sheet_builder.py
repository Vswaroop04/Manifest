from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from apps.trips.services.hos_calculator import TripEventData

_ON_DUTY_ND_TYPES = {"fuel", "pickup", "dropoff"}
_OFF_DUTY_TYPES = {"rest", "break"}


@dataclass
class Segment:
    status: str
    start_min: int
    end_min: int


@dataclass
class DayLogData:
    day_number: int
    date: date
    segments: list[Segment]
    total_driving: Decimal
    total_on_duty_nd: Decimal
    total_off_duty: Decimal
    total_sleeper: Decimal
    recap_70hr: Decimal


def build(events: list[TripEventData], departure_date: date) -> list[DayLogData]:
    """
    Convert a flat list of TripEventData into per-day DayLogData.
    Segments cover the full 24-hour period — gaps between events are off-duty.
    """
    if not events:
        return []

    day_map: dict[date, list[tuple[str, int, int]]] = {}

    def record(status: str, start_dt, end_dt) -> None:
        current = start_dt.date()
        remaining_end = end_dt

        while current <= remaining_end.date():
            day_start = start_dt if current == start_dt.date() else start_dt.replace(
                year=current.year, month=current.month, day=current.day,
                hour=0, minute=0, second=0, microsecond=0,
            )
            day_end_boundary = day_start.replace(
                hour=23, minute=59, second=59, microsecond=0,
            )

            seg_start = max(start_dt, day_start)
            seg_end = min(remaining_end, day_end_boundary)

            if seg_end > seg_start:
                start_min = int((seg_start - seg_start.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() // 60)
                end_min = int((seg_end - seg_end.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() // 60)
                if current not in day_map:
                    day_map[current] = []
                day_map[current].append((status, start_min, min(end_min, 1440)))

            current = date(current.year, current.month, current.day) + timedelta(days=1)
            start_dt = seg_end

    # Walk paired drive_start/drive_end and standalone stops
    i = 0
    while i < len(events):
        ev = events[i]

        if ev.event_type == "drive_start":
            # Find matching drive_end
            j = i + 1
            while j < len(events) and events[j].event_type != "drive_end":
                j += 1
            if j < len(events):
                record("driving", ev.start_time, events[j].start_time)
                i = j + 1
            else:
                i += 1

        elif ev.event_type in _ON_DUTY_ND_TYPES and ev.end_time:
            record("on_duty_nd", ev.start_time, ev.end_time)
            i += 1

        elif ev.event_type in _OFF_DUTY_TYPES and ev.end_time:
            record("off_duty", ev.start_time, ev.end_time)
            i += 1

        else:
            i += 1

    if not day_map:
        return []

    all_days = sorted(day_map.keys())
    result: list[DayLogData] = []
    running_on_duty = Decimal("0")

    for day_num, day_date in enumerate(all_days, start=1):
        raw_segs = sorted(day_map.get(day_date, []), key=lambda s: s[1])

        # Fill off-duty gaps so the 24hr grid is complete
        filled: list[tuple[str, int, int]] = []
        cursor = 0
        for status, s, e in raw_segs:
            if s > cursor:
                filled.append(("off_duty", cursor, s))
            filled.append((status, s, e))
            cursor = e
        if cursor < 1440:
            filled.append(("off_duty", cursor, 1440))

        segments = [Segment(status=s, start_min=a, end_min=b) for s, a, b in filled]

        def total_hrs(status_name: str) -> Decimal:
            mins = sum(b - a for s, a, b in filled if s == status_name)
            return Decimal(str(mins)) / Decimal("60")

        driving = total_hrs("driving")
        on_duty_nd = total_hrs("on_duty_nd")
        off_duty = total_hrs("off_duty")
        sleeper = total_hrs("sleeper")

        running_on_duty += (driving + on_duty_nd).quantize(Decimal("0.01"))

        result.append(DayLogData(
            day_number=day_num,
            date=day_date,
            segments=segments,
            total_driving=driving.quantize(Decimal("0.01")),
            total_on_duty_nd=on_duty_nd.quantize(Decimal("0.01")),
            total_off_duty=off_duty.quantize(Decimal("0.01")),
            total_sleeper=sleeper.quantize(Decimal("0.01")),
            recap_70hr=running_on_duty.quantize(Decimal("0.01")),
        ))

    return result
