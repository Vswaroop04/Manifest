import time
import requests
from .base import BaseRoutingProvider, RouteResult

# OSRM public demo — car routing only, no truck profile
# Do NOT use the demo server in production; self-host instead.
_DEMO_BASE = "http://router.project-osrm.org/route/v1/driving"


class OSRMRouter(BaseRoutingProvider):
    name = "OSRM (demo)"
    supports_truck = False  # car profile only on public demo

    def route(self, coordinates: list[list[float]], truck_profile: bool = True) -> RouteResult:
        # OSRM coords format: "lng,lat;lng,lat"
        coord_str = ";".join(f"{lng},{lat}" for lng, lat in coordinates)
        url = f"{_DEMO_BASE}/{coord_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
        }
        t0 = time.perf_counter()
        try:
            resp = requests.get(url, params=params, timeout=15)
            latency_ms = (time.perf_counter() - t0) * 1000
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != "Ok":
                return RouteResult(
                    provider=self.name, label=self.name,
                    distance_miles=None, duration_hours=None,
                    has_geometry=False, has_turn_by_turn=False,
                    truck_profile=False, latency_ms=latency_ms,
                    success=False, error=data.get("message", "OSRM error"),
                )

            route = data["routes"][0]
            distance_miles = route["distance"] / 1609.34  # meters → miles
            duration_hours = route["duration"] / 3600
            steps = route.get("legs", [{}])[0].get("steps", [])

            return RouteResult(
                provider=self.name,
                label=f"{self.name} (car only — no truck profile)",
                distance_miles=distance_miles,
                duration_hours=duration_hours,
                has_geometry=bool(route.get("geometry")),
                has_turn_by_turn=len(steps) > 0,
                truck_profile=False,
                latency_ms=latency_ms,
                success=True,
                waypoint_count=len(coordinates),
                raw=route,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - t0) * 1000
            return RouteResult(
                provider=self.name, label=self.name,
                distance_miles=None, duration_hours=None,
                has_geometry=False, has_turn_by_turn=False,
                truck_profile=False, latency_ms=latency_ms,
                success=False, error=str(exc),
            )
