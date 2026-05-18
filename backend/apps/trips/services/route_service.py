import logging
from dataclasses import dataclass
from decimal import Decimal

import polyline
import requests
from django.conf import settings

logger = logging.getLogger("app")

_ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv"
_OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
_TIMEOUT = 10
_METERS_PER_MILE = Decimal("1609.344")


class RoutingError(Exception):
    pass


@dataclass
class RouteResult:
    geometry: list[list[float]]
    total_miles: Decimal
    total_drive_secs: int
    used_fallback: bool


def get_route(waypoints: list[tuple[float, float]]) -> RouteResult:
    """
    Fetch a truck-aware route for the given waypoints (lat, lng).
    Tries ORS HGV first, falls back to OSRM on 429 or 5xx.
    """
    try:
        return _ors_route(waypoints)
    except RoutingError as exc:
        logger.warning(
            "ORS routing failed, falling back to OSRM — truck restrictions not applied",
            extra={"error": str(exc)},
        )
        return _osrm_route(waypoints)


def _ors_route(waypoints: list[tuple[float, float]]) -> RouteResult:
    coords = [[lng, lat] for lat, lng in waypoints]
    try:
        resp = requests.post(
            _ORS_URL,
            json={"coordinates": coords},
            headers={
                "Authorization": settings.ORS_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT,
        )
    except requests.Timeout:
        raise RoutingError("ORS request timed out")

    if resp.status_code in (429, 500, 502, 503, 504):
        raise RoutingError(f"ORS returned {resp.status_code}")

    if not resp.ok:
        raise RoutingError(f"ORS error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    route = data["routes"][0]
    summary = route["summary"]

    total_miles = Decimal(str(summary["distance"])) / _METERS_PER_MILE
    total_drive_secs = int(summary["duration"])
    decoded = polyline.decode(route["geometry"])
    geometry = [[lat, lng] for lat, lng in decoded]

    return RouteResult(
        geometry=geometry,
        total_miles=total_miles.quantize(Decimal("0.1")),
        total_drive_secs=total_drive_secs,
        used_fallback=False,
    )


def _osrm_route(waypoints: list[tuple[float, float]]) -> RouteResult:
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in waypoints)
    try:
        resp = requests.get(
            f"{_OSRM_URL}/{coord_str}",
            params={"overview": "full", "geometries": "polyline"},
            timeout=_TIMEOUT,
        )
    except requests.Timeout:
        raise RoutingError("OSRM request timed out")

    if not resp.ok:
        raise RoutingError(f"OSRM error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    if data.get("code") != "Ok":
        raise RoutingError(f"OSRM returned code: {data.get('code')}")

    route = data["routes"][0]
    total_miles = Decimal(str(route["distance"])) / _METERS_PER_MILE
    total_drive_secs = int(route["duration"])
    decoded = polyline.decode(route["geometry"])
    geometry = [[lat, lng] for lat, lng in decoded]

    return RouteResult(
        geometry=geometry,
        total_miles=total_miles.quantize(Decimal("0.1")),
        total_drive_secs=total_drive_secs,
        used_fallback=True,
    )
