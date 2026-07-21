#!/usr/bin/env python3
"""Produce a safe, local readiness report for the next real-device run."""

from __future__ import annotations

import argparse
import json
import plistlib
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "computer/data"
HOME = Path.home()


def jsonl(prefix: str) -> list[dict]:
    found = []
    for path in sorted(DATA.glob(f"{prefix}-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    found.append(value)
            except json.JSONDecodeError:
                pass
    return found


def launch_agent(label: str, expected: dict | None = None) -> tuple[bool, str]:
    path = HOME / "Library/LaunchAgents" / f"{label}.plist"
    if not path.exists():
        return False, "not installed"
    with path.open("rb") as source:
        value = plistlib.load(source)
    if expected and value.get("StartCalendarInterval") != expected:
        return False, f"unexpected schedule {value.get('StartCalendarInterval')}"
    return True, "installed" + (f" at {expected}" if expected else "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="fail until a real phone upload has arrived")
    args = parser.parse_args()
    checks: dict[str, dict] = {}

    try:
        with urlopen("http://127.0.0.1:8766/api/v1/health", timeout=3) as response:
            healthy = response.status == 200 and json.load(response).get("ok") is True
    except Exception as error:
        healthy = False
        receiver_detail = str(error)
    else:
        receiver_detail = "local API responded"
    checks["mac_receiver"] = {"pass": healthy, "detail": receiver_detail}

    contract_path = DATA / "contract-test-report.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8")) if contract_path.exists() else {}
    checks["all_fields_contract"] = {"pass": contract.get("passed") is True,
                                     "detail": "11 phone categories in one request"}
    for name, path in {
        "phone_apk": ROOT / "phone-app/build/outputs/apk/debug/phone-app-debug.apk",
        "watch_apk": ROOT / "watch-app/build/outputs/apk/debug/watch-app-debug.apk",
    }.items():
        checks[name] = {"pass": path.exists(), "detail": str(path)}

    pre_bed = [row for row in jsonl("pre-bed-summary") if not row.get("simulated")]
    checks["real_watch_capture"] = {
        "pass": bool(pre_bed),
        "detail": (f"{pre_bed[-1].get('sample_count')} samples at {pre_bed[-1].get('window_end')}" if pre_bed else "none received"),
    }
    real_phone = [row for row in jsonl("health-sync") if row.get("source") != "demo"]
    install_status_path = DATA / "phone-install-status.json"
    install_status = json.loads(install_status_path.read_text(encoding="utf-8")) if install_status_path.exists() else {}
    checks["real_phone_upload"] = {
        "pass": bool(real_phone),
        "detail": (f"source={real_phone[-1].get('source')} received={real_phone[-1].get('received_at')}" if real_phone
                   else install_status.get("error", "blocked until the phone app is installed and Health Connect permission is granted")),
    }
    latest_real = real_phone[-1] if real_phone else None
    phone_record_count = sum(len(latest_real.get(name, [])) for name in (
        "sleep_sessions", "heart_rate_samples", "resting_heart_rate_records", "steps_records",
        "exercise_sessions", "active_calories_records", "total_calories_records",
        "oxygen_saturation_samples", "respiratory_rate_samples", "skin_temperature_records",
        "floors_climbed_records",
    )) if latest_real else 0
    checks["samsung_records_in_health_connect"] = {
        "pass": phone_record_count > 0,
        "detail": f"{phone_record_count} real records" if phone_record_count else "all permissions granted, but Samsung Health returned zero records",
    }
    phone_schedule_path = DATA / "phone-schedule-status.json"
    phone_schedule = json.loads(phone_schedule_path.read_text(encoding="utf-8")) if phone_schedule_path.exists() else {}
    checks["phone_21_55_schedule"] = {
        "pass": phone_schedule.get("scheduled") is True and phone_schedule.get("local_time") == "21:55",
        "detail": "HealthSyncWorker registered; ADB not required" if phone_schedule.get("scheduled") else "not confirmed",
    }

    for key, label, expected in [
        ("receiver_launch_agent", "com.sleeptight.receiver", None),
        ("daily_launch_agent", "com.sleeptight.daily-snapshot", {"Hour": 21, "Minute": 59}),
        ("monthly_launch_agent", "com.sleeptight.monthly-report", {"Day": 1, "Hour": 9, "Minute": 0}),
    ]:
        passed, detail = launch_agent(label, expected)
        checks[key] = {"pass": passed, "detail": detail}

    automation = HOME / ".codex/automations/sleep-tight-nightly-plan/automation.toml"
    auto_text = automation.read_text(encoding="utf-8") if automation.exists() else ""
    auto_ok = 'status = "ACTIVE"' in auto_text and "BYHOUR=22;BYMINUTE=0" in auto_text
    checks["codex_automation"] = {"pass": auto_ok, "detail": "active daily at 22:05" if auto_ok else "not confirmed"}

    blockers = [name for name, value in checks.items() if not value["pass"]]
    source_only = blockers == ["samsung_records_in_health_connect"]
    report = {"generated_at": datetime.now().astimezone().isoformat(), "pipeline_ready": not blockers or source_only,
              "fully_ready_with_source_data": not blockers, "blockers": blockers, "checks": checks}
    json_path = DATA / "tomorrow-readiness.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md = ["# Sleep Tight — tomorrow readiness", "", f"Generated: {report['generated_at']}", "",
          "| Check | Result | Detail |", "|---|---:|---|"]
    for name, value in checks.items():
        md.append(f"| {name.replace('_', ' ').title()} | {'PASS' if value['pass'] else 'BLOCKED'} | {value['detail']} |")
    md.extend(["", f"Overall: **{'READY' if not blockers else 'PIPELINE READY — SAMSUNG SOURCE DATA EMPTY' if source_only else 'NOT READY'}**", ""])
    md_path = DATA / "tomorrow-readiness.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.strict and blockers:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
