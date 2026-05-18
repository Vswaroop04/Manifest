from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RouteResult:
    provider: str
    label: str
    distance_miles: float | None
    duration_hours: float | None
    has_geometry: bool
    has_turn_by_turn: bool
    truck_profile: bool       # did we use a truck/HGV routing profile?
    latency_ms: float
    success: bool
    error: str | None = None
    waypoint_count: int = 2
    raw: dict = field(default_factory=dict)

    def distance_error_pct(self, expected_miles: float) -> float | None:
        if self.distance_miles is None:
            return None
        return abs(self.distance_miles - expected_miles) / expected_miles * 100


class BaseRoutingProvider(ABC):
    name: str
    supports_truck: bool = False

    @abstractmethod
    def route(
        self,
        coordinates: list[list[float]],  # list of [lng, lat]
        truck_profile: bool = True,
    ) -> RouteResult:
        """Calculate a route. Must measure latency internally."""
        ...
