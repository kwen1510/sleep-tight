# Wearable sensing and platform feasibility

## 1. Signals worth collecting

| Signal | What it can support | Important limitation |
|---|---|---|
| Heart rate | personal baseline, settling, sustained arousal-like change | nonspecific; affected by illness, alcohol, temperature, medication, REM, and fit |
| Inter-beat intervals / HRV | overnight autonomic trend | PPG artifacts and vendor access; short-window HRV is unstable |
| Accelerometer | movement, probable sleep/wake, out-of-bed event | quiet wake resembles sleep |
| Respiratory rate | slow trend, quality flag | often derived from PPG; not diagnostic |
| SpO₂ | quality/anomaly context where available | intermittent, device-dependent, not a substitute for apnea testing |
| Skin temperature deviation | longitudinal context | usually relative, delayed, device-dependent |
| Vendor sleep stage | display and later comparison | proprietary, often delayed, not a real-time control truth |

Store the device-reported value, timestamp, units, sampling context, quality/confidence, and source. Never silently interpolate a gap across an intervention decision.

## 2. Apple Watch

HealthKit is permission-controlled. An active `HKWorkoutSession` can receive higher-frequency heart-rate samples and continue in the background, but this creates an obvious workout session, affects battery, allows only one workout session at a time, and may be inappropriate product behaviour for an all-night sleep app. HealthKit’s normal sleep analyses are not a guaranteed low-latency stream for automation.

Watch Connectivity offers immediate messages when the companion is reachable and queued/background transfers for eventual delivery. Apple documents `URLSessionWebSocketTask` on watchOS only for specific supported use cases; low-level networking and background execution remain constrained.

**Recommended Apple prototype path:**

`Apple Watch app → Watch Connectivity → iPhone companion → authenticated WSS → computer`

The phone buffers and retries. The computer must tolerate delay and disconnection. Prototype the actual all-night sample cadence and battery use on physical devices before committing to features.

Do not disguise sleep monitoring as a workout merely to obtain background privileges. Confirm App Review, HealthKit, and user-interface requirements for the intended use.

Official references: [HealthKit workout sessions](https://developer.apple.com/documentation/healthkit/running-workout-sessions), [Watch Connectivity](https://developer.apple.com/documentation/WatchConnectivity), [data transfer sample](https://developer.apple.com/documentation/WatchConnectivity/transferring-data-with-watch-connectivity), and [watchOS networking technote](https://developer.apple.com/documentation/Technotes/tn3135-low-level-networking-on-watchOS).

## 3. Wear OS

Health Services is the preferred sensor layer on Wear OS 3+. It exposes:

- `PassiveMonitoringClient` for long-running, relatively infrequent background updates;
- `MeasureClient` for short-lived rapid measurements while the user is engaged;
- `ExerciseClient` for an app-owned active exercise.

Passive heart-rate readings may be batched at unpredictable intervals, so passive monitoring cannot promise second-level reactions. Permissions vary by OS/API target; current guidance uses `READ_HEART_RATE` and, for newer background use, `READ_HEALTH_DATA_IN_BACKGROUND`.

Wear OS can access HTTP/TCP/UDP networking directly, with the network often proxied through the phone over Bluetooth. Doze and network transitions still make a permanent socket fragile. For watch-to-phone communication, the Data Layer is appropriate; it is not a general network API.

**Recommended Wear OS prototype path:**

`Wear OS app → Data Layer → Android companion → authenticated WSS → computer`

A direct watch-to-computer socket can be an advanced mode, but the phone relay is easier to secure, observe, buffer, and support.

Official references: [Health Services overview](https://developer.android.com/health-and-fitness/health-services), [passive monitoring](https://developer.android.com/health-and-fitness/health-services/monitor-background), [permissions](https://developer.android.com/health-and-fitness/health-services/permissions), [Data Layer client choice](https://developer.android.com/training/wearables/data/client-types), and [direct networking](https://developer.android.com/training/wearables/data/network-communication).

## 4. Latency classes

Design the product around explicit latency classes:

| Class | Target | Suitable actions |
|---|---:|---|
| immediate | <2 s, best effort | dashboard display; never safety-critical |
| near-real-time | 5–60 s | coarse settling/arousal trends, if data quality is high |
| delayed | minutes | state summary and logging |
| next-morning | hours | sleep-stage import, nightly report, model update |

Lighting fades and sound-policy changes do not need millisecond timing. EEG phase-locked stimulation does, which is another reason it is outside the watch MVP.

## 5. Data schema

Use an append-only event envelope:

```json
{
  "schema": 1,
  "event_id": "uuid",
  "session_id": "random-night-id",
  "source": "apple_watch",
  "observed_at": "2026-07-14T23:41:12.345+08:00",
  "received_at": "2026-07-14T23:41:14.102+08:00",
  "type": "heart_rate",
  "value": 57.0,
  "unit": "count/min",
  "quality": "good",
  "sequence": 812
}
```

Add separate `command`, `command_ack`, `environment`, and `user_report` events. Clock offset, end-to-end delay, drop rate, reconnects, battery, and actuator acknowledgements are research variables, not just engineering logs.

## 6. State estimation

Start with an interpretable finite-state model:

`pre-bed → settling → probable asleep → possible arousal → waking → complete`

Require sustained evidence and hysteresis. For example, movement plus a persistent heart-rate departure might raise `possible_arousal`; neither signal alone should trigger a disruptive response. Record `unknown` when packets or quality are insufficient. Only a validated later model should add N1/N2/N3/REM, and even then its posterior probability should be stored rather than collapsing uncertainty to a label.
