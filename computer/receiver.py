#!/usr/bin/env python3
"""Local Sleep Tight WebSocket receiver and authenticated health ingestion API."""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit
from urllib.parse import parse_qs

from websockets.asyncio.server import serve

from personalization import PersonalizationEngine
from evening_orchestrator import EveningOrchestrator
from sleep_tight_core import SleepTightStore


def validate_event(raw: str) -> dict:
    event = json.loads(raw)
    if not isinstance(event, dict) or event.get("type") not in {"hello", "heart_rate", "pre_bed_summary"}:
        raise ValueError("unsupported event type")
    if event["type"] == "heart_rate":
        bpm = event.get("bpm")
        if not isinstance(bpm, (int, float)) or isinstance(bpm, bool) or not 20 <= bpm <= 250:
            raise ValueError("bpm must be a number from 20 to 250")
        if not isinstance(event.get("sequence"), int) or event["sequence"] < 1:
            raise ValueError("sequence must be a positive integer")
        if not isinstance(event.get("observed_at"), str):
            raise ValueError("observed_at is required")
    if event["type"] == "pre_bed_summary":
        count = event.get("sample_count")
        if not isinstance(count, int) or count < 1:
            raise ValueError("sample_count must be a positive integer")
        for name in ("window_start", "window_end"):
            if not isinstance(event.get(name), str):
                raise ValueError(f"{name} is required")
    return event


class Receiver:
    def __init__(self, token: str, data_dir: Path):
        self.token = token
        self.data_dir = data_dir
        self.dashboards = set()
        self.last_event = None
        self.store = SleepTightStore(data_dir)
        self.personalizer = PersonalizationEngine(data_dir)
        self.evening = EveningOrchestrator(data_dir, Path(__file__).resolve().parents[1])

    async def handle(self, connection):
        path = connection.request.path
        if urlsplit(path).path == "/dashboard":
            host = connection.remote_address[0] if connection.remote_address else ""
            if host not in {"127.0.0.1", "::1"}:
                await connection.close(1008, "unauthorized")
                return
            self.dashboards.add(connection)
            try:
                if self.last_event:
                    await connection.send(json.dumps(self.last_event))
                await connection.wait_closed()
            finally:
                self.dashboards.discard(connection)
            return

        supplied = connection.request.headers.get("Authorization", "")
        if supplied != f"Bearer {self.token}":
            await connection.close(1008, "unauthorized")
            return

        peer = connection.remote_address
        print(f"connected: {peer}")
        try:
            async for raw in connection:
                try:
                    event = validate_event(raw)
                except (json.JSONDecodeError, ValueError) as error:
                    print(f"rejected from {peer}: {error}")
                    continue
                event["received_at"] = datetime.now(timezone.utc).isoformat()
                if event["type"] == "hello":
                    print(f"hello: {event.get('device', 'unknown')}")
                    await connection.send('{"type":"ready","schema":1}')
                elif event["type"] == "heart_rate":
                    self.append(event)
                    self.last_event = event
                    await self.broadcast(event)
                    print(f"{event['observed_at']}  {event['bpm']:>5.1f} bpm  seq={event['sequence']}")
                else:
                    receiver_event = dict(event)
                    receiver_event["received_at"] = datetime.now(timezone.utc).isoformat()
                    self.store._append("pre-bed-summary", receiver_event)
                    await connection.send(json.dumps({
                        "schema": 1,
                        "type": "ingest_ack",
                        "source": "watch",
                        "accepted": True,
                        "received_at": receiver_event["received_at"],
                        "correlation_id": receiver_event.get("correlation_id"),
                        "sample_count": receiver_event["sample_count"],
                        "transport": "wifi_lan",
                    }, separators=(",", ":")))
                    await self.broadcast(receiver_event)
                    print(f"pre-bed summary: {event['sample_count']} samples, mean={event.get('mean_bpm')}")
        finally:
            print(f"disconnected: {peer}")

    def append(self, event: dict) -> None:
        day = datetime.now(timezone.utc).date().isoformat()
        self.store.append_heart_rate(event)

    async def broadcast(self, event: dict) -> None:
        message = json.dumps(event, separators=(",", ":"))
        for dashboard in tuple(self.dashboards):
            try:
                await dashboard.send(message)
            except Exception:
                self.dashboards.discard(dashboard)


class ApiHandler(BaseHTTPRequestHandler):
    receiver: Receiver
    token: str
    static_dir: Path

    def log_message(self, format, *args):
        print(f"api: {self.address_string()} {format % args}")

    def _is_local(self) -> bool:
        return self.client_address[0] in {"127.0.0.1", "::1"}

    def _authorized(self) -> bool:
        return self.headers.get("Authorization", "") == f"Bearer {self.token}"

    def _json(self, status: int, body: dict) -> None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 8_000_000:
            raise ValueError("body must be between 1 byte and 8 MB")
        return json.loads(self.rfile.read(length))

    def _require_auth(self) -> bool:
        if self._authorized():
            return True
        self._json(401, {"error": "unauthorized"})
        return False

    def _local_action_allowed(self) -> bool:
        if not self._is_local():
            return False
        origin = self.headers.get("Origin")
        if not origin:
            return True
        return origin in {f"http://{self.headers.get('Host')}", f"https://{self.headers.get('Host')}"}

    def do_GET(self):
        parsed_url = urlsplit(self.path)
        path = parsed_url.path
        if path == "/api/v1/health":
            self._json(200, {"ok": True, "schema": 1})
            return
        if path == "/api/v1/status":
            if not self._require_auth(): return
            self._json(200, {
                "ok": True,
                "watch_connected": self.receiver.last_event is not None,
                "last_watch_event": self.receiver.last_event,
                "latest_snapshot": self.receiver.store.latest_snapshot(),
                "personalization": {
                    "planned_nights": len(self.receiver.personalizer.decisions()),
                    "learning_eligible_nights": sum(1 for row in self.receiver.personalizer.decisions()
                                                   if row.get("eligible_for_learning", False)),
                    "completed_outcomes": len(self.receiver.personalizer.outcomes()),
                },
                "sources": self.receiver.evening.source_status(),
                "latest_evening_run": self.receiver.evening.status("latest"),
            })
            return
        if path == "/api/v1/snapshots/latest":
            if not self._require_auth(): return
            snapshot = self.receiver.store.latest_snapshot()
            self._json(200 if snapshot else 404, snapshot or {"error": "no snapshot yet"})
            return
        if path == "/api/v1/extraction/coverage":
            if not self._require_auth(): return
            snapshot = self.receiver.store.latest_snapshot()
            if not snapshot:
                self._json(404, {"error": "no snapshot yet"})
            else:
                self._json(200, snapshot.get("extraction", {}))
            return
        if path == "/api/v1/demo/room-command" and self._is_local():
            demo = self.receiver.data_dir / "demo/synthetic-room-command.json"
            self._json(200 if demo.exists() else 404,
                       json.loads(demo.read_text(encoding="utf-8")) if demo.exists() else {"error": "demo command missing"})
            return
        if path == "/api/v1/room-command/latest" and self._is_local():
            command = self.receiver.data_dir / "room-command/latest.json"
            self._json(200 if command.exists() else 404,
                       json.loads(command.read_text(encoding="utf-8")) if command.exists() else {"error": "no room command yet"})
            return
        if path == "/api/v1/room-command" and self._is_local():
            run_id = parse_qs(parsed_url.query).get("run_id", [""])[0]
            try:
                run_path = self.receiver.evening._run_path(run_id)
                command = self.receiver.data_dir / "room-command" / run_path.name
                self._json(200 if command.exists() else 404,
                           json.loads(command.read_text(encoding="utf-8")) if command.exists() else {"error": "room command not ready"})
            except ValueError as error:
                self._json(400, {"error": str(error)})
            return
        if path == "/api/v1/evening/sources" and self._is_local():
            self._json(200, self.receiver.evening.source_status())
            return
        if path == "/api/v1/evening/status" and self._is_local():
            run_id = parse_qs(parsed_url.query).get("run_id", ["latest"])[0]
            try:
                status = self.receiver.evening.status(run_id)
                self._json(200 if status else 404, status or {"error": "evening run not found"})
            except ValueError as error:
                self._json(400, {"error": str(error)})
            return
        if path == "/api/v1/personalization/latest-plan":
            if not self._require_auth(): return
            latest = self.receiver.personalizer.root / "latest-plan.json"
            self._json(200 if latest.exists() else 404,
                       json.loads(latest.read_text(encoding="utf-8")) if latest.exists() else {"error": "no plan yet"})
            return
        if path == "/adaptive_sleep_model.js" and self._is_local():
            content = (self.static_dir / "adaptive_sleep_model.js").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
            return
        static_pages = {
            "/": "dashboard.html",
            "/dashboard.html": "dashboard.html",
            "/sleep-report.html": "sleep-report.html",
            "/wind-down-demo.html": "wind-down-demo.html",
            "/platform-demo.html": "platform-demo.html",
        }
        if path in static_pages and self._is_local():
            filename = static_pages[path]
            content = (self.static_dir / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if path == "/poc-10pm.html" and self._is_local():
            content = (self.receiver.data_dir / "replays/poc-10pm.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/v1/evening/run":
            if not self._local_action_allowed():
                self._json(403, {"error": "evening runs may only be started from this Mac"})
                return
            try:
                body = self._body()
                run_id = body.get("run_id")
                self._json(202, self.receiver.evening.run(run_id, start_codex=True))
            except (json.JSONDecodeError, ValueError) as error:
                self._json(400, {"error": str(error)})
            except Exception as error:
                print(f"evening run error: {error}")
                self._json(500, {"error": "could not build evening plan"})
            return
        if not self._require_auth(): return
        try:
            body = self._body()
            if path == "/api/v1/ingest/health":
                result = self.receiver.store.ingest_health(body)
                self._json(202, result)
            elif path == "/api/v1/check-in":
                self._json(202, self.receiver.store.ingest_checkin(body))
            elif path == "/api/v1/snapshots/run":
                self._json(200, self.receiver.store.build_snapshot())
            elif path == "/api/v1/personalization/plan":
                snapshot = self.receiver.store.latest_snapshot() or self.receiver.store.build_snapshot()
                self._json(200, self.receiver.personalizer.plan_night(snapshot, body.get("night"), bool(body.get("force"))))
            elif path == "/api/v1/personalization/outcome":
                allowed = {"subjective_sleep_quality", "morning_alertness", "sleep_duration_minutes",
                           "vendor_sleep_score", "awakenings", "nightmare", "sleep_latency_minutes", "notes"}
                values = {name: body[name] for name in allowed if name in body}
                self._json(202, self.receiver.personalizer.record_outcome(body.get("night", ""), **values))
            elif path == "/api/v1/personalization/report":
                self._json(200, self.receiver.personalizer.report(body.get("month")))
            else:
                self._json(404, {"error": "not found"})
        except (json.JSONDecodeError, ValueError) as error:
            self._json(400, {"error": str(error)})
        except Exception as error:
            print(f"api error: {error}")
            self._json(500, {"error": "internal error"})


async def run(args) -> None:
    receiver = Receiver(args.token, args.data_dir)
    ApiHandler.receiver = receiver
    ApiHandler.token = args.token
    ApiHandler.static_dir = Path(__file__).parent
    dashboard_server = ThreadingHTTPServer((args.api_host, args.api_port), ApiHandler)
    Thread(target=dashboard_server.serve_forever, daemon=True).start()
    advertiser = None
    if shutil.which("dns-sd"):
        advertiser = subprocess.Popen(
            ["dns-sd", "-R", "Sleep Tight", "_sleeptight._tcp", "local", str(args.port), "v=1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        api_advertiser = subprocess.Popen(
            ["dns-sd", "-R", "Sleep Tight API", "_sleeptight-api._tcp", "local", str(args.api_port), "v=1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    else:
        api_advertiser = None
    try:
        async with serve(receiver.handle, args.host, args.port, max_size=4096, ping_interval=20, ping_timeout=20):
            print(f"watch WebSocket: ws://{args.host}:{args.port}")
            print(f"health API: http://{args.api_host}:{args.api_port}/api/v1")
            print(f"dashboard: http://127.0.0.1:{args.api_port}/dashboard.html")
            print("discovery: _sleeptight._tcp.local")
            print(f"writing to {args.data_dir.resolve()}")
            await asyncio.get_running_loop().create_future()
    finally:
        dashboard_server.shutdown()
        if advertiser:
            advertiser.terminate()
        if api_advertiser:
            api_advertiser.terminate()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--api-host", default="0.0.0.0")
    parser.add_argument("--api-port", type=int, default=8766)
    parser.add_argument("--token", default=os.environ.get("SLEEP_TIGHT_TOKEN"))
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parent / "data")
    args = parser.parse_args()
    if not args.token:
        parser.error("pass --token or set SLEEP_TIGHT_TOKEN")
    return args


if __name__ == "__main__":
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        pass
