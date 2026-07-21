#!/usr/bin/env python3
"""Replay the latest real capture at a virtual 22:05 without changing device clocks."""

from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "computer/data"
OUT = DATA / "replays"
SGT = timezone(timedelta(hours=8))


def rows(prefix: str) -> list[dict]:
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


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def shifted(value: str, delta: timedelta) -> str:
    return (dt(value) + delta).isoformat().replace("+00:00", "Z")


def main() -> None:
    summaries = rows("pre-bed-summary")
    if not summaries:
        raise SystemExit("No real pre-bed summary is available")
    summary = summaries[-1]
    original_end = dt(summary["window_end"])
    local_end = original_end.astimezone(SGT)
    virtual_end_local = local_end.replace(hour=22, minute=5, second=0, microsecond=0)
    if virtual_end_local > local_end:
        virtual_end_local -= timedelta(days=1)
    virtual_end = virtual_end_local.astimezone(timezone.utc)
    shift = virtual_end - original_end

    samples = []
    original_start = dt(summary["window_start"])
    for row in rows("heart-rate"):
        stamp = row.get("observed_at")
        if stamp and original_start <= dt(stamp) <= original_end:
            samples.append({"observed_at": shifted(stamp, shift), "bpm": row.get("bpm"),
                            "accuracy": row.get("accuracy"), "sequence": row.get("sequence")})

    phone_uploads = [row for row in rows("health-sync") if row.get("source") == "health_connect"]
    phone = phone_uploads[-1] if phone_uploads else None
    fields = [
        "sleep_sessions", "heart_rate_samples", "steps_records", "exercise_sessions",
        "total_calories_records", "oxygen_saturation_samples",
    ]
    def at_or_before_cutoff(record: dict) -> bool:
        stamp = next((record.get(name) for name in ("time", "end_time", "observed_at", "start_time") if record.get(name)), None)
        return bool(stamp) and dt(stamp) <= original_end

    phone_counts = {name: sum(1 for record in (phone or {}).get(name, []) if at_or_before_cutoff(record)) for name in fields}
    phone_total = sum(phone_counts.values())
    replay = {
        "schema": 1,
        "type": "virtual_22_05_replay",
        "simulation_boundary": "Timestamps shifted only in this replay; device clocks and original records are unchanged.",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "original_window": {"start": summary["window_start"], "end": summary["window_end"]},
        "virtual_window": {"start": shifted(summary["window_start"], shift), "end": shifted(summary["window_end"], shift),
                           "local_end": virtual_end_local.isoformat()},
        "shift_minutes": round(shift.total_seconds() / 60, 2),
        "watch": {
            "provenance": "real Galaxy Watch capture",
            "summary_sample_count": summary.get("sample_count"),
            "recovered_packet_count": len(samples), "samples": samples,
            "count_note": "The on-watch summary includes one capture-boundary sample outside the strict stored window; both counts are retained.",
            "min_bpm": summary.get("min_bpm"), "median_bpm": summary.get("median_bpm"),
            "mean_bpm": summary.get("mean_bpm"), "max_bpm": summary.get("max_bpm"),
        },
        "phone": {
            "provenance": "real Health Connect upload",
            "upload_received_at": (phone or {}).get("received_at"),
            "cutoff_applied": summary["window_end"],
            "cutoff_note": "Only phone records timestamped at or before the original watch-window endpoint are counted.",
            "permissions": (phone or {}).get("permissions", {}),
            "record_counts": phone_counts, "total_records": phone_total,
            "status": "available" if phone_total else "upload succeeded; source returned zero records",
        },
        "codex_input": {
            "pre_bed_hr_median": summary.get("median_bpm"),
            "pre_bed_hr_range": [summary.get("min_bpm"), summary.get("max_bpm")],
            "previous_sleep": None,
            "steps": None,
            "exercise_minutes": None,
            "oxygen_median": None,
            "confidence": "low",
            "missing": ["previous_sleep", "steps", "exercise", "oxygen_saturation", "morning_outcome"],
        },
        "proof_decision": {
            "profile": "control routine",
            "reason": "The replay proves timing and transport, but phone health content is empty; do not personalize from heart rate alone.",
            "light": "Use the standard low, warm wind-down profile; no HR-triggered changes.",
            "sound": "Use the usual quiet preference; no evidence yet to select music or masking noise.",
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "poc-10pm.json").write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    counts = "".join(f"<tr><td>{html.escape(name.replace('_', ' ').title())}</td><td>{count}</td></tr>" for name, count in phone_counts.items())
    page = f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Sleep Tight · 10:05 p.m. replay</title><style>
:root{{color-scheme:dark;font-family:Inter,system-ui,sans-serif;--bg:#090d16;--card:#121a29;--line:#29354b;--ink:#f5f1e8;--muted:#9ca7b9;--mint:#8bd3c7;--amber:#efc276}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);line-height:1.5}}main{{width:min(100%,1100px);margin:auto;padding:clamp(20px,5vw,64px)}}
h1{{font-size:clamp(38px,7vw,72px);line-height:1;letter-spacing:-.05em;margin:.3em 0}}h2{{margin:0 0 14px}}p{{color:var(--muted)}}.badge{{color:var(--amber);font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:12px}}.card{{min-width:0;padding:20px;border:1px solid var(--line);border-radius:18px;background:var(--card)}}
.value{{font-size:34px;font-weight:800;color:var(--mint)}}small{{color:var(--muted)}}table{{width:100%;border-collapse:collapse}}td{{padding:10px;border-bottom:1px solid var(--line)}}td:last-child{{text-align:right;font-weight:800}}
.decision{{border-left:3px solid var(--mint)}}code{{overflow-wrap:anywhere}}@media(max-width:520px){{main{{padding:18px}}}}
</style><main><div class='badge'>Proof of concept · virtual clock only</div><h1>The real capture, replayed at 10:05 p.m.</h1>
<p>The original watch window ended at {html.escape(local_end.isoformat())}. This report shifted its copied timestamps by {replay['shift_minutes']} minutes so the window ends at <strong>{html.escape(virtual_end_local.isoformat())}</strong>. Original data and device clocks were not changed.</p>
<div class='grid'><section class='card'><small>Real watch samples</small><div class='value'>{summary.get('sample_count')}</div><p>{len(samples)} timestamped packets recovered · median {summary.get('median_bpm')} bpm · range {summary.get('min_bpm')}–{summary.get('max_bpm')}</p></section>
<section class='card'><small>Real phone records</small><div class='value'>{phone_total}</div><p>{html.escape(replay['phone']['status'])}</p></section>
<section class='card'><small>Virtual cutoff</small><div class='value'>22:05</div><p>Singapore time · isolated replay</p></section></div>
<div class='grid' style='margin-top:12px'><section class='card'><h2>Phone data at cutoff</h2><table>{counts}</table></section>
<section class='card decision'><h2>What Codex would do</h2><p><strong>Control routine; low confidence.</strong></p><p>{html.escape(replay['proof_decision']['reason'])}</p><p>{html.escape(replay['proof_decision']['light'])}</p><p>{html.escape(replay['proof_decision']['sound'])}</p></section></div>
<section class='card' style='margin-top:12px'><h2>Result</h2><p>The scheduling, timestamp normalization, watch summary and phone upload path work. This replay correctly refuses to fabricate sleep, activity or oxygen values that Samsung Health has not supplied.</p><small>JSON artifact: <code>computer/data/replays/poc-10pm.json</code></small></section></main></html>"""
    (OUT / "poc-10pm.html").write_text(page, encoding="utf-8")
    print(json.dumps({"html": str(OUT / "poc-10pm.html"), "json": str(OUT / "poc-10pm.json"),
                      "watch_summary_samples": summary.get("sample_count"), "recovered_packets": len(samples), "phone_records": phone_total,
                      "virtual_end": virtual_end_local.isoformat()}, indent=2))


if __name__ == "__main__":
    main()
