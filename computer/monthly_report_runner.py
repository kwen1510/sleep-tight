#!/usr/bin/env python3
"""Generate last month's local personalization report."""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from personalization import PersonalizationEngine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parent / "data")
    parser.add_argument("--month", help="YYYY-MM; defaults to the previous calendar month")
    args = parser.parse_args()
    previous_month = (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    print(json.dumps(PersonalizationEngine(args.data_dir).report(args.month or previous_month), indent=2))


if __name__ == "__main__":
    main()
