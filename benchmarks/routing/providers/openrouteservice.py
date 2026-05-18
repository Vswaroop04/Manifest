import time
import requests
from .base import BaseRoutingProvider, RouteResult

_PROFILES = {
    True: "driving-hgv",   # Heavy Goods Vehicle — truck-aware routing
    False: "driving-car",
}


class OpenRouteServiceRouter(BaseRoutingProvider):
    name = "OpenRouteService"
    supports_truck = True
    _base_url = "https://api.openrouteservice.org/v2/directions/{profile}"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def route(self, coordinates: list[list[float]], truck_profile: bool = True) -> RouteResult:
        profile = _PROFILES[truck_profile]
        url = self._base_url.format(profile=profile)
        payload = {
            "coordinates": coordinates,
            "units": "mi",
            "instructions": True,
            "geometry": True,
        }
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        t0 = time.perf_counter()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            latency_ms = (time.perf_counter() - t0) * 1000
            resp.raise_for_status()
            data = resp.json()
            route = data["routes"][0]
            summary = route["summary"]
            steps = route.get("segments", [{}])[0].get("steps", [])
            return RouteResult(
                provider=self.name,
                label=f"{self.name} ({'HGV' if truck_profile else 'car'})",
                distance_miles=summary["distance"],
                duration_hours=summary["duration"] / 3600,
                has_geometry=bool(route.get("geometry")),
                has_turn_by_turn=len(steps) > 0,
                truck_profile=truck_profile,
                latency_ms=latency_ms,
                success=True,
                waypoint_count=len(coordinates),
                raw=route,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - t0) * 1000
            return RouteResult(
                provider=self.name,
                label=self.name,
                distance_miles=None,
                duration_hours=None,
                has_geometry=False,
                has_turn_by_turn=False,
                truck_profile=truck_profile,
                latency_ms=latency_ms,
                success=False,
                error=str(exc),
            )
