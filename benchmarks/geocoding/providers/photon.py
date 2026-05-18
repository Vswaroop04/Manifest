import time
import requests
from .base import BaseGeocodeProvider, GeocodeResult

# Photon by Komoot — completely free, no key, powered by OSM
# Fair use: don't hammer it. 1 req/sec is safe.
_USER_AGENT = "spotter-labs-benchmark/1.0 (benchmark only)"


class PhotonGeocoder(BaseGeocodeProvider):
    name = "Photon (Komoot)"
    _base_url = "https://photon.komoot.io/api/"

    def geocode(self, query: str) -> GeocodeResult:
        params = {
            "q": query,
            "limit": 1,
            "lang": "en",
            "bbox": "-125,24,-66,50",  # continental US bounding box
        }
        headers = {"User-Agent": _USER_AGENT}
        t0 = time.perf_counter()
        try:
            resp = requests.get(self._base_url, params=params, headers=headers, timeout=10)
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
            label_parts = filter(None, [
                props.get("name"), props.get("city"),
                props.get("state"), props.get("country"),
            ])
            return GeocodeResult(
                provider=self.name,
                query=query,
                lat=lat,
                lng=lng,
                label=", ".join(label_parts),
                confidence=None,  # Photon doesn't return confidence scores
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
