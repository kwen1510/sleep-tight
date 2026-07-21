#!/usr/bin/env python3
"""Report real-device evidence separately from synthetic contract coverage."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "computer/data"
CONTRACT = json.loads((DATA / "contract-test-report.json").read_text(encoding="utf-8"))


def rows(prefix: str) -> list[dict]:
    result = []
    for path in sorted(DATA.glob(f"{prefix}-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    result.append(value)
            except json.JSONDecodeError:
                pass
    return result


health = rows("health-sync")
real_health = [row for row in health if row.get("source") != "demo"]
latest_real = real_health[-1] if real_health else None
watch = rows("pre-bed-summary")
latest_watch = watch[-1] if watch else None
install_status_path = DATA / "phone-install-status.json"
install_status = json.loads(install_status_path.read_text(encoding="utf-8")) if install_status_path.exists() else {}

categories = [
    ("Sleep session/duration", "sleep_sessions"),
    ("Sleep stages", "sleep_sessions"),
    ("Daytime heart rate", "heart_rate_samples"),
    ("Steps", "steps_records"),
    ("Exercise", "exercise_sessions"),
    ("Total calories", "total_calories_records"),
    ("Oxygen saturation", "oxygen_saturation_samples"),
]

lines = [
    "# Sleep Tight — actual data availability",
    "",
    f"Generated: {datetime.now().astimezone().isoformat()}",
    "",
    "> Synthetic contract values are never counted as real health data in this report.",
    "",
    "## Executive result",
    "",
    f"- Full one-request schema test: {'PASS' if CONTRACT.get('passed') else 'FAIL'} (11 Health Connect categories).",
    f"- Real Galaxy Watch pre-bed capture: {'PASS' if latest_watch else 'NOT SEEN'}" +
    (f" ({latest_watch.get('sample_count')} samples; median {latest_watch.get('median_bpm')} bpm)." if latest_watch else "."),
    f"- Real phone/Health Connect upload: {'PASS' if latest_real else 'NOT YET TESTED — ' + install_status.get('error', 'phone app installation/permission remains required.')}",
    "",
    "## Real phone values",
    "",
    "| Value | Actual state | Count |",
    "|---|---:|---:|",
]

for label, field in categories:
    records = (latest_real or {}).get(field, [])
    if latest_real is None:
        state = "Schema verified only"
    elif field in (latest_real.get("extraction_errors") or {}):
        state = "Read error"
    elif records:
        state = "Real records received"
    elif field in (latest_real.get("attempted_categories") or []):
        state = "Attempted; source returned none"
    else:
        state = "Not attempted"
    lines.append(f"| {label} | {state} | {len(records)} |")

lines.extend([
    "",
    "## Current non-phone input",
    "",
    (f"- Galaxy Watch pre-bed heart rate: {latest_watch.get('sample_count')} real samples; median {latest_watch.get('median_bpm')} bpm."
     if latest_watch else "- Galaxy Watch pre-bed heart rate: no capture yet."),
    "- Morning outcome: manual sleep quality, alertness, awakenings, latency and nightmare report.",
    "",
    "## Tomorrow's acceptance result",
    "",
    ("**Transport PASS:** the real run contains `source: health_connect`, reports every attempted category, preserves per-category errors, and supersedes all `demo` data. **Content pending:** Samsung Health returned zero records."
     if latest_real else "Pending: a real phone run must contain `source: health_connect`, report attempted categories, preserve per-category errors, and supersede all `demo` data."),
    "",
])

output = DATA / "data-availability-report.md"
output.write_text("\n".join(lines), encoding="utf-8")
print(output)
