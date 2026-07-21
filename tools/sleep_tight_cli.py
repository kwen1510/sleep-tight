#!/usr/bin/env python3
"""Small command-line client for the local Sleep Tight API."""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


def settings():
    config = json.loads((ROOT / "computer/config.json").read_text(encoding="utf-8"))
    return "http://127.0.0.1:8766", config["token"]


def request(method, path, body=None):
    base, token = settings()
    encoded = json.dumps(body).encode() if body is not None else None
    req = Request(base + path, data=encoded, method=method,
                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        raise SystemExit(f"API error {error.code}: {error.read().decode()}")


def demo_payload():
    now = datetime.now(timezone.utc)
    sleep_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    sleep_start = sleep_end - timedelta(hours=7, minutes=18)
    return {
        "schema": 1, "type": "health_sync", "source": "demo",
        "generated_at": now.isoformat(), "window_start": (now - timedelta(days=8)).isoformat(),
        "window_end": now.isoformat(), "permissions": {"demo": True},
        "sleep_sessions": [{"record_id": "demo-sleep-latest", "start_time": sleep_start.isoformat(), "end_time": sleep_end.isoformat(),
                            "duration_minutes": 438, "score": 78, "stages": [], "source": "demo"}],
        "heart_rate_samples": [{"record_id": f"demo-hr-{i}", "time": (now - timedelta(minutes=i)).isoformat(), "bpm": 68 + i % 5}
                               for i in range(120)],
        "resting_heart_rate_records": [{"record_id": "demo-resting-hr", "time": now.isoformat(), "bpm": 61}],
        "steps_records": [{"record_id": "demo-steps-today", "start_time": now.replace(hour=0, minute=0).isoformat(),
                           "end_time": now.isoformat(), "count": 8642}],
        "exercise_sessions": [{"record_id": "demo-exercise-today", "start_time": (now - timedelta(hours=3, minutes=40)).isoformat(),
                               "end_time": (now - timedelta(hours=3)).isoformat(), "exercise_type": "walking"}],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "snapshot", "demo", "check-in"])
    parser.add_argument("--sleepiness", type=float)
    parser.add_argument("--tension", type=float)
    args = parser.parse_args()
    if args.command == "status": result = request("GET", "/api/v1/status")
    elif args.command == "snapshot": result = request("POST", "/api/v1/snapshots/run", {})
    elif args.command == "demo":
        request("POST", "/api/v1/ingest/health", demo_payload())
        result = request("POST", "/api/v1/snapshots/run", {})
    else:
        result = request("POST", "/api/v1/check-in", {
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "sleepiness": args.sleepiness, "tension": args.tension,
        })
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
