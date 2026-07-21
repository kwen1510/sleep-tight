# Product architecture and conservative control design

## 1. Recommended local-first architecture

```text
Watch sensors
    ↓ platform health API
Watch app
    ↓ paired-device transport
Phone relay (buffer, consent, retry, clock sync)
    ↓ authenticated WSS on trusted LAN
Computer session service
    ├── event store
    ├── state estimator
    ├── safety/policy engine
    └── dashboard
          ↓ authenticated local API
Home Assistant
    ├── dimmable, colour-temperature lamp
    └── room speaker / sound machine
```

Home Assistant is a useful hardware abstraction layer: its WebSocket API supports authenticated commands and service calls, including light control. It lets the research prototype change lamp or speaker brands without rewriting the sleep controller. Keep an adapter boundary so a direct Hue/Matter implementation can replace it later.

## 2. Why the phone relay is worth keeping

The user described watch → WebSocket → computer. Direct transport is possible on some watches, but a relay provides:

- a supported paired-device channel when the watch lacks Wi-Fi;
- durable buffering when the computer sleeps or the network changes;
- a place for consent, setup, and emergency stop controls;
- less radio/CPU burden on the watch;
- certificate and credential management outside the most constrained device.

The relay should preserve original timestamps and sequence numbers. It must not turn delayed samples into apparently live triggers.

## 3. Controller layers

### Layer A: deterministic safety envelope

This layer cannot be overridden by a learned model:

- lamp off during the core sleep interval;
- no abrupt brightness or colour changes;
- hard user-defined maximum speaker level;
- no sound increase during probable sleep;
- no actuation on stale, missing, low-quality, or out-of-order data;
- rate limits and minimum dwell times;
- manual stop on phone and computer;
- default safe state on crash/disconnect: lamp off, sound fade to off;
- scheduled alarm remains functional without the watch or computer.

### Layer B: nightly schedule

An example starting policy, to be user-calibrated:

- 60–30 min before target bedtime: slowly dim to a low, warm setting;
- 30–0 min: continue dimming; optional preferred quiet audio;
- probable sleep: fade audio down/off; turn lamp fully off;
- core sleep: hold darkness and silence;
- wake window: scheduled dawn ramp; optional gentle sound at hard alarm.

These are UX defaults, not clinical prescriptions. Lux at the eye, lamp geometry, room reflectance, and speaker distance matter more than an arbitrary app percentage.

### Layer C: personalization

Once per week, choose among a small set of safe profiles based on repeated nights. A contextual bandit is possible later, but a simple randomized/crossover profile selector is easier to audit and produces better evidence. Inputs can include bedtime regularity, recent duration, ambient noise, intervention history, and morning rating. Avoid optimizing a vendor “sleep score”; it can create a feedback loop with opaque scoring logic.

## 4. WebSocket responsibilities

Use WSS with short-lived paired credentials. The session protocol needs:

- explicit schema version;
- challenge/authentication before events;
- monotonically increasing sequence numbers;
- ping/pong and reconnect with exponential backoff;
- replay protection and bounded resend queue;
- server acknowledgement of commands, separate from actuator acknowledgement;
- strict message-size and frequency limits;
- JSON schema validation;
- redacted operational logs.

WebSocket is a transport, not a guarantee of continuous delivery. The controller must work as a state machine across reconnects.

## 5. Home Assistant command example

Home Assistant exposes `/api/websocket`, authenticates with an access token, and accepts `call_service` messages. A light command is conceptually:

```json
{
  "id": 24,
  "type": "call_service",
  "domain": "light",
  "service": "turn_on",
  "target": {"entity_id": "light.bedroom"},
  "service_data": {
    "brightness_pct": 8,
    "color_temp_kelvin": 2200,
    "transition": 300
  }
}
```

Validate actual entity capabilities; not all lights support the same colour-temperature range or transitions. Use Home Assistant state-change events as acknowledgements. Reference: [Home Assistant WebSocket API](https://developers.home-assistant.io/docs/api/websocket/).

## 6. Failure-mode table

| Failure | Required response |
|---|---|
| Watch disconnects | mark state unknown; continue safe fixed schedule |
| Computer sleeps/reboots | lamp off; audio fades/off; phone shows degraded mode |
| Duplicated/replayed event | ignore by event ID/sequence |
| Stale “arousal” packet arrives | log only; never actuate |
| Lamp unreachable | no repeated flashing retries; notify next morning |
| Speaker reconnects at old volume | controller first sets safe volume, then starts audio |
| Heart rate extreme | do not diagnose or automate treatment; preserve data and show appropriate user guidance |
| User gets out of bed | optional dim path light from room motion; do not infer from HR alone |

## 7. Minimal technology choices

For a prototype, keep the computer service small: one process, SQLite, a WebSocket endpoint, an adapter for Home Assistant, and a local dashboard. A message broker, cloud microservices, and machine-learning pipeline are unnecessary until the single-user loop is reliable. Export every night to JSON/CSV so analysis is not coupled to the production database.
