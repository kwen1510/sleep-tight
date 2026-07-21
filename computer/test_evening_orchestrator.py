import json
import tempfile
import unittest
from unittest.mock import patch
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from evening_orchestrator import EveningOrchestrator


class EveningOrchestratorTest(unittest.TestCase):
    def health_payload(self, now, source="health_connect"):
        return {
            "schema": 1, "type": "health_sync", "source": source,
            "generated_at": now.isoformat(), "window_start": (now - timedelta(hours=24)).isoformat(),
            "window_end": now.isoformat(), "permissions": {}, "attempted_categories": [],
            "extraction_errors": {}, "device": {"platform": "test", "correlation_id": "same-run"},
            "sleep_sessions": [], "heart_rate_samples": [], "resting_heart_rate_records": [],
            "steps_records": [], "exercise_sessions": [], "active_calories_records": [],
            "total_calories_records": [], "oxygen_saturation_samples": [],
            "respiratory_rate_samples": [], "skin_temperature_records": [], "floors_climbed_records": [],
        }

    def test_builds_idempotent_room_command_with_source_freshness(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            engine = EveningOrchestrator(data, Path(__file__).parents[1], enable_codex=False)
            now = datetime.now(timezone.utc)
            engine.store.ingest_health(self.health_payload(now))
            engine.store._append("pre-bed-summary", {
                "schema": 1, "type": "pre_bed_summary", "window_start": (now - timedelta(minutes=1)).isoformat(),
                "window_end": now.isoformat(), "sample_count": 60, "median_bpm": 66,
                "correlation_id": "same-run", "received_at": now.isoformat(),
            }, now)
            first = engine.run("manual-test", start_codex=False)
            command_before = (data / first["room_command"]).read_text(encoding="utf-8")
            second = engine.run("manual-test", start_codex=False)
            self.assertEqual(first, second)
            self.assertEqual(command_before, (data / first["room_command"]).read_text(encoding="utf-8"))
            self.assertEqual(first["sources"]["fresh_source_count"], 2)
            self.assertEqual(first["sources"]["transport"], "wifi_lan")
            self.assertEqual(first["sources"]["watch"]["counts"]["heart_rate_samples"], 60)
            self.assertEqual(first["sources"]["automation"]["watch"]["time"], "21:55")
            self.assertEqual(first["sources"]["automation"]["codex"]["time"], "22:05")

    def test_synthetic_input_is_excluded_from_learning(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            engine = EveningOrchestrator(data, Path(__file__).parents[1], enable_codex=False)
            now = datetime.now(timezone.utc)
            payload = self.health_payload(now, source="demo")
            payload["device"]["simulation"] = True
            engine.store.ingest_health(payload)
            result = engine.run("synthetic-test", start_codex=False)
            plan = json.loads((data / result["plan"]).read_text(encoding="utf-8"))
            command = json.loads((data / result["room_command"]).read_text(encoding="utf-8"))
            self.assertFalse(plan["eligible_for_learning"])
            self.assertEqual(command["data_status"], "synthetic_input")

    def test_no_data_uses_conservative_control(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            engine = EveningOrchestrator(data, Path(__file__).parents[1], enable_codex=False)
            result = engine.run("empty-test", start_codex=False)
            plan = json.loads((data / result["plan"]).read_text(encoding="utf-8"))
            command = json.loads((data / result["room_command"]).read_text(encoding="utf-8"))
            self.assertEqual(plan["profile_id"], "control")
            self.assertEqual(command["confidence"], "low")
            self.assertEqual(command["missing_or_stale_sources"], ["phone", "watch"])

    def test_old_phone_upload_is_stale_and_watch_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            engine = EveningOrchestrator(data, Path(__file__).parents[1], enable_codex=False)
            now = datetime.now(timezone.utc)
            old = now - timedelta(minutes=20)
            event = self.health_payload(old)
            event["received_at"] = old.isoformat()
            engine.store._append("health-sync", event, old)
            status = engine.source_status(now)
            self.assertTrue(status["phone"]["available"])
            self.assertFalse(status["phone"]["fresh"])
            self.assertFalse(status["watch"]["available"])
            self.assertEqual(status["missing_or_stale"], ["phone", "watch"])

    def test_codex_timeout_is_non_blocking_status(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = EveningOrchestrator(Path(directory), Path(__file__).parents[1], enable_codex=True)
            engine.run("timeout-test", start_codex=False)
            with patch("evening_orchestrator.shutil.which", return_value="/tmp/codex"), patch(
                "evening_orchestrator.subprocess.run", side_effect=subprocess.TimeoutExpired("codex", 600)
            ):
                engine._codex_worker("timeout-test")
            self.assertEqual(engine.status("timeout-test")["codex"]["state"], "timeout")
            self.assertEqual(engine.status("timeout-test")["state"], "codex_error")

    def test_codex_decision_is_validated_before_scene_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            engine = EveningOrchestrator(data, Path(__file__).parents[1], enable_codex=False)
            engine.run("codex-success-test", start_codex=False)
            engine.enable_codex = True
            decision = {
                "profile_label": "Quiet instrumental descent",
                "light_start_percent": 34,
                "fade_minutes": 35,
                "sound_profile": "low_arousal_instrumental",
                "sound_start_percent": 18,
                "tempo_bpm": 62,
                "confidence": "medium",
                "decision_reason": "Recent heart rate is settling and the available history supports a gentle routine.",
                "evidence_used": ["Fresh watch capture", "Recent phone activity"],
                "missing_data": ["Previous sleep session"],
            }
            with patch("evening_orchestrator.shutil.which", return_value="/tmp/codex"), patch(
                "evening_orchestrator.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0, stdout=json.dumps(decision), stderr=""),
            ):
                engine._codex_worker("codex-success-test")
            status = engine.status("codex-success-test")
            command = json.loads((data / status["room_command"]).read_text(encoding="utf-8"))
            self.assertEqual(status["state"], "scene_ready")
            self.assertEqual(command["generated_by"], "Codex constrained decision")
            self.assertEqual(command["sound"]["start_percent"], 18)
            self.assertAlmostEqual(command["schedule"]["demo_minutes_per_second"], 1 / 60, places=7)
            self.assertTrue(command["safety"]["codex_decision_schema_validated"])

    def test_codex_failure_is_recorded_without_changing_command(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            engine = EveningOrchestrator(data, Path(__file__).parents[1], enable_codex=False)
            result = engine.run("codex-error-test", start_codex=False)
            command_before = (data / result["room_command"]).read_text(encoding="utf-8")
            engine.enable_codex = True
            with patch("evening_orchestrator.shutil.which", return_value="/tmp/codex"), patch(
                "evening_orchestrator.subprocess.run",
                return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="authentication failed"),
            ):
                engine._codex_worker("codex-error-test")
            self.assertEqual(engine.status("codex-error-test")["codex"]["state"], "error")
            self.assertEqual(command_before, (data / result["room_command"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
