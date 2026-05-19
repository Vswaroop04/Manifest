from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from apps.trips.services.hos_calculator import TripEventData


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


_STATUS_MAP: dict[str, str] = {
    "break": "off_duty",
    "rest": "sleeper",
    "off_duty": "off_duty",
    "fuel": "on_duty_nd",
    "pickup": "on_duty_nd",
    "dropoff": "on_duty_nd",
}


def _merge_consecutive(
    segs: list[tuple[str, int, int]],
) -> list[tuple[str, int, int]]:
    if not segs:
        return segs
    merged = [segs[0]]
    for status, s, e in segs[1:]:
        prev_status, prev_s, prev_e = merged[-1]
        if status == prev_status and s == prev_e:
            merged[-1] = (prev_status, prev_s, e)
        else:
            merged.append((status, s, e))
    return merged


def _add_span(
    day_map: dict[date, list[tuple[str, int, int]]],
    status: str,
    start_dt,
    end_dt,
) -> None:
    cur = start_dt
    while cur.date() <= end_dt.date():
        origin = cur.replace(hour=0, minute=0, second=0, microsecond=0)
        day_boundary = origin.replace(hour=23, minute=59, second=59, microsecond=0)
        seg_start = cur
        seg_end = min(end_dt, day_boundary)
        if seg_end > seg_start:
            s = int((seg_start - origin).total_seconds() // 60)
            e = min(int((seg_end - origin).total_seconds() // 60), 1440)
            day_map.setdefault(cur.date(), []).append((status, s, e))
        cur = origin + timedelta(days=1)


def build(events: list[TripEventData]) -> list[DayLogData]:
    if not events:
        return []

    day_map: dict[date, list[tuple[str, int, int]]] = {}

    i = 0
    while i < len(events):
        ev = events[i]

        if ev.event_type == "drive_start":
            j = i + 1
            while j < len(events) and events[j].event_type != "drive_end":
                j += 1
            if j < len(events):
                _add_span(day_map, "driving", ev.start_time, events[j].start_time)
                i = j + 1
            else:
                i += 1
        elif ev.end_time:
            status = _STATUS_MAP.get(ev.event_type)
            if status:
                _add_span(day_map, status, ev.start_time, ev.end_time)
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

        filled: list[tuple[str, int, int]] = []
        cursor = 0
        for status, s, e in raw_segs:
            if s > cursor:
                filled.append(("off_duty", cursor, s))
            filled.append((status, s, e))
            cursor = e
        if cursor < 1440:
            filled.append(("off_duty", cursor, 1440))

        filled = _merge_consecutive(filled)
        segments = [Segment(status=s, start_min=a, end_min=b) for s, a, b in filled]

        def total_hrs(status_name: str) -> Decimal:
            mins = sum(b - a for s, a, b in filled if s == status_name)
            return Decimal(str(mins)) / Decimal("60")

        driving = total_hrs("driving")
        on_duty_nd = total_hrs("on_duty_nd")
        off_duty = total_hrs("off_duty")
        sleeper = total_hrs("sleeper")

        running_on_duty += (driving + on_duty_nd).quantize(Decimal("0.01"))

        result.append(
            DayLogData(
                day_number=day_num,
                date=day_date,
                segments=segments,
                total_driving=driving.quantize(Decimal("0.01")),
                total_on_duty_nd=on_duty_nd.quantize(Decimal("0.01")),
                total_off_duty=off_duty.quantize(Decimal("0.01")),
                total_sleeper=sleeper.quantize(Decimal("0.01")),
                recap_70hr=running_on_duty.quantize(Decimal("0.01")),
            )
        )

    return result
