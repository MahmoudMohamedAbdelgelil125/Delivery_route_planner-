"""The planning algorithm.

The rules interact like this:

  * "group the same area together" is a grouping rule -> it decides WHICH
    deliveries can share a trip.
  * "lower priority number first" is an ordering rule -> it decides WHEN a
    trip goes out, and which package claims space first.

So the plan is built in three passes:

  1. Split the deliveries by area.
  2. Pack each area with First-Fit Decreasing (most urgent first, and within
     the same priority the heaviest first).
  3. Sort the finished trips so the most urgent ones are dispatched first.

An optional fourth pass merges very empty trips from different areas, which is
the extension described in the README.
"""

from typing import Dict, List

from models import EPSILON, Delivery, Trip


def plan_trips(
    deliveries: List[Delivery],
    capacity: float = 10.0,
    merge_leftovers: bool = False,
    merge_threshold: float = 0.5,
) -> List[Trip]:
    """Turn a list of deliveries into an ordered list of trips."""
    if not deliveries:
        return []

    trips: List[Trip] = []
    for group in _group_by_area(deliveries).values():
        trips.extend(_pack_area(group, capacity))

    if merge_leftovers:
        trips = _merge_underfilled(trips, capacity, merge_threshold)

    return _sort_for_dispatch(trips)


def _group_by_area(deliveries: List[Delivery]) -> Dict[str, List[Delivery]]:
    """Bucket deliveries by their normalised area key (insertion ordered)."""
    groups: Dict[str, List[Delivery]] = {}
    for delivery in deliveries:
        groups.setdefault(delivery.area_key, []).append(delivery)
    return groups


def _pack_area(group: List[Delivery], capacity: float) -> List[Trip]:
    """First-Fit Decreasing packing for the deliveries of one area.

    Ordering key:
      priority ascending  -> urgent packages claim space first
      weight descending   -> big items go in while trips are still empty,
                             small items later fill the gaps they leave
      input order         -> deterministic output for identical rows
    """
    ordered = sorted(group, key=lambda d: (d.priority, -d.weight, d.seq))

    trips: List[Trip] = []
    for delivery in ordered:
        target = next((trip for trip in trips if trip.fits(delivery)), None)
        if target is None:
            target = Trip(capacity=capacity)
            trips.append(target)
        target.add(delivery)
    return trips


def _merge_underfilled(trips: List[Trip], capacity: float, threshold: float) -> List[Trip]:
    """Combine nearly empty trips from different areas when they fit together.

    Only trips below `threshold` utilisation are candidates, so a well filled
    single-area trip is never broken up. Each round merges the single best
    pair (the one that ends up fullest) and then re-evaluates, because a merged
    trip may no longer be under the threshold.
    """
    remaining = list(trips)

    while True:
        candidates = [t for t in remaining if t.utilisation < threshold]
        best = None

        for index, first in enumerate(candidates):
            for second in candidates[index + 1:]:
                combined = first.total_weight + second.total_weight
                if combined > capacity + EPSILON:
                    continue
                if best is None or combined > best[0]:
                    best = (combined, first, second)

        if best is None:
            return remaining

        _, keep, absorb = best
        keep.deliveries.extend(absorb.deliveries)
        keep.deliveries.sort(key=lambda d: (d.priority, -d.weight, d.seq))
        remaining.remove(absorb)


def _sort_for_dispatch(trips: List[Trip]) -> List[Trip]:
    """Most urgent trip first; fuller trips first on a tie; then by area name."""
    return sorted(
        trips,
        key=lambda t: (t.top_priority, -t.total_weight, t.areas[0]),
    )
