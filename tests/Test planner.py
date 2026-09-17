"""Tests for the planner. Run with:  python -m unittest discover tests"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader import load_deliveries          # noqa: E402
from models import Delivery, Trip           # noqa: E402
from planner import plan_trips              # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def make(identifier, area, priority, weight, seq=0):
    return Delivery(identifier, area, area.casefold(), priority, weight, seq)


class TestRules(unittest.TestCase):

    def test_empty_input_gives_no_trips(self):
        self.assertEqual(plan_trips([]), [])

    def test_no_trip_exceeds_capacity(self):
        deliveries = [make(str(i), "Maadi", 1, 3.5, i) for i in range(10)]
        for trip in plan_trips(deliveries, capacity=10.0):
            self.assertLessEqual(trip.total_weight, 10.0 + 1e-9)

    def test_every_delivery_appears_exactly_once(self):
        deliveries = [
            make("1", "Nasr City", 2, 4.5, 0),
            make("2", "Maadi", 1, 2.0, 1),
            make("3", "Nasr City", 3, 1.2, 2),
            make("4", "Zamalek", 1, 7.0, 3),
            make("5", "Maadi", 2, 3.5, 4),
        ]
        placed = [d.id for trip in plan_trips(deliveries) for d in trip.deliveries]
        self.assertEqual(sorted(placed), ["1", "2", "3", "4", "5"])
        self.assertEqual(len(placed), len(set(placed)))

    def test_trips_are_single_area_without_merging(self):
        deliveries = [
            make("1", "Maadi", 1, 4.0, 0),
            make("2", "Zamalek", 1, 4.0, 1),
        ]
        trips = plan_trips(deliveries)
        self.assertEqual(len(trips), 2)
        for trip in trips:
            self.assertFalse(trip.is_mixed)

    def test_exactly_full_trip_is_allowed(self):
        deliveries = [
            make("1", "Maadi", 1, 4.5, 0),
            make("2", "Maadi", 1, 3.5, 1),
            make("3", "Maadi", 1, 2.0, 2),
        ]
        trips = plan_trips(deliveries)
        self.assertEqual(len(trips), 1)
        self.assertAlmostEqual(trips[0].total_weight, 10.0)

    def test_most_urgent_trip_is_dispatched_first(self):
        deliveries = [
            make("1", "Nasr City", 3, 2.0, 0),
            make("2", "Maadi", 1, 2.0, 1),
        ]
        self.assertEqual(plan_trips(deliveries)[0].top_priority, 1)

    def test_output_is_deterministic(self):
        deliveries = [make(str(i), "Maadi", 1, 2.5, i) for i in range(7)]
        first = [[d.id for d in t.deliveries] for t in plan_trips(deliveries)]
        second = [[d.id for d in t.deliveries] for t in plan_trips(list(deliveries))]
        self.assertEqual(first, second)


class TestMergeExtension(unittest.TestCase):

    def test_merge_combines_two_nearly_empty_trips(self):
        deliveries = [
            make("1", "Maadi", 1, 1.0, 0),
            make("2", "Zamalek", 1, 1.0, 1),
        ]
        self.assertEqual(len(plan_trips(deliveries)), 2)
        merged = plan_trips(deliveries, merge_leftovers=True)
        self.assertEqual(len(merged), 1)
        self.assertTrue(merged[0].is_mixed)

    def test_merge_never_breaks_capacity(self):
        deliveries = [
            make("1", "Maadi", 1, 4.0, 0),
            make("2", "Zamalek", 1, 4.0, 1),
            make("3", "Dokki", 1, 4.0, 2),
        ]
        for trip in plan_trips(deliveries, merge_leftovers=True):
            self.assertLessEqual(trip.total_weight, 10.0 + 1e-9)

    def test_well_filled_trips_are_left_alone(self):
        deliveries = [
            make("1", "Maadi", 1, 6.0, 0),
            make("2", "Zamalek", 1, 3.0, 1),
        ]
        trips = plan_trips(deliveries, merge_leftovers=True)
        self.assertEqual(len(trips), 2)


class TestLoader(unittest.TestCase):

    def test_sample_file_loads(self):
        deliveries, rejected = load_deliveries(os.path.join(DATA, "deliveries.csv"), 10.0)
        self.assertEqual(len(deliveries), 5)
        self.assertEqual(rejected, [])

    def test_csv_and_json_agree(self):
        from_csv, _ = load_deliveries(os.path.join(DATA, "deliveries.csv"), 10.0)
        from_json, _ = load_deliveries(os.path.join(DATA, "deliveries.json"), 10.0)
        self.assertEqual([d.id for d in from_csv], [d.id for d in from_json])

    def test_bad_rows_are_rejected_with_reasons(self):
        deliveries, rejected = load_deliveries(os.path.join(DATA, "edge_cases.csv"), 10.0)
        reasons = {item.identifier: item.reason for item in rejected}
        self.assertIn("6", reasons)                      # 12 kg > capacity
        self.assertIn("exceeds vehicle capacity", reasons["6"])
        self.assertIn("10", reasons)                     # weight "abc"
        self.assertIn("11", reasons)                     # negative weight
        self.assertTrue(all(d.weight > 0 for d in deliveries))

    def test_area_spelling_is_normalised(self):
        deliveries, _ = load_deliveries(os.path.join(DATA, "edge_cases.csv"), 10.0)
        keys = {d.area_key for d in deliveries if "nasr" in d.area_key}
        self.assertEqual(len(keys), 1)

    def test_empty_file_returns_nothing(self):
        deliveries, rejected = load_deliveries(os.path.join(DATA, "empty.csv"), 10.0)
        self.assertEqual(deliveries, [])
        self.assertEqual(rejected, [])


class TestTrip(unittest.TestCase):

    def test_add_beyond_capacity_raises(self):
        trip = Trip(capacity=10.0)
        trip.add(make("1", "Maadi", 1, 9.0))
        with self.assertRaises(ValueError):
            trip.add(make("2", "Maadi", 1, 2.0))


if __name__ == "__main__":
    unittest.main()