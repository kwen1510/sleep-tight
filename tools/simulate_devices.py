#!/usr/bin/env python3
"""Send clearly labelled synthetic phone and watch data to the live Mac receiver."""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from websockets.asyncio.client import connect

from test_full_pipeline import payload as complete_phone_payload


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "computer/config.json").read_text(encoding="utf-8"))
TOKEN = CONFIG["token"]
HTTP_BASE = "http://127.0.0.1:8766"
WATCH_URL = "ws://127.0.0.1:8765"


def post(path: str, body: dict) -> dict:
    request = Request(
        HTTP_BASE + path,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def phone_payload(simulation_id: str) -> dict:
    body = complete_phone_payload()
    body["device"] = {
        "platform": "simulated_android_phone",
        "simulation": True,
        "simulation_id": simulation_id,
        "correlation_id": simulation_id,
        "note": "Synthetic transport test; not a real health measurement",
    }
    return body


async def send_watch(simulation_id: str, samples: int, interval: float) -> dict:
    start = datetime.now(timezone.utc).replace(microsecond=0)
    values = [72, 71, 71, 70, 69, 69, 68, 67, 67, 66, 66, 65][:samples]
    async with connect(
        WATCH_URL,
        additional_headers={"Authorization": f"Bearer {TOKEN}"},
        open_timeout=10,
    ) as socket:
        await socket.send(json.dumps({
            "schema": 1,
            "type": "hello",
            "device": "simulated-galaxy-watch",
            "simulated": True,
            "simulation_id": simulation_id,
        }))
        ready = json.loads(await asyncio.wait_for(socket.recv(), timeout=5))
        for sequence, bpm in enumerate(values, 1):
            observed = start + timedelta(seconds=sequence)
            await socket.send(json.dumps({
                "schema": 1,
                "type": "heart_rate",
                "sequence": sequence,
                "observed_at": observed.isoformat(),
                "bpm": bpm,
                "accuracy": 3,
                "simulated": True,
                "simulation_id": simulation_id,
                "correlation_id": simulation_id,
                "capture_mode": "manual_60_second",
            }))
            if interval:
                await asyncio.sleep(interval)
        await socket.send(json.dumps({
            "schema": 1,
            "type": "pre_bed_summary",
            "window_start": start.isoformat(),
            "window_end": (start + timedelta(minutes=10)).isoformat(),
            "sample_count": len(values),
            "min_bpm": min(values),
            "max_bpm": max(values),
            "mean_bpm": round(sum(values) / len(values), 1),
            "median_bpm": sorted(values)[len(values) // 2],
            "scheduled": True,
            "manual": True,
            "capture_mode": "manual_60_second",
            "simulated": True,
            "simulation_id": simulation_id,
            "correlation_id": simulation_id,
        }))
        await asyncio.sleep(0.25)
    return {"ready": ready, "samples_sent": len(values), "summary_sent": True}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=12, choices=range(1, 13))
    parser.add_argument("--interval", type=float, default=0.03,
                        help="real seconds between simulated watch samples")
    parser.add_argument("--build-snapshot", action="store_true",
                        help="also rebuild latest.json (real sources still take priority over demo data)")
    parser.add_argument("--source", choices=("both", "phone", "watch"), default="both",
                        help="send both device paths or isolate one transport")
    args = parser.parse_args()

    simulation_id = f"sim-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"
    phone = post("/api/v1/ingest/health", phone_payload(simulation_id)) if args.source in {"both", "phone"} else None
    watch = await send_watch(simulation_id, args.samples, max(0, args.interval)) if args.source in {"both", "watch"} else None
    snapshot = post("/api/v1/snapshots/run", {}) if args.build_snapshot else None
    result = {
        "ok": True,
        "simulation_id": simulation_id,
        "synthetic_data_warning": "These records are transport-test data, not measurements.",
        "phone_http": phone,
        "watch_websocket": watch,
        "snapshot_rebuilt": snapshot is not None,
        "data_directory": str(ROOT / "computer/data"),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
