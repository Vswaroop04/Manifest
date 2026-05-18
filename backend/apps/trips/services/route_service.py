import logging
from dataclasses import dataclass
from decimal import Decimal

import polyline
import requests
from django.conf import settings

from apps.trips.constants import HTTP_TIMEOUT, METERS_PER_MILE
from apps.trips.exceptions import RoutingError

logger = logging.getLogger("app")


@dataclass
class RouteResult:
    geometry: list[list[float]]
    total_miles: Decimal
    total_drive_secs: int
    used_fallback: bool


def get_route(waypoints: list[tuple[float, float]]) -> RouteResult:
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
            settings.ORS_URL,
            json={"coordinates": coords},
            headers={
                "Authorization": settings.ORS_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=HTTP_TIMEOUT,
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
    total_miles = (Decimal(str(summary["distance"])) / METERS_PER_MILE).quantize(Decimal("0.1"))
    geometry = [[lat, lng] for lat, lng in polyline.decode(route["geometry"])]

    return RouteResult(
        geometry=geometry,
        total_miles=total_miles,
        total_drive_secs=int(summary["duration"]),
        used_fallback=False,
    )


def _osrm_route(waypoints: list[tuple[float, float]]) -> RouteResult:
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in waypoints)
    try:
        resp = requests.get(
            f"{settings.OSRM_URL}/{coord_str}",
            params={"overview": "full", "geometries": "polyline"},
            timeout=HTTP_TIMEOUT,
        )
    except requests.Timeout:
        raise RoutingError("OSRM request timed out")

    if not resp.ok:
        raise RoutingError(f"OSRM error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    if data.get("code") != "Ok":
        raise RoutingError(f"OSRM returned code: {data.get('code')}")

    route = data["routes"][0]
    total_miles = (Decimal(str(route["distance"])) / METERS_PER_MILE).quantize(Decimal("0.1"))
    geometry = [[lat, lng] for lat, lng in polyline.decode(route["geometry"])]

    return RouteResult(
        geometry=geometry,
        total_miles=total_miles,
        total_drive_secs=int(route["duration"]),
        used_fallback=True,
    )
