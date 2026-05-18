import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal, Optional

from apps.trips.constants import (
    FUEL_INTERVAL_MILES as _FUEL_INTERVAL,
    FUEL_STOP_DURATION as _FUEL_DURATION,
    HOS_BREAK_DURATION as _BREAK_DURATION,
    HOS_BREAK_TRIGGER as _BREAK_TRIGGER,
    HOS_CYCLE_LIMIT as _CYCLE_LIMIT,
    HOS_DRIVE_LIMIT as _DRIVE_LIMIT,
    HOS_REST_DURATION as _REST_DURATION,
    HOS_WINDOW_LIMIT as _WINDOW_LIMIT,
    STOP_DURATION as _STOP_DURATION,
)

logger = logging.getLogger("app")

@dataclass
class Waypoint:
    label: str
    mile_marker: Decimal
    event_type: Literal["pickup", "dropoff"]
    coords: Optional[tuple[float, float]] = None


@dataclass
class TripEventData:
    event_type: str  # matches EventType choices in models.py
    start_time: datetime
    end_time: Optional[datetime]
    location_label: str
    coords: Optional[tuple[float, float]]
    mile_marker: Decimal
    metadata: dict = field(default_factory=dict)


@dataclass
class _State:
    current_time: datetime
    current_mile: Decimal
    shift_start: datetime
    drive_in_shift: timedelta
    drive_for_break: timedelta
    cycle_hrs: Decimal


def _td_to_dec_hrs(td: timedelta) -> Decimal:
    return Decimal(str(td.total_seconds() / 3600))


def _build_mandatory_stops(
    waypoints: list[Waypoint],
    total_miles: Decimal,
) -> list[tuple[Decimal, str, Optional[Waypoint]]]:
    stops: list[tuple[Decimal, str, Optional[Waypoint]]] = [
        (w.mile_marker, "waypoint", w) for w in waypoints
    ]
    marker = _FUEL_INTERVAL
    while marker < total_miles:
        stops.append((marker, "fuel", None))
        marker += _FUEL_INTERVAL
    return sorted(stops, key=lambda x: x[0])


def _append_stop(
    events: list[TripEventData],
    state: _State,
    stop_kind: str,
    waypoint: Optional[Waypoint],
) -> None:
    if stop_kind == "fuel":
        duration = _FUEL_DURATION
        events.append(TripEventData(
            event_type="fuel",
            start_time=state.current_time,
            end_time=state.current_time + duration,
            location_label="Fuel Stop",
            coords=None,
            mile_marker=state.current_mile,
            metadata={"trigger": "1000mi_rule"},
        ))
        state.current_time += duration
        state.cycle_hrs += _td_to_dec_hrs(duration)
    else:
        assert waypoint is not None
        duration = _STOP_DURATION
        events.append(TripEventData(
            event_type=waypoint.event_type,
            start_time=state.current_time,
            end_time=state.current_time + duration,
            location_label=waypoint.label,
            coords=waypoint.coords,
            mile_marker=state.current_mile,
            metadata={},
        ))
        state.current_time += duration
        state.cycle_hrs += _td_to_dec_hrs(duration)


def _append_break(events: list[TripEventData], state: _State) -> None:
    events.append(TripEventData(
        event_type="break",
        start_time=state.current_time,
        end_time=state.current_time + _BREAK_DURATION,
        location_label="",
        coords=None,
        mile_marker=state.current_mile,
        metadata={"trigger": "8hr_rule"},
    ))
    state.current_time += _BREAK_DURATION
    state.drive_for_break = timedelta()


def _append_rest(events: list[TripEventData], state: _State, trigger: str) -> None:
    events.append(TripEventData(
        event_type="rest",
        start_time=state.current_time,
        end_time=state.current_time + _REST_DURATION,
        location_label="",
        coords=None,
        mile_marker=state.current_mile,
        metadata={"trigger": trigger},
    ))
    state.current_time += _REST_DURATION
    state.shift_start = state.current_time
    state.drive_in_shift = timedelta()
    state.drive_for_break = timedelta()


def _append_drive_end(
    events: list[TripEventData],
    state: _State,
    drive_time: timedelta,
    miles: Decimal,
) -> None:
    events.append(TripEventData(
        event_type="drive_end",
        start_time=state.current_time + drive_time,
        end_time=state.current_time + drive_time,
        location_label="",
        coords=None,
        mile_marker=state.current_mile + miles,
    ))
    state.current_time += drive_time
    state.drive_in_shift += drive_time
    state.drive_for_break += drive_time
    state.cycle_hrs += _td_to_dec_hrs(drive_time)
    state.current_mile += miles


def _day_start(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _day_end(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def calculate(
    departure_time: datetime,
    cycle_hours_used: Decimal,
    total_miles: Decimal,
    total_drive_secs: int,
    waypoints: list[Waypoint],
) -> list[TripEventData]:
    if total_miles <= 0:
        return []

    avg_speed = total_miles / Decimal(str(total_drive_secs / 3600))

    state = _State(
        current_time=departure_time,
        current_mile=Decimal("0"),
        shift_start=departure_time,
        drive_in_shift=timedelta(),
        drive_for_break=timedelta(),
        cycle_hrs=cycle_hours_used,
    )

    mandatory = _build_mandatory_stops(waypoints, total_miles)
    stop_idx = 0
    events: list[TripEventData] = []

    # Off-duty from midnight to departure if driver doesn't start at midnight
    midnight = _day_start(departure_time)
    if departure_time > midnight:
        events.append(TripEventData(
            event_type="off_duty",
            start_time=midnight,
            end_time=departure_time,
            location_label="",
            coords=None,
            mile_marker=Decimal("0"),
            metadata={"trigger": "pre_departure"},
        ))

    events.append(TripEventData(
        event_type="drive_start",
        start_time=state.current_time,
        end_time=None,
        location_label="",
        coords=None,
        mile_marker=state.current_mile,
    ))

    while state.current_mile < total_miles:
        remaining = total_miles - state.current_mile
        window_elapsed = state.current_time - state.shift_start

        drive_avail = _DRIVE_LIMIT - state.drive_in_shift
        window_avail = _WINDOW_LIMIT - window_elapsed
        break_avail = _BREAK_TRIGGER - state.drive_for_break
        cycle_avail_hrs = _CYCLE_LIMIT - state.cycle_hrs

        # Convert time limits to miles
        max_by_drive = _td_to_dec_hrs(drive_avail) * avg_speed
        max_by_window = _td_to_dec_hrs(window_avail) * avg_speed
        max_by_break = _td_to_dec_hrs(break_avail) * avg_speed
        max_by_cycle = cycle_avail_hrs * avg_speed

        max_drive_miles = min(max_by_drive, max_by_window, max_by_break, max_by_cycle, remaining)

        # Skip stops already passed
        while stop_idx < len(mandatory) and mandatory[stop_idx][0] <= state.current_mile:
            stop_idx += 1

        # Check if next stop falls within driveable range
        next_stop: Optional[tuple[Decimal, str, Optional[Waypoint]]] = None
        if stop_idx < len(mandatory):
            candidate = mandatory[stop_idx]
            if candidate[0] <= state.current_mile + max_drive_miles:
                next_stop = candidate
                stop_idx += 1

        if next_stop is not None:
            stop_mile, stop_kind, waypoint = next_stop
            drive_miles = stop_mile - state.current_mile
            drive_time = timedelta(hours=float(drive_miles / avg_speed))

            _append_drive_end(events, state, drive_time, drive_miles)

            # Check if break is due before processing stop
            if state.drive_for_break >= _BREAK_TRIGGER:
                _append_break(events, state)

            _append_stop(events, state, stop_kind, waypoint)

            if state.current_mile < total_miles:
                events.append(TripEventData(
                    event_type="drive_start",
                    start_time=state.current_time,
                    end_time=None,
                    location_label="",
                    coords=None,
                    mile_marker=state.current_mile,
                ))
        else:
            # A HOS rule fires — drive to the limit then stop
            drive_time = timedelta(hours=float(max_drive_miles / avg_speed))
            _append_drive_end(events, state, drive_time, max_drive_miles)

            if state.current_mile >= total_miles:
                break

            window_elapsed = state.current_time - state.shift_start

            if state.drive_for_break >= _BREAK_TRIGGER and state.drive_in_shift < _DRIVE_LIMIT and window_elapsed < _WINDOW_LIMIT:
                _append_break(events, state)
            elif state.drive_in_shift >= _DRIVE_LIMIT:
                _append_rest(events, state, "11hr_limit")
            elif window_elapsed >= _WINDOW_LIMIT:
                _append_rest(events, state, "14hr_window")
            else:
                # Cycle limit
                _append_rest(events, state, "70hr_cycle")

            if state.current_mile < total_miles:
                events.append(TripEventData(
                    event_type="drive_start",
                    start_time=state.current_time,
                    end_time=None,
                    location_label="",
                    coords=None,
                    mile_marker=state.current_mile,
                ))

    # Off-duty from arrival to midnight if trip ends before end of day
    arrival_time = state.current_time
    eod = _day_end(arrival_time)
    if arrival_time < eod:
        events.append(TripEventData(
            event_type="off_duty",
            start_time=arrival_time,
            end_time=eod,
            location_label="",
            coords=None,
            mile_marker=total_miles,
            metadata={"trigger": "post_arrival"},
        ))

    return events
