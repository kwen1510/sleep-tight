#!/usr/bin/env python3
"""Operate the local Sleep Tight personalization loop."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPUTER = ROOT / "computer"
sys.path.insert(0, str(COMPUTER))

from personalization import PersonalizationEngine  # noqa: E402
from sleep_tight_core import SleepTightStore  # noqa: E402


def load_snapshot(data_dir: Path, path: Path | None = None, build: bool = False) -> dict:
    if build:
        return SleepTightStore(data_dir).build_snapshot()
    path = path or data_dir / "snapshots/latest.json"
    if not path.exists():
        raise SystemExit(f"No snapshot found at {path}. Run `python3 tools/sleep_tight_cli.py snapshot` first.")
    return json.loads(path.read_text(encoding="utf-8"))


def latest_open_night(engine: PersonalizationEngine) -> str:
    completed = {row["decision_id"] for row in engine.outcomes()}
    for decision in reversed(engine.decisions()):
        if decision["decision_id"] not in completed:
            return decision["night"]
    raise SystemExit("There is no planned night waiting for a morning outcome.")


def status(engine: PersonalizationEngine) -> dict:
    decisions = engine.decisions()
    outcomes = engine.outcomes()
    completed = {row["decision_id"] for row in outcomes}
    latest = decisions[-1] if decisions else None
    return {
        "planned_nights": len(decisions),
        "learning_eligible_nights": sum(1 for row in decisions if row.get("eligible_for_learning", False)),
        "excluded_demo_or_unknown_nights": sum(1 for row in decisions if not row.get("eligible_for_learning", False)),
        "completed_outcomes": len(completed),
        "awaiting_morning_outcome": [row["night"] for row in decisions if row["decision_id"] not in completed],
        "latest_plan": latest,
        "personalization_directory": str(engine.root),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sleep Tight's local N-of-1 personalization engine")
    parser.add_argument("--data-dir", type=Path, default=COMPUTER / "data")
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="select tonight's single-variable experiment")
    plan.add_argument("--night", help="night in YYYY-MM-DD form; defaults to today")
    plan.add_argument("--snapshot", type=Path)
    plan.add_argument("--build-snapshot", action="store_true")
    plan.add_argument("--force", action="store_true", help="append a replacement plan for testing only")

    morning = commands.add_parser("morning", help="record the outcome of a planned night")
    morning.add_argument("--night", help="defaults to the newest plan without an outcome")
    morning.add_argument("--quality", type=float, help="subjective sleep quality, 0-10")
    morning.add_argument("--alertness", type=float, help="morning alertness, 0-10")
    morning.add_argument("--duration", type=float, help="sleep duration in minutes")
    morning.add_argument("--sleep-score", type=float)
    morning.add_argument("--awakenings", type=int)
    nightmare = morning.add_mutually_exclusive_group()
    nightmare.add_argument("--nightmare", action="store_true", dest="nightmare_value")
    nightmare.add_argument("--no-nightmare", action="store_false", dest="nightmare_value")
    morning.set_defaults(nightmare_value=None)
    morning.add_argument("--latency", type=float, help="estimated minutes to fall asleep")
    morning.add_argument("--notes")
    morning.add_argument("--snapshot", type=Path)

    report = commands.add_parser("report", help="create JSON, Markdown, and HTML monthly reports")
    report.add_argument("--month", help="YYYY-MM; defaults to the current month")
    commands.add_parser("status", help="show experiment progress")

    args = parser.parse_args()
    engine = PersonalizationEngine(args.data_dir)
    if args.command == "plan":
        result = engine.plan_night(load_snapshot(args.data_dir, args.snapshot, args.build_snapshot), args.night, args.force)
    elif args.command == "morning":
        snapshot = load_snapshot(args.data_dir, args.snapshot) if (args.snapshot or (args.data_dir / "snapshots/latest.json").exists()) else None
        result = engine.record_outcome(
            args.night or latest_open_night(engine),
            subjective_sleep_quality=args.quality,
            morning_alertness=args.alertness,
            sleep_duration_minutes=args.duration,
            vendor_sleep_score=args.sleep_score,
            awakenings=args.awakenings,
            nightmare=args.nightmare_value,
            sleep_latency_minutes=args.latency,
            notes=args.notes,
            snapshot=snapshot,
        )
    elif args.command == "report":
        result = engine.report(args.month)
    else:
        result = status(engine)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
