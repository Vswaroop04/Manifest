import time
import requests
from .base import BaseGeocodeProvider, GeocodeResult

# LocationIQ structured API — separate fields prevent the freeform parsing failure
# that tanks accuracy on ambiguous or international addresses.
# Free tier: 5,000 requests/day, 2 req/sec.
_BASE_URL = "https://us1.locationiq.com/v1/search"


class LocationIQStructuredGeocoder(BaseGeocodeProvider):
    """
    Uses LocationIQ's structured endpoint (street + city + state + postalcode)
    instead of a single freeform string.  Structured input avoids the parser
    mis-classifying tokens (e.g. treating a zip code as a city name) which is
    the main cause of multi-km errors in freeform geocoding.
    """
    name = "LocationIQ (structured)"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, query: str) -> GeocodeResult:
        """
        Parse a best-effort structured form from a freeform query string so we
        can compare apples-to-apples with other providers on the same test cases.
        Production use would receive pre-structured fields from the UI form.
        """
        params = self._parse_query(query)
        params.update({
            "key": self.api_key,
            "format": "json",
            "limit": 1,
            "countrycodes": "us",
            "addressdetails": 1,
            "normalizecity": 1,
        })
        t0 = time.perf_counter()
        try:
            resp = requests.get(_BASE_URL, params=params, timeout=10)
            latency_ms = (time.perf_counter() - t0) * 1000
            resp.raise_for_status()
            data = resp.json()

            if not data or isinstance(data, dict) and "error" in data:
                error = data.get("error", "No results") if isinstance(data, dict) else "No results"
                return GeocodeResult(
                    provider=self.name, query=query, lat=None, lng=None,
                    label="", confidence=None, latency_ms=latency_ms,
                    success=False, error=error, raw={},
                )

            hit = data[0]
            return GeocodeResult(
                provider=self.name,
                query=query,
                lat=float(hit["lat"]),
                lng=float(hit["lon"]),
                label=hit.get("display_name", ""),
                # LocationIQ returns importance similar to Nominatim
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

    @staticmethod
    def _parse_query(query: str) -> dict:
        """
        Heuristically split a freeform query into structured fields.
        Handles the common patterns in GEOCODING_TEST_CASES:
          - "City, ST"
          - "Street, City, ST zip"
          - "zip only"
        """
        parts = [p.strip() for p in query.split(",")]

        # Zip code only
        if len(parts) == 1 and parts[0].isdigit() and len(parts[0]) == 5:
            return {"postalcode": parts[0], "country": "US"}

        # "City, ST" or "City ST"
        if len(parts) == 2:
            city, state_part = parts
            state = state_part.strip().split()[0]  # handle "TX 75201"
            return {"city": city, "state": state, "country": "US"}

        # "Street number Name, City, ST zip" — 3+ parts
        if len(parts) >= 3:
            street = parts[0]
            city = parts[1]
            state_zip = parts[2].strip().split()
            state = state_zip[0] if state_zip else ""
            postal = state_zip[1] if len(state_zip) > 1 else ""
            result = {"street": street, "city": city, "state": state, "country": "US"}
            if postal:
                result["postalcode"] = postal
            return result

        # Fallback: treat entire query as city
        return {"city": query, "country": "US"}
