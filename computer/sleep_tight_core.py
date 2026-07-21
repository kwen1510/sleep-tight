"""Storage, validation, and daily snapshot logic for Sleep Tight.

Only the standard library is used so the receiver can run from launchd without a
virtual environment or a package-install step.
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Iterable


SCHEMA_VERSION = 1
SUPPORTED_SOURCES = {"health_connect", "samsung_health", "watch", "demo"}
LIST_FIELDS = {
    "sleep_sessions",
    "heart_rate_samples",
    "resting_heart_rate_records",
    "steps_records",
    "exercise_sessions",
    "active_calories_records",
    "total_calories_records",
    "oxygen_saturation_samples",
    "respiratory_rate_samples",
    "skin_temperature_records",
    "floors_climbed_records",
}

# Research-derived measurement contract. `supported` means implemented now;
# `conditional` depends on the wearable/vendor writing that field; `future`
# requires a new sensor or Samsung partner SDK integration.
EXTRACTION_CONTRACT = {
    "sleep_session": {"tier": "core", "status": "supported", "field": "sleep_sessions"},
    "sleep_stages": {"tier": "context", "status": "conditional", "field": "sleep_sessions"},
    "vendor_sleep_score": {"tier": "context", "status": "conditional", "field": "sleep_sessions"},
    "daytime_heart_rate": {"tier": "core", "status": "supported", "field": "heart_rate_samples"},
    "resting_heart_rate": {"tier": "core", "status": "supported", "field": "resting_heart_rate_records"},
    "steps": {"tier": "core", "status": "supported", "field": "steps_records"},
    "exercise": {"tier": "core", "status": "supported", "field": "exercise_sessions"},
    "active_calories": {"tier": "context", "status": "supported", "field": "active_calories_records"},
    "total_calories": {"tier": "context", "status": "supported", "field": "total_calories_records"},
    "oxygen_saturation": {"tier": "context", "status": "conditional", "field": "oxygen_saturation_samples"},
    "respiratory_rate": {"tier": "context", "status": "conditional", "field": "respiratory_rate_samples"},
    "skin_temperature": {"tier": "context", "status": "conditional", "field": "skin_temperature_records"},
    "floors_climbed": {"tier": "optional", "status": "conditional", "field": "floors_climbed_records"},
    "pre_bed_heart_rate": {"tier": "core", "status": "supported", "field": "pre_bed_window"},
    "ibi_hrv": {"tier": "research", "status": "future", "reason": "Requires Samsung Health Sensor SDK partner access."},
    "wrist_movement": {"tier": "research", "status": "future", "reason": "Watch accelerometer stream is not implemented yet."},
    "raw_ppg_eda": {"tier": "research", "status": "future", "reason": "Requires Samsung Health Sensor SDK and is unnecessary for tomorrow's wellness test."},
    "subjective_check_in": {"tier": "core", "status": "supported", "field": "check_in"},
    "room_environment": {"tier": "research", "status": "future", "reason": "Requires room light, sound, and temperature sensors."},
}


def parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_health_sync(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("body must be a JSON object")
    if payload.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"schema must be {SCHEMA_VERSION}")
    if payload.get("type") != "health_sync":
        raise ValueError("type must be health_sync")
    if payload.get("source") not in SUPPORTED_SOURCES:
        raise ValueError("unsupported source")
    parse_time(payload.get("generated_at"))
    parse_time(payload.get("window_start"))
    parse_time(payload.get("window_end"))
    for name in LIST_FIELDS:
        value = payload.get(name, [])
        if not isinstance(value, list):
            raise ValueError(f"{name} must be a list")
        if len(value) > 100_000:
            raise ValueError(f"{name} is too large")
        if any(not isinstance(item, dict) for item in value):
            raise ValueError(f"{name} entries must be objects")
    permissions = payload.get("permissions", {})
    if not isinstance(permissions, dict):
        raise ValueError("permissions must be an object")
    extraction_errors = payload.get("extraction_errors", {})
    if not isinstance(extraction_errors, dict):
        raise ValueError("extraction_errors must be an object")
    attempted = payload.get("attempted_categories", [])
    if not isinstance(attempted, list) or any(not isinstance(item, str) for item in attempted):
        raise ValueError("attempted_categories must be a list of strings")
    normalized = {name: payload.get(name, []) for name in LIST_FIELDS}
    normalized.update({
        "schema": SCHEMA_VERSION,
        "type": "health_sync",
        "source": payload["source"],
        "generated_at": iso(parse_time(payload["generated_at"])),
        "window_start": iso(parse_time(payload["window_start"])),
        "window_end": iso(parse_time(payload["window_end"])),
        "permissions": permissions,
        "device": payload.get("device", {}),
        "extraction_errors": extraction_errors,
        "attempted_categories": attempted,
    })
    return normalized


def validate_checkin(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("body must be a JSON object")
    observed_at = iso(parse_time(payload.get("observed_at", iso(utc_now()))))
    result: dict[str, Any] = {"schema": 1, "type": "check_in", "observed_at": observed_at}
    for name in ("sleepiness", "tension", "mood"):
        value = payload.get(name)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 10:
                raise ValueError(f"{name} must be from 0 to 10")
            result[name] = value
    for name in ("caffeine_after_15_00", "alcohol", "illness", "pain", "late_meal"):
        value = payload.get(name)
        if value is not None:
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be true or false")
            result[name] = value
    if payload.get("note"):
        result["note"] = str(payload["note"])[:500]
    return result


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _record_time(record: dict[str, Any], *names: str) -> datetime | None:
    for name in names:
        value = record.get(name)
        if value:
            try:
                return parse_time(value)
            except (TypeError, ValueError):
                pass
    return None


def _latest(records: Iterable[dict[str, Any]], *time_names: str) -> dict[str, Any] | None:
    dated = [(stamp, item) for item in records if (stamp := _record_time(item, *time_names))]
    return max(dated, default=(None, None), key=lambda pair: pair[0])[1]


@dataclass
class SleepTightStore:
    data_dir: Path

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir = self.data_dir / "snapshots"
        self.snapshot_dir.mkdir(exist_ok=True)
        self._lock = Lock()

    def _append(self, prefix: str, event: dict[str, Any], at: datetime | None = None) -> Path:
        at = at or utc_now()
        path = self.data_dir / f"{prefix}-{at.date().isoformat()}.jsonl"
        with self._lock, path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(event, separators=(",", ":")) + "\n")
        return path

    def ingest_health(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = validate_health_sync(payload)
        event["received_at"] = iso(utc_now())
        path = self._append("health-sync", event, parse_time(event["received_at"]))
        counts = {name: len(event[name]) for name in sorted(LIST_FIELDS)}
        device = event.get("device") if isinstance(event.get("device"), dict) else {}
        correlation_id = payload.get("correlation_id") or device.get("correlation_id")
        return {"accepted": True, "source": event["source"], "stored": path.name,
                "received_at": event["received_at"],
                "correlation_id": correlation_id,
                "total_records": sum(counts.values()),
                "transport": "wifi_lan",
                "counts": counts,
                "attempted_categories": event["attempted_categories"],
                "extraction_errors": event["extraction_errors"]}

    def ingest_checkin(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = validate_checkin(payload)
        event["received_at"] = iso(utc_now())
        path = self._append("check-in", event, parse_time(event["observed_at"]))
        return {"accepted": True, "stored": path.name}

    def append_heart_rate(self, event: dict[str, Any]) -> None:
        at = _record_time(event, "observed_at", "received_at") or utc_now()
        self._append("heart-rate", event, at)

    def _read_jsonl(self, prefix: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        day = start.date()
        while day <= end.date():
            path = self.data_dir / f"{prefix}-{day.isoformat()}.jsonl"
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    try:
                        value = json.loads(line)
                        if isinstance(value, dict):
                            rows.append(value)
                    except json.JSONDecodeError:
                        continue
            day += timedelta(days=1)
        return rows

    def build_snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        now = (now or utc_now()).astimezone(timezone.utc)
        start = now - timedelta(days=8)
        syncs = self._read_jsonl("health-sync", start, now)
        checkins = self._read_jsonl("check-in", now - timedelta(days=1), now)
        watch_hr = self._read_jsonl("heart-rate", now - timedelta(hours=4), now)
        pre_bed_summaries = self._read_jsonl("pre-bed-summary", now - timedelta(days=1), now)

        # Each upload is a complete overlapping history window. Keep only the
        # newest upload from each source; combining every nightly upload would
        # count the same steps and exercise records repeatedly.
        newest_sync_by_source: dict[str, dict[str, Any]] = {}
        for sync in syncs:
            source = str(sync.get("source", "unknown"))
            previous = newest_sync_by_source.get(source)
            current_time = _record_time(sync, "generated_at", "received_at") or start
            previous_time = _record_time(previous or {}, "generated_at", "received_at") or start
            if previous is None or current_time >= previous_time:
                newest_sync_by_source[source] = sync
        if any(source != "demo" for source in newest_sync_by_source):
            newest_sync_by_source.pop("demo", None)

        records = {name: [] for name in LIST_FIELDS}
        for sync in newest_sync_by_source.values():
            for name in LIST_FIELDS:
                records[name].extend(sync.get(name, []))
        # The phone intentionally resends an overlapping history window. Remove
        # identical records so a step interval isn't counted once per nightly sync.
        for name, values in records.items():
            unique: dict[str, dict[str, Any]] = {}
            for value in values:
                identity = value.get("record_id")
                key = f"id:{identity}" if identity else json.dumps(value, sort_keys=True, separators=(",", ":"))
                unique[key] = value
            records[name] = list(unique.values())

        local_tz = datetime.now().astimezone().tzinfo or timezone.utc
        today_start = now.astimezone(local_tz).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
        sleeps = []
        for session in records["sleep_sessions"]:
            end = _record_time(session, "end_time", "end")
            if end and end <= now:
                sleeps.append((end, session))
        last_sleep = max(sleeps, default=(None, None), key=lambda pair: pair[0])[1]

        step_total = 0
        for row in records["steps_records"]:
            stamp = _record_time(row, "end_time", "time", "start_time")
            value = _finite_number(row.get("count", row.get("steps")))
            if stamp and today_start <= stamp <= now and value is not None:
                step_total += int(value)

        exercises = []
        active_minutes = 0.0
        for row in records["exercise_sessions"]:
            end = _record_time(row, "end_time", "end")
            start_time = _record_time(row, "start_time", "start")
            if end and today_start <= end <= now:
                exercises.append(row)
                if start_time:
                    active_minutes += max(0, (end - start_time).total_seconds() / 60)

        current_hr_values = []
        cutoff = now - timedelta(minutes=15)
        for row in watch_hr:
            stamp = _record_time(row, "observed_at")
            bpm = _finite_number(row.get("bpm"))
            if stamp and stamp >= cutoff and bpm is not None and 20 <= bpm <= 250:
                current_hr_values.append(bpm)

        latest_sync = _latest(newest_sync_by_source.values(), "received_at", "generated_at")
        latest_checkin = _latest(checkins, "observed_at", "received_at")
        last_exercise = _latest(exercises, "end_time", "end")
        latest_pre_bed = _latest(pre_bed_summaries, "window_end", "received_at")

        day_hr_values = []
        for row in records["heart_rate_samples"]:
            stamp = _record_time(row, "time", "observed_at")
            bpm = _finite_number(row.get("bpm"))
            if stamp and today_start <= stamp <= now and bpm is not None and 20 <= bpm <= 250:
                day_hr_values.append(bpm)
        latest_resting_hr = _latest(records["resting_heart_rate_records"], "time", "observed_at")

        def values_between(field: str, value_names: tuple[str, ...], range_start: datetime, range_end: datetime) -> list[float]:
            values: list[float] = []
            for row in records[field]:
                stamp = _record_time(row, "time", "end_time", "observed_at", "start_time")
                value = None
                for name in value_names:
                    value = _finite_number(row.get(name))
                    if value is not None:
                        break
                if stamp and range_start <= stamp <= range_end and value is not None:
                    values.append(value)
            return values

        active_calories = values_between("active_calories_records", ("kilocalories",), today_start, now)
        total_calories = values_between("total_calories_records", ("kilocalories",), today_start, now)
        floors = values_between("floors_climbed_records", ("floors",), today_start, now)
        physiology_start = now - timedelta(hours=24)
        if last_sleep:
            physiology_start = _record_time(last_sleep, "start_time", "start") or physiology_start
            physiology_end = _record_time(last_sleep, "end_time", "end") or now
        else:
            physiology_end = now
        oxygen_values = values_between("oxygen_saturation_samples", ("percentage", "spo2"), physiology_start, physiology_end)
        respiratory_values = values_between("respiratory_rate_samples", ("breaths_per_minute", "rate"), physiology_start, physiology_end)
        latest_skin = _latest(records["skin_temperature_records"], "end_time", "time", "start_time")
        skin_deltas = []
        for row in records["skin_temperature_records"]:
            for delta in row.get("deltas", []):
                if isinstance(delta, dict):
                    value = _finite_number(delta.get("celsius"))
                    if value is not None:
                        skin_deltas.append(value)

        stage_minutes: dict[str, float] = {}
        if last_sleep:
            for stage in last_sleep.get("stages", []):
                if not isinstance(stage, dict):
                    continue
                start_time = _record_time(stage, "start_time", "start")
                end_time = _record_time(stage, "end_time", "end")
                if start_time and end_time and end_time >= start_time:
                    name = str(stage.get("stage", "unknown"))
                    stage_minutes[name] = stage_minutes.get(name, 0.0) + (end_time - start_time).total_seconds() / 60
        stage_minutes = {name: round(value, 1) for name, value in stage_minutes.items()}

        sleep_summary = None
        if last_sleep:
            sleep_summary = {
                "start_time": last_sleep.get("start_time", last_sleep.get("start")),
                "end_time": last_sleep.get("end_time", last_sleep.get("end")),
                "duration_minutes": last_sleep.get("duration_minutes"),
                "score": last_sleep.get("score"),
                "stages": last_sleep.get("stages", []),
                "source": last_sleep.get("source"),
                "stage_minutes": stage_minutes,
            }

        missing = []
        if not last_sleep:
            missing.append("previous_sleep")
        if not records["steps_records"]:
            missing.append("steps")
        if not current_hr_values:
            missing.append("current_heart_rate")
        if not latest_checkin:
            missing.append("subjective_check_in")

        extraction_errors: dict[str, Any] = {}
        attempted_categories: set[str] = set()
        for sync in newest_sync_by_source.values():
            extraction_errors.update(sync.get("extraction_errors", {}))
            attempted_categories.update(sync.get("attempted_categories", []))

        coverage = {}
        for signal, definition in EXTRACTION_CONTRACT.items():
            item = dict(definition)
            field = item.get("field")
            if field in records:
                item["record_count"] = len(records[field])
                item["available"] = len(records[field]) > 0
                item["attempted"] = field in attempted_categories or not attempted_categories
                if field in extraction_errors:
                    item["error"] = extraction_errors[field]
            elif field == "pre_bed_window":
                item["available"] = latest_pre_bed is not None
                item["attempted"] = True
            elif field == "check_in":
                item["available"] = latest_checkin is not None
                item["attempted"] = True
            else:
                item["available"] = False
                item["attempted"] = False
            coverage[signal] = item

        # These two signals are optional subfields of a sleep record. A sleep
        # session alone must not make either look available.
        coverage["sleep_stages"]["available"] = any(
            isinstance(session.get("stages"), list) and bool(session["stages"])
            for session in records["sleep_sessions"]
        )
        coverage["vendor_sleep_score"]["available"] = any(
            _finite_number(session.get("score")) is not None
            for session in records["sleep_sessions"]
        )

        snapshot = {
            "schema": 1,
            "type": "daily_snapshot",
            "generated_at": iso(now),
            "timezone_note": "Aggregation uses the timestamp offsets supplied by the phone; server filenames use UTC.",
            "previous_sleep": sleep_summary,
            "today": {
                "steps": step_total if records["steps_records"] else None,
                "active_minutes": round(active_minutes, 1) if exercises else None,
                "exercise_count": len(exercises),
                "last_exercise_end": (last_exercise or {}).get("end_time", (last_exercise or {}).get("end")),
                "current_hr_median": round(statistics.median(current_hr_values), 1) if current_hr_values else None,
                "current_hr_sample_count": len(current_hr_values),
                "day_hr_median": round(statistics.median(day_hr_values), 1) if day_hr_values else None,
                "day_hr_min": round(min(day_hr_values), 1) if day_hr_values else None,
                "day_hr_max": round(max(day_hr_values), 1) if day_hr_values else None,
                "day_hr_sample_count": len(day_hr_values),
                "latest_resting_hr": (latest_resting_hr or {}).get("bpm"),
                "active_calories_kcal": round(sum(active_calories), 1) if active_calories else None,
                "total_calories_kcal": round(sum(total_calories), 1) if total_calories else None,
                "floors_climbed": round(sum(floors), 1) if floors else None,
            },
            "overnight_physiology": {
                "oxygen_median_percent": round(statistics.median(oxygen_values), 2) if oxygen_values else None,
                "oxygen_min_percent": round(min(oxygen_values), 2) if oxygen_values else None,
                "oxygen_sample_count": len(oxygen_values),
                "respiratory_rate_median": round(statistics.median(respiratory_values), 2) if respiratory_values else None,
                "respiratory_rate_sample_count": len(respiratory_values),
                "skin_temperature_baseline_celsius": (latest_skin or {}).get("baseline_celsius"),
                "skin_temperature_delta_median_celsius": round(statistics.median(skin_deltas), 3) if skin_deltas else None,
                "skin_temperature_record_count": len(records["skin_temperature_records"]),
            },
            "pre_bed_window": latest_pre_bed,
            "check_in": latest_checkin,
            "available_record_counts": {name: len(value) for name, value in sorted(records.items())},
            "extraction": {
                "attempted_categories": sorted(attempted_categories),
                "errors": extraction_errors,
                "coverage": coverage,
                "supported_available": sum(1 for value in coverage.values() if value.get("status") in {"supported", "conditional"} and value.get("available")),
                "future_count": sum(1 for value in coverage.values() if value.get("status") == "future"),
            },
            "data_freshness": {
                "latest_health_sync": (latest_sync or {}).get("received_at"),
                "health_source": (latest_sync or {}).get("source"),
                "health_sources": sorted(newest_sync_by_source),
                "test_data_only": bool(newest_sync_by_source) and set(newest_sync_by_source) == {"demo"},
                "watch_live_within_15_minutes": bool(current_hr_values),
            },
            "missing": missing,
            "confidence": "high" if len(missing) <= 1 else "medium" if len(missing) <= 3 else "low",
            "safety": "Wellness context only; do not diagnose or trigger sleep interventions from a single vital-sign change.",
        }
        dated = self.snapshot_dir / f"daily-{now.date().isoformat()}.json"
        latest = self.snapshot_dir / "latest.json"
        encoded = json.dumps(snapshot, indent=2) + "\n"
        with self._lock:
            dated.write_text(encoded, encoding="utf-8")
            latest.write_text(encoded, encoding="utf-8")
        return snapshot

    def latest_snapshot(self) -> dict[str, Any] | None:
        path = self.snapshot_dir / "latest.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
