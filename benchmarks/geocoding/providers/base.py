from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GeocodeResult:
    provider: str
    query: str
    lat: float | None
    lng: float | None
    label: str
    confidence: float | None  # 0.0–1.0 where available
    latency_ms: float
    success: bool
    error: str | None = None
    raw: dict = field(default_factory=dict)

    def distance_error_km(self, expected_lat: float, expected_lng: float) -> float | None:
        """Great-circle distance in km between returned coord and expected coord."""
        if self.lat is None or self.lng is None:
            return None
        from math import radians, sin, cos, sqrt, atan2
        R = 6371
        dlat = radians(expected_lat - self.lat)
        dlng = radians(expected_lng - self.lng)
        a = sin(dlat / 2) ** 2 + cos(radians(self.lat)) * cos(radians(expected_lat)) * sin(dlng / 2) ** 2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))


class BaseGeocodeProvider(ABC):
    name: str

    @abstractmethod
    def geocode(self, query: str) -> GeocodeResult:
        """Geocode a text query. Must measure latency internally."""
        ...

    def supports_truck_routing(self) -> bool:
        return False
