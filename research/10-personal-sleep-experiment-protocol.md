# Sleep Tight personal experiment protocol

Last updated: 17 July 2026

## Objective

Find the safest repeatable bedtime routine that improves the user's morning-rated sleep quality and alertness without increasing awakenings, nightmare distress, or physiological strain.

This is a general-wellness N-of-1 experiment. It does not diagnose or treat insomnia, sleep apnea, nightmare disorder, arrhythmia, or another medical condition.

## Operating model

The watch collector and deterministic safety rules run throughout the night. Codex does not improvise environmental changes while the user is asleep. After the sleep session ends, Codex analyses the completed record, combines it with the user's morning report, and recommends at most one bounded change for the following night.

Unknown, missing, contradictory, or poor-quality data always produces no automatic action.

## Access required

### Available now

- heart rate at approximately 1 Hz;
- sensor accuracy;
- watch and receiver timestamps;
- packet sequence and completeness;
- local WebSocket reception and JSONL storage; and
- session start and stop from the watch.

### Required for a credible next version

- inter-beat intervals and quality flags for short HRV summaries;
- three-axis accelerometer data or 30-second movement summaries;
- explicit session markers: wind-down start, lights-out, final wake, and stop;
- watch battery level and sensor-contact/data-completeness status;
- watch model, firmware, app, and sensor-SDK versions; and
- completed Samsung sleep summary the following morning, where permitted.

### Useful but optional

- skin-temperature trend;
- respiratory-rate estimate;
- SpO2 summary and vendor quality flags;
- calibrated bedroom light at eye level;
- calibrated sound at the pillow;
- room temperature; and
- a user-pressed nightmare marker.

### Not required

- GPS or location;
- contacts, messages, microphone, photographs, or calendar contents;
- unrestricted access to other health records; or
- continuous raw PPG if IBI and movement provide adequate signal quality.

## Morning report

Complete this before seeing the watch score:

- sleep quality, 0-10;
- morning alertness, 0-10;
- estimated time to fall asleep;
- remembered awakenings;
- nightmare: no/yes, approximate time, and distress 0-10;
- alcohol and last drink time;
- caffeine and last intake time;
- exercise type and finishing time;
- unusual stress, illness, medication change, or pain;
- bedroom disturbance: light, noise, heat, cold, or another person; and
- whether the assigned routine was followed.

## Outcomes

### Primary

- morning-rated sleep quality; and
- morning alertness.

### Secondary

- probable sleep timing and regularity;
- clean-signal sleeping heart rate relative to personal baseline;
- clean-signal IBI/HRV trend when available;
- sustained movement and probable-awakening burden;
- estimated sleep latency and remembered awakenings;
- nightmare frequency and distress;
- data completeness and battery cost; and
- adverse reactions attributed to light or sound.

Vendor sleep stages and sleep score remain exploratory.

## Experiment sequence

### Phase 0 - engineering and baseline, nights 1-4

Use the user's normal routine. Do not let physiology change light or sound.

Goals:

- confirm full-night collection and stop behaviour;
- establish the approximate sleeping-heart-rate range;
- measure packet loss, accuracy, battery cost, and disconnects;
- begin the morning report; and
- identify obvious confounders and environmental disturbances.

No personal sleep conclusion is made from one night.

### Phase 1 - fixed evening light, nights 5-10

Compare repeated blocks:

- A: normal evening routine; and
- B: low-melanopic wind-down beginning 45 minutes before lights-out, fading to darkness.

Keep music and masking unchanged. If possible, randomize the order A-B-B-A-B-A. Use at least three usable nights per condition.

### Phase 2 - music, nights 11-16

Keep the best fixed light routine. Compare:

- A: silence; and
- B: 30-45 minutes of familiar low-arousal music fading to silence.

Do not use all-night playback. Use at least three usable nights per condition.

### Phase 3 - environmental noise, only if needed

Run this phase only when intermittent environmental noise is a recorded problem. Compare source control or comfortable earplugs with silence. Test calibrated minimum-effective masking only if attenuation is insufficient. Do not deliberately introduce disruptive noise.

### Phase 4 - scheduled dawn, four to six mornings

Compare a fixed alarm with a 20-30 minute dawn ramp ending at the same hard wake time. Evaluate alertness and sleep inertia, not claimed improvement in deep or REM sleep.

### Phase 5 - conservative personalisation

Compare the best fixed profile with a Codex-selected profile drawn from the same safety-bounded options. Codex may change only one of:

- wind-down start time;
- light fade duration;
- approved low-melanopic scene;
- music on/off and approved track set;
- music fade duration; or
- dawn on/off and ramp duration.

At least three usable nights are required before changing the same variable again.

## Daily Codex analysis

1. Check sensor completeness and quality.
2. Build or update a rolling 14-28-night personal baseline.
3. Compare the completed night with the user's own baseline, not population cut-offs.
4. Separate observation from interpretation.
5. List plausible explanations such as schedule, alcohol, illness, exercise, stress, room conditions, or sensor error.
6. Score confidence as high, medium, low, or unknown.
7. Retain the current profile or recommend one bounded change.
8. Explain why that change was selected and what outcome will test it.

Example:

> Data completeness was 96%. Sleeping heart rate was above the personal baseline, movement increased, and morning sleep quality was 4/10. Alcohol and a late bedtime were recorded, so the light profile cannot be blamed. Keep the environment unchanged tonight, avoid alcohol, and return to the usual bedtime. Confidence: medium.

## Nightmare handling

A heart-rate rise is not a nightmare detector. When the user wakes and confirms a nightmare, preserve the preceding 10 minutes and following 2-5 minutes of heart rate, IBI/HRV, movement, EDA if available, SpO2, and signal quality.

No sound or light is triggered from an unconfirmed cardiac change. An optional user-confirmed recovery mode may provide a very dim safety light and brief grounding prompt, then return to darkness.

Frequent distressing nightmares are addressed during waking hours with evidence-based professional support such as imagery rehearsal therapy, not automatic REM stimulation.

## Safety and stopping rules

- no routine light during intended sleep;
- no volume increase based on heart rate;
- no all-night 40-50 dBA pink-noise default;
- no intervention when data quality is uncertain;
- stop a condition after a clear adverse reaction attributed to it;
- do not delay a required wake time for a watch-estimated stage;
- retain a manual stop for all sensing and actuation; and
- recommend clinical assessment for repeated concerning oxygen values, unusual cardiac warnings, dream enactment/injury, or frequent distressing nightmares.

## Background components

1. **Watch service:** collects approved signals and sends authenticated events.
2. **Local receiver:** validates and stores events on the Mac.
3. **Deterministic controller:** executes only scheduled, calibrated, pre-approved light and sound profiles.
4. **Night summarizer:** creates one quality-controlled session summary after Stop.
5. **Morning Codex task:** reads the summary and morning report, updates the experiment ledger, and writes the next-night recommendation.

The morning task should run after the user's usual wake time. It should not continuously sample the raw stream through an LLM overnight.
