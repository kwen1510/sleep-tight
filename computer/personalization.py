"""Local N-of-1 personalization engine for Sleep Tight.

The engine is deliberately deterministic and dependency-free.  It turns each
nightly snapshot into one safety-bounded experiment, joins the following
morning's outcome, and produces a transparent monthly report.  Codex can
explain the files, but the scheduled learning loop does not depend on a model
or an internet connection.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1

CONTROL = {
    "wind_down_minutes": 30,
    "light_scene": "warm_dim_low_melanopic",
    "light_fade_minutes": 30,
    "music_mode": "preferred_low_arousal",
    "music_minutes": 30,
    "music_fade_minutes": 10,
    "breathing_minutes": 0,
    "haptic_mode": "off",
}

PROFILES = {
    "control": {
        "label": "Standard wind-down",
        "changed_variable": None,
        "settings": CONTROL,
    },
    "long_light_fade": {
        "label": "Longer light fade",
        "changed_variable": "light_fade_minutes",
        "settings": {**CONTROL, "light_fade_minutes": 45},
    },
    "silence": {
        "label": "Silence instead of music",
        "changed_variable": "music_mode",
        "settings": {**CONTROL, "music_mode": "silence", "music_minutes": 0, "music_fade_minutes": 0},
    },
    "breathing": {
        "label": "Five-minute breathing cue",
        "changed_variable": "breathing_minutes",
        "settings": {**CONTROL, "breathing_minutes": 5},
    },
    "earlier_wind_down": {
        "label": "Earlier wind-down",
        "changed_variable": "wind_down_minutes",
        "settings": {**CONTROL, "wind_down_minutes": 45},
    },
}

CONTEXT_PROFILES = {
    "ready": ["control", "long_light_fade", "silence"],
    "mentally_activated": ["control", "long_light_fade", "breathing", "silence"],
    "physically_activated": ["control", "long_light_fade", "silence"],
    "under_recovered": ["control", "earlier_wind_down"],
    "low_sleep_pressure": ["control", "silence"],
    "possible_illness": ["control"],
    "unknown": ["control"],
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _parse(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def _median(values: Iterable[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return round(statistics.median(clean), 2) if clean else None


def _mean(values: Iterable[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return round(statistics.fmean(clean), 2) if clean else None


def _correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 5 or len(xs) != len(ys):
        return None
    x_mean, y_mean = statistics.fmean(xs), statistics.fmean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    return round(numerator / denominator, 3) if denominator else None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")


def _duration_score(minutes: float) -> float:
    if 420 <= minutes <= 540:
        return 100.0
    distance = 420 - minutes if minutes < 420 else minutes - 540
    return max(0.0, 100.0 - distance / 3.0)


def score_outcome(outcome: dict[str, Any]) -> tuple[float | None, dict[str, float]]:
    """Return a 0-100 wellness score and the transparent component scores."""
    candidates = {
        "subjective_sleep_quality": (_number(outcome.get("subjective_sleep_quality")), 0.40, lambda x: x * 10),
        "morning_alertness": (_number(outcome.get("morning_alertness")), 0.20, lambda x: x * 10),
        "sleep_duration": (_number(outcome.get("sleep_duration_minutes")), 0.15, _duration_score),
        "vendor_sleep_score": (_number(outcome.get("vendor_sleep_score")), 0.05, lambda x: x),
        "awakenings": (_number(outcome.get("awakenings")), 0.10, lambda x: max(0, 100 - x * 15)),
        "nightmare": (None if outcome.get("nightmare") is None else float(bool(outcome.get("nightmare"))), 0.05,
                      lambda x: 0 if x else 100),
        "sleep_latency": (_number(outcome.get("sleep_latency_minutes")), 0.05,
                          lambda x: 100 if 10 <= x <= 30 else max(0, 100 - abs(x - 20) * 2)),
    }
    components: dict[str, float] = {}
    weighted = 0.0
    total_weight = 0.0
    for name, (value, weight, transform) in candidates.items():
        if value is None:
            continue
        component = max(0.0, min(100.0, float(transform(value))))
        components[name] = round(component, 1)
        weighted += component * weight
        total_weight += weight
    return (round(weighted / total_weight, 1), components) if total_weight else (None, components)


@dataclass
class PersonalizationEngine:
    data_dir: Path

    def __post_init__(self) -> None:
        self.root = self.data_dir / "personalization"
        self.reports_dir = self.root / "reports"
        self.root.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.decisions_path = self.root / "decisions.jsonl"
        self.outcomes_path = self.root / "outcomes.jsonl"

    def decisions(self) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for row in _read_jsonl(self.decisions_path):
            night = row.get("night")
            if night:
                latest.pop(night, None)
                latest[night] = row
        return list(latest.values())

    def outcomes(self) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for row in _read_jsonl(self.outcomes_path):
            if row.get("decision_id"):
                latest[row["decision_id"]] = row
        return list(latest.values())

    def _joined(self) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        outcomes = {row["decision_id"]: row for row in self.outcomes()}
        return [(decision, outcomes[decision["decision_id"]]) for decision in self.decisions()
                if decision.get("decision_id") in outcomes
                and decision.get("eligible_for_learning", False)
                and outcomes[decision["decision_id"]].get("score") is not None]

    def _baselines(self) -> dict[str, float | None]:
        joined = self._joined()
        return {
            "current_hr": _median(_number(decision.get("signals", {}).get("current_hr_median")) for decision, _ in joined),
            "resting_hr": _median(_number(decision.get("signals", {}).get("resting_hr")) for decision, _ in joined),
            "sleep_duration": _median(_number(outcome.get("sleep_duration_minutes")) for _, outcome in joined),
            "outcome_score": _median(_number(outcome.get("score")) for _, outcome in joined),
        }

    def _signals(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        today = snapshot.get("today") or {}
        checkin = snapshot.get("check_in") or {}
        previous = snapshot.get("previous_sleep") or {}
        generated = _parse(snapshot.get("generated_at")) or _now()
        exercise_end = _parse(today.get("last_exercise_end"))
        exercise_age = ((generated - exercise_end).total_seconds() / 60) if exercise_end else None
        return {
            "previous_sleep_minutes": _number(previous.get("duration_minutes")),
            "previous_sleep_score": _number(previous.get("score")),
            "steps": _number(today.get("steps")),
            "active_minutes": _number(today.get("active_minutes")),
            "exercise_count": _number(today.get("exercise_count")),
            "minutes_since_exercise": round(exercise_age, 1) if exercise_age is not None else None,
            "current_hr_median": _number(today.get("current_hr_median")),
            "day_hr_median": _number(today.get("day_hr_median")),
            "resting_hr": _number(today.get("latest_resting_hr")),
            "sleepiness": _number(checkin.get("sleepiness")),
            "tension": _number(checkin.get("tension")),
            "mood": _number(checkin.get("mood")),
            "caffeine_after_15_00": checkin.get("caffeine_after_15_00"),
            "alcohol": checkin.get("alcohol"),
            "illness": checkin.get("illness"),
            "pain": checkin.get("pain"),
            "late_meal": checkin.get("late_meal"),
            "missing": list(snapshot.get("missing") or []),
            "source_confidence": snapshot.get("confidence", "unknown"),
            "health_source": (snapshot.get("data_freshness") or {}).get("health_source"),
        }

    def classify(self, snapshot: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
        signals = self._signals(snapshot)
        baseline = self._baselines()
        reasons: list[str] = []
        current_hr = signals["current_hr_median"]
        hr_baseline = baseline["current_hr"]
        hr_elevated = current_hr is not None and hr_baseline is not None and current_hr >= hr_baseline + 8

        if signals["illness"] is True or signals["pain"] is True:
            reasons.append("Illness or pain was reported; experimentation is paused.")
            return "possible_illness", reasons, signals
        if len(signals["missing"]) >= 3 or signals["source_confidence"] == "low":
            reasons.append("Too many required signals are missing for a reliable change.")
            return "unknown", reasons, signals
        if signals["tension"] is not None and signals["tension"] >= 7 and (hr_elevated or (signals["sleepiness"] or 0) <= 6):
            reasons.append("High self-reported tension is paired with limited settling evidence.")
            return "mentally_activated", reasons, signals
        if signals["minutes_since_exercise"] is not None and 0 <= signals["minutes_since_exercise"] <= 180:
            reasons.append("Exercise ended within the last three hours.")
            return "physically_activated", reasons, signals
        if ((signals["previous_sleep_minutes"] is not None and signals["previous_sleep_minutes"] < 390) or
                (signals["previous_sleep_score"] is not None and signals["previous_sleep_score"] < 65)):
            reasons.append("The previous sleep period was shorter or poorer than the conservative threshold.")
            return "under_recovered", reasons, signals
        if ((signals["sleepiness"] is not None and signals["sleepiness"] <= 3) or
                ((signals["steps"] or 0) < 3000 and (signals["exercise_count"] or 0) == 0 and
                 (signals["previous_sleep_minutes"] or 0) >= 420)):
            reasons.append("Current sleepiness or daytime activity suggests low sleep pressure.")
            return "low_sleep_pressure", reasons, signals
        if hr_elevated:
            reasons.append("Pre-bed heart rate is elevated, but its cause is ambiguous; use a conservative calming profile.")
            return "mentally_activated", reasons, signals
        reasons.append("No strong recovery, activation, or data-quality warning was found.")
        return "ready", reasons, signals

    def _evidence(self, context: str | None = None) -> dict[str, dict[str, Any]]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for decision, outcome in self._joined():
            if context is None or decision.get("context") == context:
                grouped[decision["profile_id"]].append(float(outcome["score"]))
        result = {}
        for profile_id in PROFILES:
            scores = grouped.get(profile_id, [])
            result[profile_id] = {
                "n": len(scores),
                "mean": round(statistics.fmean(scores), 1) if scores else None,
                "median": round(statistics.median(scores), 1) if scores else None,
            }
        return result

    def _choose_profile(self, night: str, context: str) -> tuple[str, str]:
        candidates = CONTEXT_PROFILES[context]
        if len(candidates) == 1:
            return candidates[0], "Safety path: retain the standard routine."
        contextual = self._evidence(context)
        global_evidence = self._evidence()
        safe = []
        for profile_id in candidates:
            recent = [float(outcome["score"]) for decision, outcome in self._joined()
                      if decision["profile_id"] == profile_id][-2:]
            if len(recent) < 2 or not all(score < 40 for score in recent):
                safe.append(profile_id)
        candidates = safe or ["control"]
        under_tested = [profile_id for profile_id in candidates if contextual[profile_id]["n"] < 3]
        if under_tested:
            minimum = min(contextual[profile_id]["n"] for profile_id in under_tested)
            tied = [profile_id for profile_id in under_tested if contextual[profile_id]["n"] == minimum]
            digest = hashlib.sha256(f"{night}:{context}".encode()).digest()
            selected = tied[int.from_bytes(digest[:2], "big") % len(tied)]
            return selected, "Balanced exploration: this safe option needs more comparable nights."
        ordinal = date.fromisoformat(night).toordinal()
        if ordinal % 5 == 0:
            selected = min(candidates, key=lambda profile_id: (contextual[profile_id]["n"], profile_id))
            return selected, "Scheduled exploration night to prevent premature lock-in."
        selected = max(candidates, key=lambda profile_id: (
            contextual[profile_id]["mean"] if contextual[profile_id]["mean"] is not None
            else global_evidence[profile_id]["mean"] if global_evidence[profile_id]["mean"] is not None
            else -1,
            -contextual[profile_id]["n"],
        ))
        return selected, "Personalized selection: this option currently has the best comparable outcome score."

    def plan_night(self, snapshot: dict[str, Any], night: str | None = None, force: bool = False) -> dict[str, Any]:
        night = night or datetime.now().astimezone().date().isoformat()
        date.fromisoformat(night)
        existing = next((row for row in reversed(self.decisions()) if row.get("night") == night), None)
        if existing and not force:
            return existing
        context, reasons, signals = self.classify(snapshot)
        profile_id, selection_reason = self._choose_profile(night, context)
        profile = PROFILES[profile_id]
        decision_id = hashlib.sha256(f"sleep-tight:{night}:{len(self.decisions()) if force else 0}".encode()).hexdigest()[:16]
        decision = {
            "schema": SCHEMA_VERSION,
            "type": "nightly_plan",
            "decision_id": decision_id,
            "night": night,
            "created_at": _iso(_now()),
            "context": context,
            "context_reasons": reasons,
            "signals": signals,
            "profile_id": profile_id,
            "profile_label": profile["label"],
            "changed_variable": profile["changed_variable"],
            "settings": profile["settings"],
            "selection_reason": selection_reason,
            "evidence_before_decision": self._evidence(context),
            "eligible_for_learning": signals.get("health_source") != "demo" and context != "unknown",
            "safety": {
                "one_variable_from_control": profile_id == "control" or profile["changed_variable"] is not None,
                "during_sleep_actuation": False,
                "medical_claim": False,
            },
        }
        _append_jsonl(self.decisions_path, decision)
        (self.root / "latest-plan.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
        return decision

    def record_outcome(self, night: str, *, subjective_sleep_quality: float | None = None,
                       morning_alertness: float | None = None, sleep_duration_minutes: float | None = None,
                       vendor_sleep_score: float | None = None, awakenings: int | None = None,
                       nightmare: bool | None = None, sleep_latency_minutes: float | None = None,
                       notes: str | None = None, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        decision = next((row for row in reversed(self.decisions()) if row.get("night") == night), None)
        if not decision:
            raise ValueError(f"no nightly plan exists for {night}")
        previous = (snapshot or {}).get("previous_sleep") or {}
        outcome = {
            "schema": SCHEMA_VERSION,
            "type": "morning_outcome",
            "decision_id": decision["decision_id"],
            "night": night,
            "recorded_at": _iso(_now()),
            "subjective_sleep_quality": _number(subjective_sleep_quality),
            "morning_alertness": _number(morning_alertness),
            "sleep_duration_minutes": _number(sleep_duration_minutes if sleep_duration_minutes is not None else previous.get("duration_minutes")),
            "vendor_sleep_score": _number(vendor_sleep_score if vendor_sleep_score is not None else previous.get("score")),
            "awakenings": awakenings,
            "nightmare": nightmare,
            "sleep_latency_minutes": _number(sleep_latency_minutes),
            "notes": (notes or "")[:500],
        }
        for name in ("subjective_sleep_quality", "morning_alertness"):
            value = outcome[name]
            if value is not None and not 0 <= value <= 10:
                raise ValueError(f"{name} must be from 0 to 10")
        if awakenings is not None and (isinstance(awakenings, bool) or not isinstance(awakenings, int) or awakenings < 0):
            raise ValueError("awakenings must be a non-negative integer")
        if nightmare is not None and not isinstance(nightmare, bool):
            raise ValueError("nightmare must be true or false")
        for name, maximum in (("sleep_duration_minutes", 1440), ("sleep_latency_minutes", 720),
                              ("vendor_sleep_score", 100)):
            value = outcome[name]
            if value is not None and not 0 <= value <= maximum:
                raise ValueError(f"{name} must be from 0 to {maximum}")
        score, components = score_outcome(outcome)
        if score is None:
            raise ValueError("provide at least one morning outcome measurement")
        outcome["score"] = score
        outcome["score_components"] = components
        outcome["confidence"] = "high" if subjective_sleep_quality is not None and morning_alertness is not None else "medium"
        _append_jsonl(self.outcomes_path, outcome)
        (self.root / "latest-outcome.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        return outcome

    def import_previous_sleep(self, snapshot: dict[str, Any], current_night: str | None = None) -> dict[str, Any] | None:
        """Close the newest earlier experiment from vendor sleep data, if needed.

        This makes the loop autonomous even when the user skips the morning
        questionnaire.  A later subjective submission supersedes this record.
        """
        current_night = current_night or datetime.now().astimezone().date().isoformat()
        completed = {row["decision_id"] for row in self.outcomes()}
        pending = next((row for row in reversed(self.decisions())
                        if row["night"] < current_night and row["decision_id"] not in completed), None)
        if not pending:
            return None
        previous = snapshot.get("previous_sleep") or {}
        if _number(previous.get("duration_minutes")) is None and _number(previous.get("score")) is None:
            return None
        return self.record_outcome(pending["night"], snapshot=snapshot,
                                   notes="Automatically imported from the next available completed sleep record.")

    def report(self, month: str | None = None) -> dict[str, Any]:
        month = month or datetime.now().astimezone().strftime("%Y-%m")
        datetime.strptime(month, "%Y-%m")
        joined = [(decision, outcome) for decision, outcome in self._joined() if decision["night"].startswith(month)]
        scores = [float(outcome["score"]) for _, outcome in joined]
        profile_rows = []
        control_scores = [float(outcome["score"]) for decision, outcome in joined if decision["profile_id"] == "control"]
        control_mean = statistics.fmean(control_scores) if control_scores else None
        for profile_id, profile in PROFILES.items():
            values = [float(outcome["score"]) for decision, outcome in joined if decision["profile_id"] == profile_id]
            if not values:
                continue
            mean = statistics.fmean(values)
            profile_rows.append({
                "profile_id": profile_id,
                "label": profile["label"],
                "n": len(values),
                "mean_score": round(mean, 1),
                "median_score": round(statistics.median(values), 1),
                "difference_from_control": round(mean - control_mean, 1) if control_mean is not None else None,
                "confidence": "usable" if len(values) >= 3 else "preliminary",
            })
        profile_rows.sort(key=lambda row: (-row["mean_score"], -row["n"]))

        lifestyle = []
        for factor in ("alcohol", "caffeine_after_15_00", "late_meal", "illness", "pain"):
            yes = [float(outcome["score"]) for decision, outcome in joined if decision["signals"].get(factor) is True]
            no = [float(outcome["score"]) for decision, outcome in joined if decision["signals"].get(factor) is False]
            if len(yes) >= 2 and len(no) >= 2:
                lifestyle.append({"factor": factor, "yes_n": len(yes), "no_n": len(no),
                                  "association_points": round(statistics.fmean(yes) - statistics.fmean(no), 1),
                                  "interpretation": "association_only"})
        correlations = []
        for factor in ("steps", "active_minutes", "sleepiness", "tension", "current_hr_median"):
            pairs = [(_number(decision["signals"].get(factor)), float(outcome["score"])) for decision, outcome in joined]
            pairs = [(x, y) for x, y in pairs if x is not None]
            correlation = _correlation([x for x, _ in pairs], [y for _, y in pairs])
            if correlation is not None:
                correlations.append({"factor": factor, "n": len(pairs), "correlation": correlation,
                                     "interpretation": "association_only"})
        context_results = {}
        for context in sorted({decision["context"] for decision, _ in joined}):
            rows = []
            for profile_id, profile in PROFILES.items():
                values = [float(outcome["score"]) for decision, outcome in joined
                          if decision["context"] == context and decision["profile_id"] == profile_id]
                if values:
                    rows.append({"profile_id": profile_id, "label": profile["label"], "n": len(values),
                                 "mean_score": round(statistics.fmean(values), 1)})
            rows.sort(key=lambda row: (-row["mean_score"], -row["n"]))
            context_results[context] = {
                "nights": sum(row["n"] for row in rows),
                "best_supported_profile": rows[0]["profile_id"] if rows and rows[0]["n"] >= 2 else None,
                "profiles": rows,
            }
        suggestions = []
        for row in lifestyle:
            if row["association_points"] <= -5:
                wording = {
                    "alcohol": "Test alcohol-free evenings while keeping the sleep routine constant.",
                    "caffeine_after_15_00": "Test moving the final caffeine intake earlier.",
                    "late_meal": "Test finishing the final substantial meal earlier.",
                    "illness": "Treat illness-associated nights as recovery context, not intervention failures.",
                    "pain": "Address pain context separately before judging the bedtime routine.",
                }[row["factor"]]
                suggestions.append({"basis": row["factor"], "suggestion": wording,
                                    "confidence": "association_to_test"})
        for row in correlations:
            if row["factor"] == "tension" and row["correlation"] <= -0.3:
                suggestions.append({"basis": "tension", "suggestion": "Test a consistent pre-bed decompression period on high-tension days.",
                                    "confidence": "association_to_test"})
            if row["factor"] in {"steps", "active_minutes"} and row["correlation"] >= 0.3:
                suggestions.append({"basis": row["factor"], "suggestion": "Maintain a similar daytime activity range and test timing separately.",
                                    "confidence": "association_to_test"})
        completed = len(joined)
        planned = len([row for row in self.decisions() if row["night"].startswith(month)
                       and row.get("eligible_for_learning", False)])
        report = {
            "schema": SCHEMA_VERSION,
            "type": "monthly_personalization_report",
            "month": month,
            "generated_at": _iso(_now()),
            "planned_nights": planned,
            "completed_nights": completed,
            "completion_rate": round(completed / planned, 3) if planned else 0,
            "overall": {
                "mean_outcome_score": round(statistics.fmean(scores), 1) if scores else None,
                "median_outcome_score": round(statistics.median(scores), 1) if scores else None,
                "mean_subjective_sleep_quality": _mean(_number(outcome.get("subjective_sleep_quality")) for _, outcome in joined),
                "mean_morning_alertness": _mean(_number(outcome.get("morning_alertness")) for _, outcome in joined),
                "median_sleep_duration_minutes": _median(_number(outcome.get("sleep_duration_minutes")) for _, outcome in joined),
            },
            "profile_results": profile_rows,
            "best_supported_profile": profile_rows[0]["profile_id"] if profile_rows and profile_rows[0]["n"] >= 3 else None,
            "personal_baselines": self._baselines(),
            "context_profile_results": context_results,
            "lifestyle_associations": lifestyle,
            "continuous_associations": correlations,
            "lifestyle_suggestions": suggestions,
            "context_counts": dict(sorted({context: sum(1 for decision, _ in joined if decision["context"] == context)
                                           for context in {decision["context"] for decision, _ in joined}}.items())),
            "limitations": [
                "Associations do not prove that a lifestyle factor caused the sleep outcome.",
                "Profile differences are preliminary until each option has at least three comparable nights.",
                "Consumer-watch sleep stages and scores are estimates, not clinical measurements.",
                "Missing or low-quality data are retained as unknown rather than imputed.",
            ],
        }
        json_path = self.reports_dir / f"{month}.json"
        md_path = self.reports_dir / f"{month}.md"
        html_path = self.reports_dir / f"{month}.html"
        report["files"] = {"json": str(json_path), "markdown": str(md_path), "html": str(html_path)}
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(self._markdown(report), encoding="utf-8")
        html_path.write_text(self._html(report), encoding="utf-8")
        return report

    @staticmethod
    def _markdown(report: dict[str, Any]) -> str:
        overall = report["overall"]
        lines = [
            f"# Sleep Tight personal report — {report['month']}", "",
            f"Completed outcomes: **{report['completed_nights']} / {report['planned_nights']} nights**", "",
            "## Personal sleep profile", "",
            f"- Mean outcome score: {overall['mean_outcome_score']}",
            f"- Mean subjective sleep quality: {overall['mean_subjective_sleep_quality']} / 10",
            f"- Mean morning alertness: {overall['mean_morning_alertness']} / 10",
            f"- Median sleep duration: {overall['median_sleep_duration_minutes']} minutes", "",
            "## Intervention results", "",
            "| Routine | Nights | Mean | Difference from control | Evidence |", "|---|---:|---:|---:|---|",
        ]
        for row in report["profile_results"]:
            lines.append(f"| {row['label']} | {row['n']} | {row['mean_score']} | {row['difference_from_control']} | {row['confidence']} |")
        lines += ["", "## Lifestyle associations", ""]
        if report["lifestyle_associations"]:
            for row in report["lifestyle_associations"]:
                lines.append(f"- {row['factor']}: {row['association_points']:+.1f} outcome points when present (association only).")
        else:
            lines.append("Not enough paired nights yet.")
        lines += ["", "## Continuous associations", ""]
        if report["continuous_associations"]:
            for row in report["continuous_associations"]:
                lines.append(f"- {row['factor']}: r={row['correlation']:+.3f}, n={row['n']} (association only).")
        else:
            lines.append("Not enough complete observations yet.")
        lines += ["", "## Lifestyle experiments for next month", ""]
        if report["lifestyle_suggestions"]:
            for row in report["lifestyle_suggestions"]:
                lines.append(f"- {row['suggestion']} ({row['confidence'].replace('_', ' ')})")
        else:
            lines.append("No lifestyle adjustment has enough repeated personal evidence yet; continue collecting comparable nights.")
        lines += ["", "## Interpretation limits", ""] + [f"- {item}" for item in report["limitations"]]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _html(report: dict[str, Any]) -> str:
        rows = "".join(
            f"<tr><td>{html.escape(row['label'])}</td><td>{row['n']}</td><td>{row['mean_score']}</td>"
            f"<td>{row['difference_from_control']}</td><td>{row['confidence']}</td></tr>"
            for row in report["profile_results"]
        ) or "<tr><td colspan='5'>No completed experiments yet.</td></tr>"
        lifestyle = "".join(
            f"<li><strong>{html.escape(row['factor'])}</strong>: {row['association_points']:+.1f} points when present</li>"
            for row in report["lifestyle_associations"]
        ) or "<li>Not enough paired nights yet.</li>"
        suggestions = "".join(f"<li>{html.escape(row['suggestion'])}</li>" for row in report["lifestyle_suggestions"])
        suggestions = suggestions or "<li>Continue collecting comparable nights before changing lifestyle factors.</li>"
        overall = report["overall"]
        return f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>Sleep Tight report {html.escape(report['month'])}</title><style>
body{{font:16px system-ui;line-height:1.5;max-width:980px;margin:auto;padding:32px;color:#1e293b;background:#f8fafc}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}.card,section{{background:white;padding:20px;border-radius:14px;margin:16px 0;box-shadow:0 1px 4px #0001}}
.big{{font-size:1.7rem;font-weight:700}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;border-bottom:1px solid #e2e8f0;text-align:left}}small{{color:#64748b}}
</style><body><h1>Personal sleep report</h1><p>{html.escape(report['month'])} · {report['completed_nights']} of {report['planned_nights']} outcomes completed</p>
<div class='grid'><div class='card'><small>Outcome score</small><div class='big'>{overall['mean_outcome_score']}</div></div>
<div class='card'><small>Sleep quality</small><div class='big'>{overall['mean_subjective_sleep_quality']} / 10</div></div>
<div class='card'><small>Morning alertness</small><div class='big'>{overall['mean_morning_alertness']} / 10</div></div>
<div class='card'><small>Median sleep</small><div class='big'>{overall['median_sleep_duration_minutes']} min</div></div></div>
<section><h2>Intervention results</h2><table><thead><tr><th>Routine</th><th>Nights</th><th>Mean</th><th>vs control</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Lifestyle associations</h2><ul>{lifestyle}</ul><small>Associations are not proof of causation.</small></section>
<section><h2>Experiments for next month</h2><ul>{suggestions}</ul></section>
<section><h2>Guardrails</h2><ul>{''.join(f'<li>{html.escape(item)}</li>' for item in report['limitations'])}</ul></section></body></html>"""
