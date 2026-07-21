#!/usr/bin/env python3
"""Create the nightly snapshot and select one personalized experiment."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from personalization import PersonalizationEngine
from sleep_tight_core import SleepTightStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parent / "data")
    args = parser.parse_args()
    snapshot = SleepTightStore(args.data_dir).build_snapshot()
    engine = PersonalizationEngine(args.data_dir)
    night = datetime.now().astimezone().date().isoformat()
    imported_outcome = engine.import_previous_sleep(snapshot, night)
    plan = engine.plan_night(snapshot, night)
    print(json.dumps({"snapshot": snapshot, "imported_previous_outcome": imported_outcome,
                      "nightly_plan": plan}, indent=2))


if __name__ == "__main__":
    main()
