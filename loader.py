
import csv
import json
import os
from typing import Any, Dict, List, Tuple

from models import EPSILION, Delivery, Rejected

REQUIRED_FIELDS = ("id", "area", "priority", "weight")


def load_deliveries(path: str, capacity: float) -> Tuple[List[Delivery], List[Rejected]]:
    """Read `path` and return (valid deliveries, rejected rows)."""
    rows = _read_rows(path)

    deliveries: List[Delivery] = []
    rejected: List[Rejected] = []
    seen_ids = set()
    # area_key -> the first spelling seen in the file, used for display so that
    # "nasr  city" is reported under "Nasr City" if that came first.
    area_names: Dict[str, str] = {}

    for seq, raw in enumerate(rows):
        delivery, reason = _parse_row(raw, seq, capacity, seen_ids, area_names)
        if delivery is None:
            rejected.append(Rejected(_identify(raw, seq), reason))
        else:
            seen_ids.add(delivery.id)
            deliveries.append(delivery)

    return deliveries, rejected


def _read_rows(path: str) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"input file not found: {path}")

    extension = os.path.splitext(path)[1].lower()

    if extension == ".json":
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):           # allow {"deliveries": [...]}
            data = data.get("deliveries", [])
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list of delivery objects")
        return data

    # Default to CSV.
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []                        # completely empty file
        missing = [f for f in REQUIRED_FIELDS if f not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
        return [row for row in reader if any((value or "").strip() for value in row.values())]


def _parse_row(raw, seq, capacity, seen_ids, area_names):
    """Return (Delivery, None) on success or (None, reason) on failure."""
    if not isinstance(raw, dict):
        return None, "row is not a record with named fields"

    identifier = str(raw.get("id", "")).strip()
    if not identifier:
        return None, "missing id"
    if identifier in seen_ids:
        return None, f"duplicate id '{identifier}' (first occurrence kept)"

    priority = _to_int(raw.get("priority"))
    if priority is None:
        return None, f"priority '{raw.get('priority')}' is not a whole number"

    weight = _to_float(raw.get("weight"))
    if weight is None:
        return None, f"weight '{raw.get('weight')}' is not a number"
    if weight <= 0:
        return None, f"weight {weight:g} kg must be greater than zero"
    if weight > capacity + EPSILION:
        return None, f"weight {weight:g} kg exceeds vehicle capacity {capacity:g} kg"

    area, area_key = _normalise_area(raw.get("area"))
    area = area_names.setdefault(area_key, area)

    return Delivery(identifier, area, area_key, priority, weight, seq), None


def _normalise_area(value):
    """Collapse whitespace and casefold so 'nasr  city' groups with 'Nasr City'."""
    cleaned = " ".join(str(value or "").split())
    if not cleaned:
        return "Unspecified", "unspecified"
    return cleaned, cleaned.casefold()


def _to_int(value):
    number = _to_float(value)
    if number is None or number != int(number):
        return None
    return int(number)


def _to_float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _identify(raw, seq):
    if isinstance(raw, dict):
        identifier = str(raw.get("id", "")).strip()
        if identifier:
            return identifier
    return f"row {seq + 1}"
