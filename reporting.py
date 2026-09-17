"""Turning a finished plan into human-readable text or machine-readable JSON."""

from typing import Any, Dict, List

from models import Rejected, Trip


def format_report(trips: List[Trip], rejected: List[Rejected], capacity: float) -> str:
    lines: List[str] = []
    lines.append("DELIVERY PLAN")
    lines.append(f"Vehicle capacity: {capacity:g} kg")
    lines.append("")

    if not trips:
        lines.append("No trips planned - there are no deliverable requests.")
    for number, trip in enumerate(trips, start=1):
        label = " + ".join(trip.areas)
        if trip.is_mixed:
            label += "  [mixed]"
        lines.append(
            f"Trip {number}: {label}"
            f"  |  {trip.total_weight:.1f}/{capacity:g} kg"
            f"  ({trip.utilisation:.0%})"
            f"  |  most urgent: P{trip.top_priority}"
        )
        for delivery in trip.deliveries:
            lines.append(
                f"    #{delivery.id:<4} {delivery.area:<14}"
                f" P{delivery.priority:<3} {delivery.weight:>5.1f} kg"
            )
        lines.append("")

    if rejected:
        lines.append(f"NOT PLANNED ({len(rejected)})")
        for item in rejected:
            lines.append(f"    #{item.identifier:<4} {item.reason}")
        lines.append("")

    lines.append("SUMMARY")
    delivered = sum(len(trip.deliveries) for trip in trips)
    moved = sum(trip.total_weight for trip in trips)
    average = sum(trip.utilisation for trip in trips) / len(trips) if trips else 0.0
    lines.append(f"    Trips planned      : {len(trips)}")
    lines.append(f"    Deliveries planned : {delivered}")
    lines.append(f"    Deliveries skipped : {len(rejected)}")
    lines.append(f"    Total weight moved : {moved:.1f} kg")
    lines.append(f"    Average fill rate  : {average:.0%}")

    return "\n".join(lines)


def to_dict(trips: List[Trip], rejected: List[Rejected], capacity: float) -> Dict[str, Any]:
    """Same information as the text report, for piping into another program."""
    return {
        "capacity_kg": capacity,
        "trip_count": len(trips),
        "trips": [
            {
                "trip_number": number,
                "areas": trip.areas,
                "mixed_areas": trip.is_mixed,
                "total_weight_kg": round(trip.total_weight, 3),
                "utilisation": round(trip.utilisation, 4),
                "top_priority": trip.top_priority,
                "deliveries": [
                    {
                        "id": d.id,
                        "area": d.area,
                        "priority": d.priority,
                        "weight_kg": d.weight,
                    }
                    for d in trip.deliveries
                ],
            }
            for number, trip in enumerate(trips, start=1)
        ],
        "not_planned": [
            {"id": item.identifier, "reason": item.reason} for item in rejected
        ],
    }
