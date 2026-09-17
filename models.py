"""Core data types for the delivery route planner."""

from dataclasses import dataclass, field
from typing import List

# Weights are decimals read from text, so 4.5 + 3.5 + 2.0 can come out as
# 10.000000000000002. Every capacity comparison uses this tolerance so a
# trip that is exactly full is not rejected by floating point noise.
EPSILON = 1e-9


@dataclass(frozen=True)
class Delivery:
    """One delivery request from the input file."""

    id: str
    area: str       # display name, e.g. "Nasr City"
    area_key: str   # normalised grouping key, e.g. "nasr city"
    priority: int   # lower number = more urgent
    weight: float   # kg
    seq: int        # position in the input file; stable tie-breaker

    def __str__(self) -> str:
        return f"#{self.id} {self.area} (P{self.priority}, {self.weight:g} kg)"


@dataclass
class Trip:
    """One vehicle run. Holds deliveries and never exceeds its capacity."""

    capacity: float
    deliveries: List[Delivery] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        return sum(d.weight for d in self.deliveries)

    @property
    def remaining(self) -> float:
        return self.capacity - self.total_weight

    @property
    def areas(self) -> List[str]:
        """Display names of the areas in this trip, in first-seen order."""
        seen = {}
        for d in self.deliveries:
            seen.setdefault(d.area_key, d.area)
        return list(seen.values())

    @property
    def is_mixed(self) -> bool:
        return len(self.areas) > 1

    @property
    def top_priority(self) -> int:
        """Priority of the most urgent package on board."""
        return min(d.priority for d in self.deliveries)

    @property
    def utilisation(self) -> float:
        return self.total_weight / self.capacity if self.capacity else 0.0

    def fits(self, delivery: Delivery) -> bool:
        return delivery.weight <= self.remaining + EPSILON

    def add(self, delivery: Delivery) -> None:
        if not self.fits(delivery):
            raise ValueError(
                f"delivery {delivery.id} ({delivery.weight} kg) does not fit in "
                f"a trip with {self.remaining:.2f} kg left"
            )
        self.deliveries.append(delivery)


@dataclass(frozen=True)
class Rejected:
    """A row that could not become a valid delivery, plus the reason."""

    identifier: str
    reason: str