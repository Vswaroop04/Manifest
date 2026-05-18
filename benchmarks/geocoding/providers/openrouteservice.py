import time
import requests
from .base import BaseGeocodeProvider, GeocodeResult


class OpenRouteServiceGeocoder(BaseGeocodeProvider):
    name = "OpenRouteService"
    _base_url = "https://api.openrouteservice.org/geocode/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, query: str) -> GeocodeResult:
        params = {
            "api_key": self.api_key,
            "text": query,
            "size": 1,
            "boundary.country": "US",
        }
        t0 = time.perf_counter()
        try:
            resp = requests.get(self._base_url, params=params, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            if not features:
                return GeocodeResult(
                    provider=self.name, query=query, lat=None, lng=None,
                    label="", confidence=None, latency_ms=latency_ms,
                    success=False, error="No results", raw=data,
                )
            feat = features[0]
            lng, lat = feat["geometry"]["coordinates"]
            props = feat.get("properties", {})
            return GeocodeResult(
                provider=self.name,
                query=query,
                lat=lat,
                lng=lng,
                label=props.get("label", ""),
                confidence=props.get("confidence"),
                latency_ms=latency_ms,
                success=True,
                raw=feat,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - t0) * 1000
            return GeocodeResult(
                provider=self.name, query=query, lat=None, lng=None,
                label="", confidence=None, latency_ms=latency_ms,
                success=False, error=str(exc), raw={},
            )
