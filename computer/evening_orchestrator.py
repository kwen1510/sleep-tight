"""Immediate evening-plan orchestration and optional Codex commentary."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from personalization import PersonalizationEngine
from sleep_tight_core import SleepTightStore


RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


class EveningOrchestrator:
    def __init__(self, data_dir: Path, project_root: Path, *, enable_codex: bool = True):
        self.data_dir = data_dir
        self.project_root = project_root
        self.store = SleepTightStore(data_dir)
        self.personalizer = PersonalizationEngine(data_dir)
        self.root = data_dir / "evening"
        self.runs = self.root / "runs"
        self.room = data_dir / "room-command"
        self.recommendations = data_dir / "recommendations"
        self.inputs = self.root / "inputs"
        self.decision_schema = project_root / "computer" / "codex-evening-decision.schema.json"
        for path in (self.runs, self.room, self.recommendations, self.inputs):
            path.mkdir(parents=True, exist_ok=True)
        self.enable_codex = enable_codex
        self._lock = Lock()
        self._codex_running = False

    def _read_rows(self, prefix: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted(self.data_dir.glob(f"{prefix}-*.jsonl"))[-3:]:
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                    if isinstance(row, dict):
                        rows.append(row)
                except json.JSONDecodeError:
                    continue
        return rows

    @staticmethod
    def _latest(rows: list[dict[str, Any]], *fields: str) -> dict[str, Any] | None:
        dated = []
        for row in rows:
            stamp = next((_parse(row.get(name)) for name in fields if _parse(row.get(name))), None)
            if stamp:
                dated.append((stamp, row))
        return max(dated, default=(None, None), key=lambda pair: pair[0])[1]

    @staticmethod
    def _device_metadata(row: dict[str, Any] | None) -> tuple[bool, str | None]:
        row = row or {}
        device = row.get("device") if isinstance(row.get("device"), dict) else {}
        simulated = bool(row.get("simulated") or device.get("simulation") or row.get("source") == "demo")
        correlation = row.get("correlation_id") or row.get("simulation_id") or device.get("correlation_id") or device.get("simulation_id")
        return simulated, str(correlation) if correlation else None

    def source_status(self, now: datetime | None = None) -> dict[str, Any]:
        now = now or _now()
        phone = self._latest(self._read_rows("health-sync"), "received_at", "generated_at")
        watch = self._latest(self._read_rows("pre-bed-summary"), "received_at", "window_end")
        phone_simulated, phone_correlation = self._device_metadata(phone)
        watch_simulated, watch_correlation = self._device_metadata(watch)

        def item(row: dict[str, Any] | None, simulated: bool, correlation: str | None, field: str) -> dict[str, Any]:
            stamp = _parse((row or {}).get("received_at") or (row or {}).get(field))
            age = round((now - stamp).total_seconds()) if stamp else None
            counts = {}
            if row and row.get("type") == "health_sync":
                counts = {name: len(value) for name, value in row.items() if isinstance(value, list) and name.endswith(("_records", "_samples", "_sessions"))}
            elif row and row.get("type") == "pre_bed_summary":
                counts = {"heart_rate_samples": int(row.get("sample_count") or 0)}
            return {
                "available": row is not None,
                "received_at": _iso(stamp) if stamp else None,
                "age_seconds": age,
                "fresh": age is not None and 0 <= age <= 15 * 60,
                "simulated": simulated,
                "correlation_id": correlation,
                "counts": counts,
                "transport": "wifi_lan",
            }

        result = {
            "checked_at": _iso(now),
            "freshness_threshold_seconds": 900,
            "transport": "wifi_lan",
            "automation": {
                "watch": {"time": "21:55", "precision": "exact", "action": "10-minute calibrated heart-rate capture and Wi-Fi upload"},
                "phone": {"time": "21:55", "precision": "background", "action": "Health Connect export; Android may delay slightly"},
                "snapshot": {"time": "22:05", "precision": "scheduled", "action": "Mac consolidates received records"},
                "codex": {"time": "22:05", "precision": "scheduled", "action": "Mac creates the evening recommendation"},
            },
            "phone": item(phone, phone_simulated, phone_correlation, "generated_at"),
            "watch": item(watch, watch_simulated, watch_correlation, "window_end"),
        }
        result["fresh_source_count"] = sum(1 for name in ("phone", "watch") if result[name]["fresh"])
        result["missing_or_stale"] = [name for name in ("phone", "watch") if not result[name]["fresh"]]
        return result

    def _run_path(self, run_id: str) -> Path:
        if not RUN_ID.fullmatch(run_id):
            raise ValueError("run_id must contain only letters, numbers, dots, dashes, or underscores")
        return self.runs / f"{run_id}.json"

    def _write_status(self, status: dict[str, Any]) -> None:
        path = self._run_path(status["run_id"])
        encoded = json.dumps(status, indent=2) + "\n"
        path.write_text(encoded, encoding="utf-8")
        latest = self.root / "latest.json"
        current = json.loads(latest.read_text(encoding="utf-8")) if latest.exists() else None
        if current is None or current.get("run_id") == status["run_id"] or status.get("created_at", "") >= current.get("created_at", ""):
            latest.write_text(encoded, encoding="utf-8")

    def status(self, run_id: str) -> dict[str, Any] | None:
        path = self.root / "latest.json" if run_id == "latest" else self._run_path(run_id)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    @staticmethod
    def _fallback_decision(plan: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
        settings = plan.get("settings") or {}
        missing = list(sources.get("missing_or_stale") or [])
        return {
            "profile_label": plan.get("profile_label") or "Conservative warm wind-down",
            "light_start_percent": 32,
            "fade_minutes": max(20, min(int(settings.get("wind_down_minutes") or 30), 60)),
            "sound_profile": "low_arousal_instrumental",
            "sound_start_percent": 16,
            "tempo_bpm": 64,
            "confidence": "low" if missing else "medium",
            "decision_reason": plan.get("selection_reason") or "Conservative control profile.",
            "evidence_used": list(plan.get("context_reasons") or ["Deterministic control profile"]),
            "missing_data": missing,
        }

    @staticmethod
    def _validate_codex_decision(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("Codex decision must be a JSON object")
        profiles = {"low_arousal_instrumental", "pink_noise", "brown_noise", "ocean"}
        profile = value.get("sound_profile")
        if profile not in profiles:
            raise ValueError("Codex selected an unsupported sound profile")

        def number(name: str, low: int, high: int) -> int:
            raw = value.get(name)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                raise ValueError(f"Codex decision field {name} must be numeric")
            return max(low, min(int(round(raw)), high))

        def strings(name: str, maximum: int) -> list[str]:
            raw = value.get(name)
            if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
                raise ValueError(f"Codex decision field {name} must be a string list")
            return [item.strip()[:160] for item in raw[:maximum] if item.strip()]

        label = value.get("profile_label")
        reason = value.get("decision_reason")
        confidence = value.get("confidence")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("Codex decision is missing a profile label")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Codex decision is missing its reasoning")
        if confidence not in {"low", "medium", "high"}:
            raise ValueError("Codex decision has invalid confidence")
        evidence = strings("evidence_used", 5)
        if not evidence:
            raise ValueError("Codex decision must identify evidence used")
        return {
            "profile_label": label.strip()[:80],
            "light_start_percent": number("light_start_percent", 24, 42),
            "fade_minutes": number("fade_minutes", 20, 60),
            "sound_profile": profile,
            "sound_start_percent": number("sound_start_percent", 14, 22),
            "tempo_bpm": number("tempo_bpm", 55, 72),
            "confidence": confidence,
            "decision_reason": reason.strip()[:500],
            "evidence_used": evidence,
            "missing_data": strings("missing_data", 8),
        }

    def _room_command(self, run_id: str, plan: dict[str, Any], snapshot: dict[str, Any], sources: dict[str, Any], decision: dict[str, Any], *, generated_by: str) -> dict[str, Any]:
        local_now = datetime.now().astimezone().replace(second=0, microsecond=0)
        fade = decision["fade_minutes"]
        lights_out = local_now + timedelta(minutes=fade)
        missing = list(sources["missing_or_stale"])
        return {
            "schema_version": 1,
            "type": "room_command",
            "data_status": "synthetic_input" if sources["phone"]["simulated"] or sources["watch"]["simulated"] else "personal_plan",
            "run_id": run_id,
            "decision_id": plan.get("decision_id"),
            "generated_by": generated_by,
            "generated_at": _iso(_now()),
            "confidence": decision["confidence"],
            "missing_or_stale_sources": missing,
            "warning": "Conservative plan generated with incomplete inputs." if missing else None,
            "schedule": {
                "wind_down_start": local_now.strftime("%H:%M"),
                "demo_refresh_start": local_now.strftime("%H:%M"),
                "demo_minutes_per_second": round(1 / 60, 8),
                "lights_out": lights_out.strftime("%H:%M"),
                "duration_minutes": fade,
            },
            "light": {
                "profile": "warm_amber_fade",
                "start_rgb": [255, 169, 92],
                "end_rgb": [255, 104, 58],
                "start_percent": decision["light_start_percent"],
                "end_percent": 0,
                "curve": "ease_out",
            },
            "sound": {
                "profile": decision["sound_profile"],
                "tempo_bpm": decision["tempo_bpm"],
                "start_percent": decision["sound_start_percent"],
                "end_percent": 0,
                "fade_minutes": fade,
                "stop_at_lights_out": True,
                "audibility_note": "Web Audio gain target; actual loudness depends on the Mac speaker setting.",
            },
            "plan": {
                "profile_id": plan.get("profile_id"),
                "profile_label": decision["profile_label"],
                "context": plan.get("context"),
                "reasons": decision["evidence_used"],
                "selection_reason": decision["decision_reason"],
                "codex_missing_data": decision["missing_data"],
            },
            "safety": {
                "simulation_only": True,
                "browser_percent_is_not_dba": True,
                "screen_output_is_not_melanopic_edi": True,
                "codex_decision_schema_validated": generated_by.startswith("Codex"),
                "command_is_immutable_after_scene_start": True,
            },
        }

    def run(self, requested_run_id: str | None = None, *, start_codex: bool = True) -> dict[str, Any]:
        run_id = requested_run_id or f"evening-{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
        path = self._run_path(run_id)
        with self._lock:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
            sources = self.source_status()
            snapshot = self.store.build_snapshot()
            night = datetime.now().astimezone().date().isoformat()
            self.personalizer.import_previous_sleep(snapshot, night)
            plan = self.personalizer.plan_night(snapshot, night, force=True)
            if sources["phone"]["simulated"] or sources["watch"]["simulated"]:
                plan["eligible_for_learning"] = False
                plan.setdefault("safety", {})["synthetic_input_excluded"] = True
                with self.personalizer.decisions_path.open("a", encoding="utf-8") as output:
                    output.write(json.dumps(plan, separators=(",", ":"), sort_keys=True) + "\n")
                (self.personalizer.root / "latest-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            context = {
                "schema": 1,
                "run_id": run_id,
                "created_at": _iso(_now()),
                "sources": sources,
                "snapshot": snapshot,
                "deterministic_baseline_for_comparison_only": plan,
                "recent_decisions": self.personalizer.decisions()[-10:],
                "wellness_only": True,
            }
            input_path = self.inputs / f"{run_id}.json"
            input_path.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
            status = {
                "schema": 1,
                "type": "evening_run",
                "run_id": run_id,
                "created_at": _iso(_now()),
                "state": "codex_deciding" if start_codex and self.enable_codex else "scene_ready",
                "sources": sources,
                "snapshot": "snapshots/latest.json",
                "plan": "personalization/latest-plan.json",
                "decision_context": f"evening/inputs/{run_id}.json",
                "room_command": None,
                "scene_url": None,
                "codex": {"state": "pending" if start_codex and self.enable_codex else "disabled"},
            }
            if not (start_codex and self.enable_codex):
                decision = self._fallback_decision(plan, sources)
                command = self._room_command(run_id, plan, snapshot, sources, decision, generated_by="Deterministic test fallback")
                command_path = self.room / f"{run_id}.json"
                command_path.write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
                (self.room / "latest.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
                status["room_command"] = f"room-command/{run_id}.json"
                status["scene_url"] = f"/wind-down-demo.html?run_id={run_id}"
            self._write_status(status)
            if start_codex and self.enable_codex:
                self._start_codex(run_id)
            return status

    def _start_codex(self, run_id: str) -> None:
        if self._codex_running:
            status = self.status(run_id)
            if status:
                status["codex"] = {"state": "queued", "message": "Another commentary job is running."}
                self._write_status(status)
            return
        self._codex_running = True
        Thread(target=self._codex_worker, args=(run_id,), daemon=True).start()

    def _codex_worker(self, run_id: str) -> None:
        status = self.status(run_id) or {"run_id": run_id}
        try:
            executable = shutil.which("codex")
            if not executable:
                executable = next((str(path) for path in (
                    Path("/opt/homebrew/bin/codex"),
                    Path("/usr/local/bin/codex"),
                    Path.home() / ".local/bin/codex",
                ) if path.exists()), None)
            if not executable:
                raise RuntimeError("Codex CLI is not installed")
            status["codex"] = {"state": "running", "started_at": _iso(_now())}
            self._write_status(status)
            context_path = self.data_dir / status["decision_context"]
            context = json.loads(context_path.read_text(encoding="utf-8"))
            prompt = (
                "You are the decision-maker for tonight's Sleep Tight wellness wind-down. Use only the JSON context "
                "provided on stdin and the research protocol at research/10-personal-sleep-experiment-protocol.md. "
                "The deterministic baseline is comparison evidence, not the decision. Choose the final bounded light "
                "and background-sound profile yourself. Prefer low-arousal instrumental music unless masking noise is "
                "better supported by this person's available history. The sound must remain audible in the background, "
                "so never choose silence and keep the schema's 14–22 percent gain range. Do not diagnose, infer "
                "nightmares, react to a single vital, edit files, browse, or call external tools. Return only the JSON "
                "required by the supplied output schema."
            )
            result = subprocess.run(
                [executable, "exec", "--ephemeral", "--skip-git-repo-check", "--ignore-rules",
                 "-s", "read-only", "--output-schema", str(self.decision_schema),
                 "-C", str(self.project_root), prompt],
                input=json.dumps(context, separators=(",", ":")), capture_output=True, text=True,
                timeout=600, check=False,
            )
            if result.returncode:
                raise RuntimeError((result.stderr or result.stdout or f"Codex exited {result.returncode}")[-1200:])
            text = result.stdout.strip()
            if not text:
                raise RuntimeError("Codex returned no decision")
            decision = self._validate_codex_decision(json.loads(text))
            dated = self.recommendations / f"{datetime.now().astimezone():%Y-%m-%d}-{run_id}.json"
            dated.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
            (self.recommendations / "latest.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
            plan = context["deterministic_baseline_for_comparison_only"]
            command = self._room_command(run_id, plan, context["snapshot"], context["sources"], decision, generated_by="Codex constrained decision")
            command_path = self.room / f"{run_id}.json"
            command_path.write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
            (self.room / "latest.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
            status = self.status(run_id) or status
            status["state"] = "scene_ready"
            status["room_command"] = f"room-command/{run_id}.json"
            status["scene_url"] = f"/wind-down-demo.html?run_id={run_id}"
            status["codex"] = {"state": "complete", "completed_at": _iso(_now()), "file": str(dated.relative_to(self.data_dir)), "decision": decision}
        except subprocess.TimeoutExpired:
            status = self.status(run_id) or status
            status["state"] = "codex_error"
            status["codex"] = {"state": "timeout", "message": "Codex decision exceeded ten minutes; no scene was started."}
        except Exception as error:
            status = self.status(run_id) or status
            status["state"] = "codex_error"
            status["codex"] = {"state": "error", "message": str(error)[:1200]}
        finally:
            self._write_status(status)
            self._codex_running = False
            queued = []
            for path in self.runs.glob("*.json"):
                try:
                    candidate = json.loads(path.read_text(encoding="utf-8"))
                    if (candidate.get("codex") or {}).get("state") == "queued":
                        queued.append(candidate)
                except (json.JSONDecodeError, OSError):
                    continue
            if queued:
                next_run = max(queued, key=lambda item: item.get("created_at", ""))
                self._start_codex(next_run["run_id"])
