# Validation plan

## 1. First objective

Do not begin by asking whether the product “enhances sleep.” First establish:

1. can it collect and timestamp a full night reliably without unacceptable battery loss?
2. can it control the room without abrupt or incorrect actions?
3. does the fixed routine appear helpful enough to justify adaptive control?

## 2. Engineering pilot: 10–14 nights

Run without automatic overnight actuation.

Measure:

- watch/phone/computer model and OS version;
- expected vs received sample count;
- latency distribution, not just average;
- reconnects, duplicates, stale packets, and clock drift;
- watch and phone battery change;
- lamp/speaker command-to-ack latency;
- lux at pillow for each lamp setting;
- dB(A) at pillow for each audio setting;
- all safety-rule activations.

Acceptance examples: no unexplained light activation, no volume above cap, all stale events rejected, and enough battery reserve to preserve the watch’s normal safety features. Set numeric reliability thresholds after observing the platform’s supported cadence.

## 3. Single-user crossover: 6–8 weeks

Compare conditions in randomized blocks, ideally with analysis rules fixed in advance:

- **A — baseline:** existing routine;
- **B — light routine:** pre-bed dimming + darkness + scheduled dawn;
- **C — light routine + optional masking:** only if environmental noise is a stated problem.

Use several nights per block and repeat blocks to reduce weekday, workload, illness, alcohol, exercise, and novelty effects. Do not compare one “good” intervention night with one baseline night.

### Primary outcome

A morning rating collected before showing the watch score, for example:

- perceived sleep quality, 0–10;
- morning alertness, 0–10.

Subjective outcomes are appropriate because the initial product claim is improved experience, but blinding is difficult and expectancy effects should be acknowledged.

### Secondary outcomes

- sleep diary: lights-out, estimated sleep latency, remembered awakenings, final wake;
- next-day sleepiness or a short psychomotor-vigilance task;
- wearable total sleep time, sleep timing, resting HR/HRV trend;
- intervention adherence;
- adverse events: awakenings attributed to light/sound, headache, anxiety, hearing discomfort;
- bedroom light and sound exposure.

Treat proprietary stage minutes and sleep scores as exploratory. Do not optimize against them.

## 4. Adaptation experiment

Only after the fixed profiles work reliably, compare:

- fixed best profile from the crossover; versus
- conservative weekly personalization choosing among the same safe profiles.

This isolates the value of “adaptive” control. If both arms change the same lamp and sound settings but only one uses wearable trends, any difference is more credibly due to adaptation rather than the routine itself.

Predefine:

- available actions;
- minimum nights before a change;
- missing-data policy;
- safety bounds;
- primary endpoint and minimum meaningful difference;
- stopping rules.

## 5. Multi-person feasibility trial

After the N-of-1 study, a small randomized crossover trial can test usability and signal direction. Stratify or record whether participants have environmental noise, because masking is unlikely to have the same value in a quiet room.

Exclude or clinically supervise people with suspected untreated sleep disorders, unstable medical/psychiatric conditions, photosensitivity concerns, significant hearing problems, or medications/shift work that materially complicate interpretation. Obtain ethics review and informed consent for research intended to produce generalizable knowledge.

## 6. Gold-standard validation track

If the eventual claim depends on real-time sleep stage, validate the full sensing-and-control pipeline against simultaneous PSG, with epoch-level confusion matrices and event timing. Report sensitivity, specificity, Cohen’s kappa, calibration, latency, failures, and results by relevant demographic/clinical subgroups. A high overall accuracy number is insufficient when sleep dominates the night and wake detection is the harder class.

If the eventual product uses phase-locked sound, wrist validation is not enough; it needs EEG, stimulus-timing characterization, arousal detection, and a study of clinical or functional outcomes rather than slow-wave amplitude alone.

## 7. Analysis safeguards

- lock the analysis before viewing condition labels;
- retain all nights and document exclusions;
- model repeated measures rather than treating nights as independent people;
- show individual trajectories and uncertainty, not only averages;
- report null and adverse results;
- separate exploratory model training from confirmatory evaluation;
- account for multiple outcomes;
- version the watch firmware, vendor algorithm, controller, and lamp/audio profile.

Consumer algorithms can change remotely, so reproducibility requires recording their versions and retaining the rawest permitted data.
