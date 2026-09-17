"""Command line entry point for the delivery route planner.

Examples:
    python main.py data/deliveries.csv
    python main.py data/deliveries.json --capacity 12
    python main.py data/edge_cases.csv --merge-leftovers
    python main.py data/deliveries.csv --json
"""

import argparse
import json
import sys

from loader import load_deliveries
from planner import plan_trips
from reporting import format_report, to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan delivery trips from a file.")
    parser.add_argument("input", help="path to a .csv or .json file of deliveries")
    parser.add_argument(
        "--capacity", type=float, default=10.0,
        help="vehicle capacity in kg (default: 10)",
    )
    parser.add_argument(
        "--merge-leftovers", action="store_true",
        help="combine nearly empty trips from different areas (extension)",
    )
    parser.add_argument(
        "--merge-threshold", type=float, default=0.5,
        help="only merge trips filled below this fraction (default: 0.5)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json",
        help="print the plan as JSON instead of a text report",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.capacity <= 0:
        print("error: --capacity must be greater than zero", file=sys.stderr)
        return 2

    try:
        deliveries, rejected = load_deliveries(args.input, args.capacity)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    trips = plan_trips(
        deliveries,
        capacity=args.capacity,
        merge_leftovers=args.merge_leftovers,
        merge_threshold=args.merge_threshold,
    )

    if args.as_json:
        print(json.dumps(to_dict(trips, rejected, args.capacity), indent=2))
    else:
        print(format_report(trips, rejected, args.capacity))

    return 0


if __name__ == "__main__":
    sys.exit(main())