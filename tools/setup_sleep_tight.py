#!/usr/bin/env python3
"""One-command setup for the Sleep Tight Mac receiver and Android APKs."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import secrets
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPUTER = ROOT / "computer"
CONFIG = COMPUTER / "config.json"


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(command))
    return subprocess.run(command, cwd=ROOT, check=check, text=True)


def save_config(token: str, time_value: str) -> None:
    CONFIG.write_text(json.dumps({"token": token, "daily_time": time_value}, indent=2) + "\n", encoding="utf-8")
    os.chmod(CONFIG, 0o600)


def launch_agent(label: str, arguments: list[str], stdout: Path, calendar: dict | None = None) -> dict:
    result = {
        "Label": label,
        "ProgramArguments": arguments,
        "WorkingDirectory": str(ROOT),
        "StandardOutPath": str(stdout),
        "StandardErrorPath": str(stdout.with_name(stdout.stem + "-error.log")),
        "EnvironmentVariables": {"PYTHONUNBUFFERED": "1"},
    }
    if calendar:
        result["StartCalendarInterval"] = calendar
    else:
        result.update({"RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 5})
    return result


def install_services(token: str, time_value: str) -> None:
    python = Path(shutil.which("python3") or "/usr/bin/python3").resolve()
    agents = Path.home() / "Library" / "LaunchAgents"
    agents.mkdir(parents=True, exist_ok=True)
    hour, minute = map(int, time_value.split(":"))
    codex_at = datetime(2000, 1, 1, hour, minute)
    definitions = {
        "com.sleeptight.receiver": launch_agent(
            "com.sleeptight.receiver",
            [str(python), str(COMPUTER / "receiver.py"), "--token", token],
            COMPUTER / "receiver.log",
        ),
        "com.sleeptight.daily-snapshot": launch_agent(
            "com.sleeptight.daily-snapshot",
            [str(python), str(COMPUTER / "daily_runner.py")],
            COMPUTER / "daily-snapshot.log",
            {"Hour": codex_at.hour, "Minute": codex_at.minute},
        ),
        "com.sleeptight.monthly-report": launch_agent(
            "com.sleeptight.monthly-report",
            [str(python), str(COMPUTER / "monthly_report_runner.py")],
            COMPUTER / "monthly-report.log",
            {"Day": 1, "Hour": 9, "Minute": 0},
        ),
    }
    uid = str(os.getuid())
    for label, definition in definitions.items():
        path = agents / f"{label}.plist"
        with path.open("wb") as output:
            plistlib.dump(definition, output)
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{label}"], check=False, capture_output=True)
        run(["launchctl", "bootstrap", f"gui/{uid}", str(path)])
    print(f"Mac receiver installed; the local snapshot and Codex recommendation are prepared at {time_value}.")
    print("The previous month's personal report is generated at 09:00 on the first day of each month.")


def build_apps() -> None:
    java_home = Path("/Applications/Android Studio.app/Contents/jbr/Contents/Home")
    env = os.environ.copy()
    if java_home.exists():
        env["JAVA_HOME"] = str(java_home)
    print("+ ./gradlew :phone-app:assembleDebug :watch-app:assembleDebug")
    subprocess.run([str(ROOT / "gradlew"), ":phone-app:assembleDebug", ":watch-app:assembleDebug"],
                   cwd=ROOT, env=env, check=True)


def install_connected() -> None:
    adb = shutil.which("adb")
    if not adb:
        print("ADB was not found. Open Android Studio once or add platform-tools to PATH.")
        return
    output = subprocess.check_output([adb, "devices"], text=True)
    serials = [line.split()[0] for line in output.splitlines()[1:] if line.strip().endswith("device")]
    if not serials:
        print("No Android phone or watch is connected; APKs are built and ready for later installation.")
        return
    seen_devices = set()
    for serial in serials:
        hardware_id = subprocess.check_output(
            [adb, "-s", serial, "shell", "getprop", "ro.serialno"], text=True
        ).strip() or serial
        if hardware_id in seen_devices:
            continue
        seen_devices.add(hardware_id)
        characteristics = subprocess.check_output(
            [adb, "-s", serial, "shell", "getprop", "ro.build.characteristics"], text=True
        ).strip()
        is_watch = "watch" in characteristics
        apk = ROOT / ("watch-app/build/outputs/apk/debug/watch-app-debug.apk" if is_watch
                      else "phone-app/build/outputs/apk/debug/phone-app-debug.apk")
        try:
            legacy_package = "com.sleeptight.heartrate" if is_watch else "com.sleeptight.sync"
            run([adb, "-s", serial, "uninstall", legacy_package], check=False)
            run([adb, "-s", serial, "install", "-r", str(apk)])
            print(f"Installed {'watch' if is_watch else 'phone'} app on {serial}.")
        except subprocess.CalledProcessError as error:
            print(f"Could not install the {'watch' if is_watch else 'phone'} app on {serial} (exit {error.returncode}).")
            print("The remaining connected devices will still be processed; no security restriction is bypassed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up Sleep Tight in one command")
    parser.add_argument("--time", default="22:05", help="daily Codex analysis time in 24-hour HH:MM form")
    parser.add_argument("--token", default=None)
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--install-connected", action="store_true")
    args = parser.parse_args()
    try:
        parsed = datetime.strptime(args.time, "%H:%M")
    except ValueError:
        parser.error("--time must look like 22:05")
    time_value = parsed.strftime("%H:%M")
    existing = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    token = args.token or existing.get("token") or secrets.token_hex(16)
    save_config(token, time_value)
    if not args.no_build:
        build_apps()
    install_services(token, time_value)
    if args.install_connected:
        install_connected()
    print("\nReady:")
    print("  Dashboard: http://127.0.0.1:8766/dashboard.html")
    print("  Latest personal plan:", COMPUTER / "data/personalization/latest-plan.json")
    print("  Monthly reports:", COMPUTER / "data/personalization/reports")
    print("  Phone APK:", ROOT / "phone-app/build/outputs/apk/debug/phone-app-debug.apk")
    print("  Watch APK:", ROOT / "watch-app/build/outputs/apk/debug/watch-app-debug.apk")
    print("  Pairing token: stored privately in computer/config.json")
    print("\nOn the phone: open Sleep Tight Sync → grant permissions → Update vitals now → save the 21:55 schedule.")
    print("On the watch: open Sleep Tight HR → save the 21:55 daily update or use the Sync Data tile.")


if __name__ == "__main__":
    main()
