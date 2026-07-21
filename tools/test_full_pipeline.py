#!/usr/bin/env python3
"""Send every implemented phone category through the live API in one request.

The source is `demo`, so it is excluded from personalization and automatically
ignored as soon as a real Health Connect upload exists.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "computer/config.json").read_text(encoding="utf-8"))
BASE = "http://127.0.0.1:8766"
TOKEN = CONFIG["token"]


def call(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    request = Request(BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
    })
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def payload() -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    sleep_end = now - timedelta(hours=16)
    sleep_start = sleep_end - timedelta(hours=7, minutes=30)
    day_start = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    attempted = [
        "sleep_sessions", "heart_rate_samples", "resting_heart_rate_records", "steps_records",
        "exercise_sessions", "active_calories_records", "total_calories_records",
        "oxygen_saturation_samples", "respiratory_rate_samples", "skin_temperature_records",
        "floors_climbed_records",
    ]
    return {
        "schema": 1, "type": "health_sync", "source": "demo",
        "generated_at": now.isoformat(), "window_start": (now - timedelta(days=8)).isoformat(),
        "window_end": now.isoformat(), "attempted_categories": attempted, "extraction_errors": {},
        "permissions": {category: True for category in attempted},
        "device": {"platform": "contract_test", "note": "Synthetic all-fields transport test"},
        "sleep_sessions": [{
            "record_id": "contract-sleep", "start_time": sleep_start.isoformat(),
            "end_time": sleep_end.isoformat(), "duration_minutes": 450, "score": 82,
            "source": "demo", "stages": [
                {"start_time": sleep_start.isoformat(), "end_time": (sleep_start + timedelta(hours=1)).isoformat(), "stage": "deep"},
                {"start_time": (sleep_start + timedelta(hours=1)).isoformat(), "end_time": sleep_end.isoformat(), "stage": "light_or_rem"},
            ],
        }],
        "heart_rate_samples": [{"record_id": "contract-hr", "time": (now - timedelta(minutes=5)).isoformat(), "bpm": 67}],
        "resting_heart_rate_records": [{"record_id": "contract-rhr", "time": (now - timedelta(hours=3)).isoformat(), "bpm": 59}],
        "steps_records": [{"record_id": "contract-steps", "start_time": day_start.isoformat(), "end_time": now.isoformat(), "count": 7654}],
        "exercise_sessions": [{"record_id": "contract-exercise", "start_time": (now - timedelta(hours=4)).isoformat(), "end_time": (now - timedelta(hours=3, minutes=20)).isoformat(), "exercise_type": "walking"}],
        "active_calories_records": [{"record_id": "contract-active-cal", "start_time": day_start.isoformat(), "end_time": now.isoformat(), "kilocalories": 320}],
        "total_calories_records": [{"record_id": "contract-total-cal", "start_time": day_start.isoformat(), "end_time": now.isoformat(), "kilocalories": 1820}],
        "oxygen_saturation_samples": [{"record_id": "contract-o2", "time": (sleep_start + timedelta(hours=2)).isoformat(), "percentage": 96}],
        "respiratory_rate_samples": [{"record_id": "contract-rr", "time": (sleep_start + timedelta(hours=2)).isoformat(), "breaths_per_minute": 15}],
        "skin_temperature_records": [{"record_id": "contract-temp", "start_time": sleep_start.isoformat(), "end_time": sleep_end.isoformat(), "baseline_celsius": 33.0, "deltas": [{"time": (sleep_start + timedelta(hours=2)).isoformat(), "celsius": 0.18}]}],
        "floors_climbed_records": [{"record_id": "contract-floors", "start_time": day_start.isoformat(), "end_time": now.isoformat(), "floors": 7}],
    }


def main() -> None:
    ingest = call("POST", "/api/v1/ingest/health", payload())
    now = datetime.now(timezone.utc).isoformat()
    call("POST", "/api/v1/check-in", {
        "observed_at": now, "sleepiness": 6, "tension": 3, "mood": 7,
        "caffeine_after_15_00": False, "alcohol": False, "illness": False,
        "pain": False, "late_meal": False, "note": "Synthetic contract test",
    })
    snapshot = call("POST", "/api/v1/snapshots/run", {})
    coverage = snapshot["extraction"]["coverage"]
    required = [
        "sleep_session", "sleep_stages", "vendor_sleep_score", "daytime_heart_rate",
        "resting_heart_rate", "steps", "exercise", "active_calories", "total_calories",
        "oxygen_saturation", "respiratory_rate", "skin_temperature", "floors_climbed",
        "pre_bed_heart_rate", "subjective_check_in",
    ]
    failures = [name for name in required if not coverage[name]["available"]]
    report = {
        "passed": not failures and not ingest["extraction_errors"],
        "tested_at": now,
        "one_request_counts": ingest["counts"],
        "failed_available_signals": failures,
        "future_signals": [name for name, value in coverage.items() if value["status"] == "future"],
        "snapshot": str(ROOT / "computer/data/snapshots/latest.json"),
    }
    output = ROOT / "computer/data/contract-test-report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
