# Sleep Tight demo setup

The demo has three local pieces:

1. **Galaxy Watch app** — performs a bounded 10-minute calibrated heart-rate capture at 21:55 or when Sync Data is tapped, streams readings and a summary to the Mac, then stops.
2. **Android phone app** — reads every health category the user grants through Health Connect and sends a normalized eight-day window to the Mac. Samsung Health must be allowed to share the desired categories with Health Connect.
3. **Mac receiver** — receives the watch WebSocket and phone HTTP uploads, stores local JSONL files, and produces one compact daily snapshot for Codex.

## One-command Mac setup

From Terminal:

```bash
cd "/Users/etdadmin/Desktop/Sleep Tight"
./setup-sleep-tight --time 22:05
```

If the phone and watch are already visible in `adb devices`, install both apps at the same time:

```bash
./setup-sleep-tight --time 22:05 --install-connected
```

The setup command builds both APKs, installs/restarts the Mac receiver, and leaves the Codex recommendation automation at 22:05, after the 21:55 phone sync and 10-minute watch capture have completed. It also schedules the previous month's report for 9 a.m. on the first day of each month. Re-running it is safe.

## Phone — three taps

Install and open **Sleep Tight Sync**. Leave `auto://sleep-tight` in the Mac-address box. The phone and watch builds share the `com.sleeptight` application identity so the watch can request a phone sync through Wear OS; after upgrading from the earlier prototype, reinstall both apps and grant permissions again.

1. Tap **Grant health permissions** and approve the categories you want.
2. Tap **Update vitals now**. The phone and Mac must be on the same private Wi-Fi network.
3. Leave the update time at `21:55` and tap **Save daily 9:55 p.m. update**.

For an immediate manual demonstration, tap **Update vitals now**. This exports a rolling 24-hour Health Connect window ending at the tap time.

In Health Connect, ensure Samsung Health has permission to write the categories being requested. A missing category remains explicitly missing; the app does not manufacture it.

## Watch — one schedule

Install and open **Sleep Tight HR**.

1. Grant heart-rate, background-sensor, notification, and exact-alarm permissions when prompted.
2. Leave the daily update time as `21:55` and tap **Save daily 21:55 update**.

For an immediate manual demonstration, tap **Update vitals now**. The watch captures heart rate for 10 minutes, streams it to the Mac, and requests the same 24-hour phone export. If the phone is unavailable, use its button directly.

At approximately 21:55 the watch begins a foreground 10-minute capture and the phone exports Health Connect. Codex runs on the Mac at 22:05, reads the latest application data, and writes the evening plan for light and sound. Android may delay scheduled work slightly; actual receipt timestamps remain visible on the dashboard.

## Verify without a phone or watch

```bash
python3 tools/sleep_tight_cli.py demo
python3 tools/sleep_tight_cli.py status
```

The normalized Codex input is:

```text
computer/data/snapshots/latest.json
```

Run the non-destructive readiness audit at any time:

```bash
python3 tools/tomorrow_readiness.py
```

It writes `computer/data/tomorrow-readiness.md` and keeps synthetic contract data separate from records actually received from the phone and watch.

The selected experiment and accumulated personal model are stored locally in:

```text
computer/data/personalization/latest-plan.json
computer/data/personalization/decisions.jsonl
computer/data/personalization/outcomes.jsonl
computer/data/personalization/reports/
```

## Hyper-personalization loop

Every scheduled evening, Sleep Tight first attaches the newest completed sleep record to the previous night's experiment. It then classifies the current context, selects one safety-bounded routine, and writes `latest-plan.json`. Running the job again on the same date returns the same plan rather than creating a duplicate experiment.

The safe routines compare a standard wind-down with exactly one intervention factor: a longer light fade, silence instead of approved music, a five-minute breathing cue, or an earlier wind-down. Possible illness and insufficient-data nights retain the standard routine. No routine actuates light, audio, or haptics during sleep.

The loop can learn from vendor sleep duration and score alone, but a ten-second morning rating makes the personal model substantially more useful:

```bash
python3 tools/personalize_sleep.py morning \
  --quality 8 --alertness 7 --duration 455 \
  --awakenings 1 --no-nightmare --latency 18
```

Check progress or generate a report at any time:

```bash
python3 tools/personalize_sleep.py status
python3 tools/personalize_sleep.py report --month 2026-07
```

Each monthly report is written as JSON for further analysis, Markdown for inspection, and a standalone HTML dashboard. Profile differences are labelled preliminary until at least three comparable nights exist. Lifestyle findings are labelled as associations rather than causal claims.

The local dashboard remains at [http://127.0.0.1:8766/dashboard.html](http://127.0.0.1:8766/dashboard.html).

For normal daily use, double-click `Start Sleep Tight.command`. It confirms the
login service is running and opens the dashboard. The receiver stays active if
the browser tab is closed so scheduled phone and watch uploads are not lost.
Use `Stop Sleep Tight.command` only when you deliberately want to stop accepting
uploads; starting it again restores the persistent login service.

The actual-data inspector and clearly labelled 30-night simulated report are at [http://127.0.0.1:8766/sleep-report.html](http://127.0.0.1:8766/sleep-report.html).

## API routes

All routes except the liveness check require `Authorization: Bearer <pairing-token>`.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Receiver liveness |
| `GET` | `/api/v1/status` | Watch, sync, and snapshot status |
| `POST` | `/api/v1/ingest/health` | Health Connect or Samsung-normalized upload |
| `POST` | `/api/v1/check-in` | Sleepiness, tension, and confounder check-in |
| `POST` | `/api/v1/snapshots/run` | Generate a normalized daily snapshot now |
| `GET` | `/api/v1/snapshots/latest` | Retrieve the latest snapshot |
| `GET` | `/api/v1/extraction/coverage` | Retrieve attempted, available, empty, and failed extraction categories |
| `GET` | `/api/v1/personalization/latest-plan` | Retrieve tonight's selected experiment |
| `GET` | `/api/v1/evening/sources` | Local phone/watch freshness for the dashboard |
| `POST` | `/api/v1/evening/run` | Local immediate snapshot, plan, room command, and Codex commentary job |
| `GET` | `/api/v1/evening/status?run_id=...` | Local evening-run and Codex job status |
| `GET` | `/api/v1/room-command/latest` | Local immutable command used by the wind-down scene |
| `POST` | `/api/v1/personalization/plan` | Select tonight's experiment idempotently |
| `POST` | `/api/v1/personalization/outcome` | Record or enrich a morning outcome |
| `POST` | `/api/v1/personalization/report` | Generate a monthly personal report |

The WebSocket remains on port `8765`; the authenticated HTTP API is on port `8766`. Both advertise themselves over local DNS-SD so the phone and watch can discover the Mac automatically.

## What is deliberately not automatic

- Samsung's Health Data SDK can read Samsung's 0–100 sleep score in developer mode for a local test; normal public distribution requires Samsung app registration. Health Connect works without that partnership but exposes duration and stages rather than a vendor score. The Mac ingestion schema already accepts `source: samsung_health`, so the optional adapter will not require a pipeline redesign.
- Codex treats sleep stages and sleep scores as consumer estimates.
- No light, sound, or vibration is triggered from one heart-rate change.
- The current local demo uses cleartext traffic on a trusted private LAN plus a bearer token. Before any remote or multi-user deployment, replace it with TLS and rotate the demo token.
