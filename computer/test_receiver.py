import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from receiver import validate_event
from sleep_tight_core import SleepTightStore, validate_checkin, validate_health_sync


class ValidateEventTest(unittest.TestCase):
    def test_accepts_heart_rate(self):
        event = validate_event(json.dumps({
            "type": "heart_rate",
            "bpm": 61.5,
            "sequence": 1,
            "observed_at": "2026-07-14T12:00:00Z",
        }))
        self.assertEqual(event["bpm"], 61.5)

    def test_rejects_bad_bpm(self):
        with self.assertRaises(ValueError):
            validate_event(json.dumps({
                "type": "heart_rate",
                "bpm": "fast",
                "sequence": 1,
                "observed_at": "2026-07-14T12:00:00Z",
            }))


class HealthSyncTest(unittest.TestCase):
    def payload(self):
        return {
            "schema": 1,
            "type": "health_sync",
            "source": "health_connect",
            "generated_at": "2026-07-18T13:55:00Z",
            "window_start": "2026-07-10T00:00:00Z",
            "window_end": "2026-07-18T14:00:00Z",
            "permissions": {"sleep": True, "steps": True},
            "sleep_sessions": [{
                "start_time": "2026-07-17T15:00:00Z",
                "end_time": "2026-07-17T22:00:00Z",
                "duration_minutes": 420,
                "score": None,
                "stages": [],
                "source": "health_connect",
            }],
            "steps_records": [{"start_time": "2026-07-18T00:00:00Z", "end_time": "2026-07-18T12:00:00Z", "count": 8123}],
            "exercise_sessions": [{"start_time": "2026-07-18T10:00:00Z", "end_time": "2026-07-18T10:45:00Z", "exercise_type": 56}],
        }

    def test_validates_and_defaults_lists(self):
        event = validate_health_sync(self.payload())
        self.assertEqual(event["source"], "health_connect")
        self.assertEqual(event["heart_rate_samples"], [])

    def test_builds_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SleepTightStore(Path(directory))
            store.ingest_health(self.payload())
            store.ingest_checkin({"observed_at": "2026-07-18T13:58:00Z", "sleepiness": 7, "tension": 3})
            store.append_heart_rate({"type": "heart_rate", "observed_at": "2026-07-18T13:59:00Z", "bpm": 64})
            snapshot = store.build_snapshot(datetime(2026, 7, 18, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(snapshot["today"]["steps"], 8123)
            self.assertEqual(snapshot["today"]["active_minutes"], 45.0)
            self.assertEqual(snapshot["today"]["current_hr_median"], 64.0)
            self.assertEqual(snapshot["previous_sleep"]["duration_minutes"], 420)

    def test_overlapping_syncs_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SleepTightStore(Path(directory))
            store.ingest_health(self.payload())
            store.ingest_health(self.payload())
            snapshot = store.build_snapshot(datetime(2026, 7, 18, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(snapshot["today"]["steps"], 8123)
            self.assertEqual(snapshot["available_record_counts"]["steps_records"], 1)

    def test_checkin_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_checkin({"observed_at": "2026-07-18T13:00:00Z", "tension": 11})

    def test_every_supported_category_survives_one_sync(self):
        payload = self.payload()
        payload.update({
            "attempted_categories": sorted([
                "sleep_sessions", "heart_rate_samples", "resting_heart_rate_records", "steps_records",
                "exercise_sessions", "active_calories_records", "total_calories_records",
                "oxygen_saturation_samples", "respiratory_rate_samples", "skin_temperature_records",
                "floors_climbed_records",
            ]),
            "extraction_errors": {},
            "heart_rate_samples": [{"record_id": "hr", "time": "2026-07-18T13:55:00Z", "bpm": 68}],
            "resting_heart_rate_records": [{"record_id": "rhr", "time": "2026-07-18T12:00:00Z", "bpm": 58}],
            "active_calories_records": [{"record_id": "ac", "start_time": "2026-07-18T10:00:00Z", "end_time": "2026-07-18T11:00:00Z", "kilocalories": 210}],
            "total_calories_records": [{"record_id": "tc", "start_time": "2026-07-18T00:00:00Z", "end_time": "2026-07-18T13:00:00Z", "kilocalories": 1650}],
            "oxygen_saturation_samples": [{"record_id": "o2", "time": "2026-07-17T20:00:00Z", "percentage": 96}],
            "respiratory_rate_samples": [{"record_id": "rr", "time": "2026-07-17T20:00:00Z", "breaths_per_minute": 15}],
            "skin_temperature_records": [{"record_id": "temp", "start_time": "2026-07-17T15:00:00Z", "end_time": "2026-07-17T22:00:00Z", "baseline_celsius": 33.1, "deltas": [{"time": "2026-07-17T20:00:00Z", "celsius": 0.2}]}],
            "floors_climbed_records": [{"record_id": "floors", "start_time": "2026-07-18T00:00:00Z", "end_time": "2026-07-18T13:00:00Z", "floors": 8}],
        })
        with tempfile.TemporaryDirectory() as directory:
            store = SleepTightStore(Path(directory))
            result = store.ingest_health(payload)
            self.assertTrue(result["accepted"])
            self.assertEqual(result["transport"], "wifi_lan")
            self.assertTrue(result["received_at"].endswith("Z"))
            self.assertEqual(result["total_records"], sum(result["counts"].values()))
            store.ingest_checkin({"observed_at": "2026-07-18T13:58:00Z", "sleepiness": 6, "tension": 2})
            store.append_heart_rate({"type": "heart_rate", "observed_at": "2026-07-18T13:59:00Z", "bpm": 64})
            store._append("pre-bed-summary", {"type": "pre_bed_summary", "window_start": "2026-07-18T13:49:00Z", "window_end": "2026-07-18T13:59:00Z", "sample_count": 600, "median_bpm": 64}, datetime(2026, 7, 18, 13, 59, tzinfo=timezone.utc))
            snapshot = store.build_snapshot(datetime(2026, 7, 18, 14, 0, tzinfo=timezone.utc))
            self.assertFalse(result["extraction_errors"])
            self.assertEqual(snapshot["today"]["active_calories_kcal"], 210.0)
            self.assertEqual(snapshot["today"]["total_calories_kcal"], 1650.0)
            self.assertEqual(snapshot["today"]["floors_climbed"], 8.0)
            self.assertEqual(snapshot["overnight_physiology"]["oxygen_median_percent"], 96.0)
            self.assertEqual(snapshot["overnight_physiology"]["respiratory_rate_median"], 15.0)
            self.assertEqual(snapshot["overnight_physiology"]["skin_temperature_delta_median_celsius"], 0.2)
            coverage = snapshot["extraction"]["coverage"]
            for signal in ("sleep_session", "daytime_heart_rate", "steps", "exercise", "active_calories",
                           "total_calories", "oxygen_saturation", "respiratory_rate", "skin_temperature",
                           "floors_climbed", "pre_bed_heart_rate", "subjective_check_in"):
                self.assertTrue(coverage[signal]["available"], signal)
            self.assertFalse(coverage["ibi_hrv"]["available"])


if __name__ == "__main__":
    unittest.main()
