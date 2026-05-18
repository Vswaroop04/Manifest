import time
import requests
from .base import BaseGeocodeProvider, GeocodeResult

# Nominatim usage policy: max 1 req/sec, must set a real User-Agent
_USER_AGENT = "spotter-labs-benchmark/1.0 (benchmark only)"


class NominatimGeocoder(BaseGeocodeProvider):
    name = "Nominatim (OSM)"
    _base_url = "https://nominatim.openstreetmap.org/search"

    def geocode(self, query: str) -> GeocodeResult:
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "us",
            "addressdetails": 1,
        }
        headers = {"User-Agent": _USER_AGENT}
        t0 = time.perf_counter()
        try:
            resp = requests.get(self._base_url, params=params, headers=headers, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return GeocodeResult(
                    provider=self.name, query=query, lat=None, lng=None,
                    label="", confidence=None, latency_ms=latency_ms,
                    success=False, error="No results", raw={},
                )
            hit = data[0]
            # Nominatim returns importance (0.0–1.0) as a proxy for confidence
            return GeocodeResult(
                provider=self.name,
                query=query,
                lat=float(hit["lat"]),
                lng=float(hit["lon"]),
                label=hit.get("display_name", ""),
                confidence=float(hit.get("importance", 0)),
                latency_ms=latency_ms,
                success=True,
                raw=hit,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - t0) * 1000
            return GeocodeResult(
                provider=self.name, query=query, lat=None, lng=None,
                label="", confidence=None, latency_ms=latency_ms,
                success=False, error=str(exc), raw={},
            )
