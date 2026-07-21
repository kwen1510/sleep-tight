# Evidence-aligned product roadmap

## Phase 0 — decide the platform

Choose one watch ecosystem and one lamp/speaker path. The lowest-risk research stack is:

- Apple Watch + iPhone **or** Wear OS + Android, not both initially;
- phone relay;
- local computer service;
- Home Assistant;
- dimmable colour-temperature lamp;
- room speaker plus a basic sound-level calibration method.

Decision criterion: access to timestamped heart rate and motion at a sustainable overnight cadence on the exact hardware, not the number of health metrics advertised by the watch.

## Phase 1 — observability only

Build watch → phone → WSS → computer ingestion, a live dashboard, SQLite event storage, JSON/CSV export, clock/latency diagnostics, and a hard session stop. Do not actuate the bedroom from vitals yet.

Exit when repeated full nights show acceptable battery, data completeness, and reconnect behaviour.

## Phase 2 — fixed environment routine

Add Home Assistant and implement only:

- scheduled pre-bed warm dimming;
- full darkness during sleep;
- optional low-level sound that fades down/off;
- scheduled dawn and hard alarm;
- manual override and safe failure state.

Measure lux/dB(A) at the pillow. Complete the crossover in [05-validation-study.md](./05-validation-study.md).

## Phase 3 — coarse adaptive environment

Add probable-asleep and possible-arousal state estimates with uncertainty. Use them only for low-risk actions such as fading already-playing audio toward silence after stable probable sleep. Adapt profiles weekly from multiple nights and user ratings.

Do not turn on the lamp or increase sound in response to a vital spike.

## Phase 4 — broader study

Freeze hardware/software versions, preregister the protocol, obtain appropriate ethics/privacy review, and conduct a multi-person feasibility study. Test the entire product, not just the classifier. Determine whether adaptation adds value beyond the fixed routine.

## Separate research track — EEG closed loop

Only pursue phase-locked acoustic stimulation with an EEG-capable wearable, deterministic local audio timing, sleep-lab validation, and clinical/academic partnership. It should not inherit claims from the smartwatch MVP.

## Backlog priorities

### Must have

- timestamp integrity and stale-data rejection;
- safe actuator state and manual override;
- consent, delete, and export;
- physical light/sound calibration;
- device/firmware/controller version records;
- morning report before displaying wearable scores.

### Should have

- bedroom ambient light and sound sensors with local processing;
- offline-first phone queue;
- policy simulation/replay before deploying a change;
- actuator capability discovery and acknowledgements;
- per-user baseline and confidence visualization.

### Defer

- cloud accounts and social features;
- multiple watch platforms;
- arbitrary smart-home automation access;
- deep-learning sleep staging;
- automatic medical alerts;
- “AI sleep score”;
- stage-targeted light or sound.

## Go/no-go questions

1. Does the chosen watch expose data with a predictable-enough overnight cadence without abusing workout APIs?
2. Does the fixed routine improve user experience compared with baseline?
3. Does sound help specifically when environmental noise exists, or does silence perform as well?
4. Does adaptation beat the fixed best profile?
5. Can the intended claims remain honest general-wellness claims?

If questions 2 or 4 are negative, the valuable product may be a simple scheduled sleep environment rather than a vital-driven controller. That is still a useful outcome.
# Current prototype status

- Watch Tile and live heart-rate streaming are working.
- Start/Stop reliability and rotating-bezel navigation are implemented on the watch app.
- Known issue: the dashboard's sound/white-noise feature is not currently producing audible output and remains paused for future work.
