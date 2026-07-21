import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from personalization import PersonalizationEngine, PROFILES, score_outcome


def snapshot(day: int = 1, *, sleep_minutes=450, sleep_score=80, steps=8000,
             exercise_age_minutes=300, current_hr=64, sleepiness=6, tension=3,
             illness=False, pain=False, confidence="high", missing=None):
    generated = datetime(2026, 7, day, 14, 0, tzinfo=timezone.utc)
    return {
        "schema": 1,
        "type": "daily_snapshot",
        "generated_at": generated.isoformat(),
        "previous_sleep": {"duration_minutes": sleep_minutes, "score": sleep_score},
        "today": {
            "steps": steps,
            "active_minutes": 40,
            "exercise_count": 1 if exercise_age_minutes is not None else 0,
            "last_exercise_end": (generated - timedelta(minutes=exercise_age_minutes)).isoformat()
            if exercise_age_minutes is not None else None,
            "current_hr_median": current_hr,
            "day_hr_median": 72,
            "latest_resting_hr": 60,
        },
        "check_in": {
            "sleepiness": sleepiness,
            "tension": tension,
            "illness": illness,
            "pain": pain,
            "alcohol": False,
            "caffeine_after_15_00": False,
            "late_meal": False,
        },
        "confidence": confidence,
        "missing": missing or [],
    }


class PersonalizationTest(unittest.TestCase):
    def test_score_prefers_subjective_outcomes(self):
        score, components = score_outcome({
            "subjective_sleep_quality": 8,
            "morning_alertness": 7,
            "sleep_duration_minutes": 460,
        })
        self.assertGreater(score, 75)
        self.assertEqual(components["subjective_sleep_quality"], 80)

    def test_classifies_major_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = PersonalizationEngine(Path(directory))
            self.assertEqual(engine.classify(snapshot())[0], "ready")
            self.assertEqual(engine.classify(snapshot(tension=8, sleepiness=4))[0], "mentally_activated")
            self.assertEqual(engine.classify(snapshot(exercise_age_minutes=60))[0], "physically_activated")
            self.assertEqual(engine.classify(snapshot(sleep_minutes=340))[0], "under_recovered")
            self.assertEqual(engine.classify(snapshot(sleepiness=2))[0], "low_sleep_pressure")
            self.assertEqual(engine.classify(snapshot(illness=True))[0], "possible_illness")
            self.assertEqual(engine.classify(snapshot(missing=["a", "b", "c"]))[0], "unknown")

    def test_nightly_plan_is_idempotent_and_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = PersonalizationEngine(Path(directory))
            first = engine.plan_night(snapshot(), "2026-07-01")
            second = engine.plan_night(snapshot(), "2026-07-01")
            self.assertEqual(first["decision_id"], second["decision_id"])
            self.assertEqual(len(engine.decisions()), 1)
            self.assertFalse(first["safety"]["during_sleep_actuation"])
            self.assertIn(first["profile_id"], PROFILES)
            replacement = engine.plan_night(snapshot(), "2026-07-01", force=True)
            self.assertNotEqual(first["decision_id"], replacement["decision_id"])
            self.assertEqual(len(engine.decisions()), 1)

    def test_demo_snapshot_never_trains_personal_model(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = PersonalizationEngine(Path(directory))
            value = snapshot()
            value["data_freshness"] = {"health_source": "demo"}
            plan = engine.plan_night(value, "2026-07-01")
            self.assertFalse(plan["eligible_for_learning"])
            engine.record_outcome("2026-07-01", subjective_sleep_quality=10)
            self.assertEqual(engine.report("2026-07")["completed_nights"], 0)

    def test_outcome_rejects_missing_plan_and_bad_rating(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = PersonalizationEngine(Path(directory))
            with self.assertRaises(ValueError):
                engine.record_outcome("2026-07-01", subjective_sleep_quality=8)
            engine.plan_night(snapshot(), "2026-07-01")
            with self.assertRaises(ValueError):
                engine.record_outcome("2026-07-01", subjective_sleep_quality=12)
            with self.assertRaises(ValueError):
                engine.record_outcome("2026-07-01", nightmare="yes", sleep_duration_minutes=450)

    def test_next_evening_imports_vendor_outcome_once(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = PersonalizationEngine(Path(directory))
            engine.plan_night(snapshot(1), "2026-07-01")
            imported = engine.import_previous_sleep(snapshot(2, sleep_minutes=432, sleep_score=76), "2026-07-02")
            self.assertEqual(imported["sleep_duration_minutes"], 432)
            self.assertEqual(imported["vendor_sleep_score"], 76)
            self.assertIsNone(engine.import_previous_sleep(snapshot(2), "2026-07-02"))

    def test_month_loop_learns_and_writes_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = PersonalizationEngine(root)
            profile_quality = {"control": 6.0, "long_light_fade": 8.5, "silence": 7.0,
                               "breathing": 7.2, "earlier_wind_down": 7.1}
            for day in range(1, 31):
                night = f"2026-07-{day:02d}"
                plan = engine.plan_night(snapshot(day), night)
                quality = profile_quality[plan["profile_id"]]
                engine.record_outcome(
                    night,
                    subjective_sleep_quality=quality,
                    morning_alertness=min(10, quality - 0.5),
                    sleep_duration_minutes=450,
                    awakenings=1,
                    nightmare=False,
                    sleep_latency_minutes=20,
                )
            report = engine.report("2026-07")
            self.assertEqual(report["completed_nights"], 30)
            self.assertEqual(report["best_supported_profile"], "long_light_fade")
            for path in report["files"].values():
                self.assertTrue(Path(path).exists())
            html_text = Path(report["files"]["html"]).read_text(encoding="utf-8")
            self.assertIn("Intervention results", html_text)
            json.loads(Path(report["files"]["json"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
