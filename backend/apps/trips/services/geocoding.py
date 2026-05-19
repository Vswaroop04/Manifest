import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests
from django.conf import settings

from apps.trips.constants import GEOCODING_CACHE_TTL, HTTP_HEADERS, HTTP_TIMEOUT
from apps.trips.exceptions import GeocodingError
from apps.trips.utils.cache import cached_or_calculate

logger = logging.getLogger("app")


class Geocoder(ABC):
    name: str

    @abstractmethod
    def geocode(self, query: str) -> Optional[tuple[float, float]]: ...


# HOS (FMCSA Part 395) only applies to US-domiciled drivers — geocoding
# is restricted to US so users can't pick foreign addresses we can't plan for.
US_BBOX = "-125.0,24.0,-66.0,49.5"  # continental US lng/lat box for Photon
US_COUNTRYCODES = "us"  # Nominatim ISO country filter


class PhotonGeocoder(Geocoder):
    name = "photon"

    def geocode(self, query: str) -> Optional[tuple[float, float]]:
        try:
            resp = requests.get(
                settings.PHOTON_URL,
                params={"q": query, "limit": 5, "bbox": US_BBOX},
                headers=HTTP_HEADERS,
                timeout=HTTP_TIMEOUT,
            )
            resp.raise_for_status()
            features = [
                f
                for f in resp.json().get("features", [])
                if f.get("properties", {}).get("countrycode") == "US"
            ]
            if not features:
                return None
            coords = features[0]["geometry"]["coordinates"]
            return float(coords[1]), float(coords[0])
        except Exception as exc:
            logger.warning(
                "Photon geocoding failed", extra={"query": query, "error": str(exc)}
            )
            return None


class NominatimGeocoder(Geocoder):
    name = "nominatim"

    def geocode(self, query: str) -> Optional[tuple[float, float]]:
        try:
            resp = requests.get(
                settings.NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "json",
                    "limit": 5,
                    "countrycodes": US_COUNTRYCODES,
                },
                headers=HTTP_HEADERS,
                timeout=HTTP_TIMEOUT,
            )
            resp.raise_for_status()
            results = resp.json()
            if not results:
                return None
            return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception as exc:
            logger.warning(
                "Nominatim geocoding failed", extra={"query": query, "error": str(exc)}
            )
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
            ttl=GEOCODING_CACHE_TTL,
        )

    def _geocode(self, query: str) -> Optional[tuple[float, float]]:
        result = self.primary.geocode(query)
        if result is not None:
            return result
        logger.warning(
            "Primary geocoder failed, falling back",
            extra={
                "query": query,
                "primary": self.primary.name,
                "fallback": self.fallback.name,
            },
        )
        result = self.fallback.geocode(query)
        if result is None:
            raise GeocodingError(f"All geocoders failed for query: {query!r}")
        return result

    def suggest(self, query: str) -> list[dict[str, object]]:
        try:
            resp = requests.get(
                settings.PHOTON_URL,
                params={"q": query, "limit": 8, "bbox": US_BBOX},
                headers=HTTP_HEADERS,
                timeout=HTTP_TIMEOUT,
            )
            resp.raise_for_status()
            features = [
                f
                for f in resp.json().get("features", [])
                if f.get("properties", {}).get("countrycode") == "US"
            ]
            suggestions = []
            for f in features[:5]:
                props = f.get("properties", {})
                coords = f["geometry"]["coordinates"]
                parts = [props.get("name"), props.get("city"), props.get("state")]
                label = ", ".join(p for p in parts if p)
                suggestions.append(
                    {"label": label, "lat": float(coords[1]), "lng": float(coords[0])}
                )
            return suggestions
        except Exception as exc:
            logger.warning("Suggest failed", extra={"query": query, "error": str(exc)})
            return []


def make_geocoder() -> MultiServiceGeocoder:
    return MultiServiceGeocoder(primary=PhotonGeocoder(), fallback=NominatimGeocoder())
