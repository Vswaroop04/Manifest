import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests

from apps.trips.utils.cache import cached_or_calculate

logger = logging.getLogger("app")

_PHOTON_URL = "https://photon.komoot.io/api/"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_TIMEOUT = 10
_CACHE_TTL = 60 * 60 * 24  # 24 hours
_HEADERS = {"User-Agent": "ELD-TripPlanner/1.0"}


class GeocodingError(Exception):
    pass


class Geocoder(ABC):
    name: str

    @abstractmethod
    def geocode(self, query: str) -> Optional[tuple[float, float]]:
        ...


class PhotonGeocoder(Geocoder):
    name = "photon"

    def geocode(self, query: str) -> Optional[tuple[float, float]]:
        try:
            resp = requests.get(
                _PHOTON_URL,
                params={"q": query, "limit": 5},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            features = resp.json().get("features", [])
            if not features:
                return None
            coords = features[0]["geometry"]["coordinates"]
            return float(coords[1]), float(coords[0])
        except Exception as exc:
            logger.warning("Photon geocoding failed", extra={"query": query, "error": str(exc)})
            return None


class NominatimGeocoder(Geocoder):
    name = "nominatim"

    def geocode(self, query: str) -> Optional[tuple[float, float]]:
        try:
            resp = requests.get(
                _NOMINATIM_URL,
                params={"q": query, "format": "json", "limit": 5},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            results = resp.json()
            if not results:
                return None
            return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception as exc:
            logger.warning("Nominatim geocoding failed", extra={"query": query, "error": str(exc)})
            return None


class MultiServiceGeocoder(Geocoder):
    name = "multi"

    def __init__(self, primary: Geocoder, fallback: Geocoder) -> None:
        self.primary = primary
        self.fallback = fallback

    def geocode(self, query: str) -> Optional[tuple[float, float]]:
        return cached_or_calculate(
            f"geocode:{query.lower().strip()}",
            lambda: self._geocode(query),
            ttl=_CACHE_TTL,
        )

    def _geocode(self, query: str) -> Optional[tuple[float, float]]:
        result = self.primary.geocode(query)
        if result is not None:
            return result
        logger.warning(
            "Primary geocoder failed, falling back",
            extra={"query": query, "primary": self.primary.name, "fallback": self.fallback.name},
        )
        result = self.fallback.geocode(query)
        if result is None:
            raise GeocodingError(f"All geocoders failed for query: {query!r}")
        return result

    def suggest(self, query: str) -> list[dict[str, object]]:
        """Return up to 5 address suggestions with label and coords for autocomplete."""
        try:
            resp = requests.get(
                _PHOTON_URL,
                params={"q": query, "limit": 5},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            features = resp.json().get("features", [])
            suggestions = []
            for f in features:
                props = f.get("properties", {})
                coords = f["geometry"]["coordinates"]
                parts = [
                    props.get("name"),
                    props.get("city"),
                    props.get("state"),
                    props.get("country"),
                ]
                label = ", ".join(p for p in parts if p)
                suggestions.append({
                    "label": label,
                    "lat": float(coords[1]),
                    "lng": float(coords[0]),
                })
            return suggestions
        except Exception as exc:
            logger.warning("Suggest failed", extra={"query": query, "error": str(exc)})
            return []


def make_geocoder() -> MultiServiceGeocoder:
    return MultiServiceGeocoder(
        primary=PhotonGeocoder(),
        fallback=NominatimGeocoder(),
    )
