# Adaptive Sleep Environment: Product Idea

## The idea

Most sleep products apply the same general advice to everyone: use a particular colour of noise, dim the lights at a fixed time, or follow a standard bedtime routine. This product takes a different approach. It treats each night as part of a careful personal experiment and gradually learns which bedroom conditions appear to work best for one person.

While I sleep, my smartwatch measures the signals it can reliably access, such as heart rate and movement. Depending on the watch and its permissions, it may also provide heart-rate variability, respiratory-rate estimates, blood-oxygen measurements, skin-temperature deviation, and vendor-generated sleep estimates.

The watch sends timestamped measurements through a phone relay and an authenticated WebSocket connection to a computer. The computer controls the bedroom environment: a dimmable lamp and a speaker capable of generating sound locally.

Codex runs on the computer as the research and analysis layer. It reviews what happened over several nights, compares the interventions with the observed outcomes and my morning feedback, and proposes the next safe experiment. The system therefore evolves from my own repeated responses instead of assuming that a population average is automatically best for me.

## Core principle

The product is not trying to discover a universal “perfect sleep sound.” It is trying to answer a narrower and more useful question:

> Within a safe set of bedroom conditions, which combination appears to help this person sleep and wake better?

Personalization is based on repeated evidence. A single heart-rate change, a single night, or a smartwatch-generated sleep-stage label is not enough to establish that an intervention works.

## How one night works

### 1. Before sleep

The system begins a user-approved bedtime profile. It can gradually lower the brightness of the lamp, shift it toward a warmer tone, and optionally start a quiet sound profile.

The person confirms the intended bedtime, wake time, and any relevant context, such as unusual stress, illness, alcohol, caffeine, exercise, travel, or disruptive external noise. These factors help prevent the system from attributing every change to the lamp or sound.

### 2. While settling

The watch sends available measurements to the computer. Movement and heart-rate trends can help the system estimate a broad state such as `awake`, `settling`, `probably asleep`, or `unknown`.

If a sound profile is active, the system may slowly fade it toward silence after stable probable sleep. It does not need to identify an exact sleep stage to perform this low-risk action.

### 3. During core sleep

Darkness and silence are the default. The system continues collecting measurements and checking that the devices are operating normally.

It does not repeatedly turn on the lamp or increase speaker volume in response to heart-rate changes. A higher heart rate may reflect normal REM sleep, a brief awakening, illness, sensor error, or another factor. The safest response to uncertain data is usually to observe rather than intervene.

If sound masking is part of that night’s experiment, it remains within a calibrated maximum level and follows the selected schedule. The intervention is recorded exactly: sound family, spectral shape, centre or cutoff frequencies, amplitude, duration, fades, speaker level, and measured room level where available.

### 4. Near the requested wake time

The system can run a gradual dawn simulation inside a user-approved window. Brightness, colour temperature, and ramp duration are recorded. A fixed hard alarm remains available even if the watch, computer, or network fails.

### 5. The following morning

Before showing a wearable sleep score, the system asks for a short report:

- How well did I sleep?
- How refreshed do I feel?
- Did the sound or light wake or disturb me?
- Were there unusual circumstances?

The morning report is important because the product is intended to improve the person’s experience, not merely maximize an opaque score produced by the watch manufacturer.

## What the system can measure

The exact measurements depend on the watch, operating system, permissions, battery state, and sampling mode.

| Measurement | Potential use | Important limitation |
|---|---|---|
| Heart rate | Personal overnight baseline and sustained changes | Changes are nonspecific |
| Inter-beat intervals or HRV | Multi-night autonomic trend | Short windows and wrist PPG can be noisy |
| Accelerometer movement | Probable sleep/wake and restlessness | Quiet wakefulness can resemble sleep |
| Respiratory-rate estimate | Nightly trend and data-quality context | Not a diagnosis of a breathing disorder |
| Blood oxygen, when available | Exploratory overnight context | Often intermittent and device-dependent |
| Skin-temperature deviation | Multi-night contextual trend | Usually relative rather than core temperature |
| Watch sleep stages | Retrospective comparison | Inferred, proprietary, and often delayed |
| Bedroom light level | Physical record of the light intervention | Requires a positioned/calibrated sensor |
| Bedroom sound level | Physical record of the audio intervention | Requires consent and suitable calibration |
| Morning self-report | Perceived quality and alertness | Subjective and affected by expectation |

No unavailable value is silently invented. Missing or delayed data produces an `unknown` state.

## The personal learning loop

The learning loop operates across nights rather than making aggressive second-by-second changes:

1. **Observe a baseline.** Record several nights without changing the existing routine.
2. **Choose one safe profile.** Examples include silence, low-level masking for environmental noise, a different fade duration, or a different dawn ramp.
3. **Run it for multiple nights.** One night is too easily affected by chance and outside factors.
4. **Collect outcomes.** Combine morning reports, sleep timing, wearable trends, adherence, and disturbances.
5. **Compare with previous conditions.** Look for repeatable differences and uncertainty, not a single best-looking score.
6. **Keep, reject, or retest.** Stable benefits can become part of the preferred profile. Unclear results are repeated or abandoned.
7. **Continue cautiously.** Preferences and circumstances can change, so the system occasionally rechecks assumptions without constantly disrupting a working routine.

The system should make small, interpretable changes. It should know what changed on a given night and why. If several variables change simultaneously, it becomes difficult to learn which one mattered.

## Sound generation and experiments

The computer generates audio locally rather than depending on a fixed streaming track. This allows each profile to be reproduced precisely.

A sound profile may define:

- white, pink, brown, or spectrally shaped broadband noise;
- frequency range and filter slopes;
- optional removal of irritating or hardware-distorted bands;
- amplitude and maximum measured room level;
- fade-in, fade-out, and total duration;
- continuous versus scheduled playback;
- speaker and room-calibration information.

“Research-backed” does not mean that every noise colour has been proven to improve sleep. Current evidence for continuous white or pink noise is weak, and newer evidence raises concern about all-night pink noise under some conditions. The initial purpose of generated noise is therefore **optional masking of disruptive environmental sound**, followed by personal comparison against silence. The system should be able to conclude that no generated sound is best for a particular person.

Brief EEG-phase-locked acoustic stimulation is a separate research method. A smartwatch cannot measure the brain-wave phase required for that technique, so the product should not describe ordinary watch-triggered audio as equivalent to EEG closed-loop stimulation.

## Light experiments

The controllable variables may include:

- pre-bed brightness curve;
- pre-bed colour temperature;
- time at which the lamp reaches darkness;
- dawn start time;
- dawn duration;
- final waking brightness and tone.

The core sleep interval remains dark by default. Light is not used as a routine response to an overnight vital change. Experiments focus on the transition into sleep and the transition into waking, where a slowly changing environment is more defensible and less likely to cause an awakening.

## The role of Codex

Codex is the deliberative research assistant, not the millisecond safety controller.

Codex can:

- summarize each night and identify missing or unreliable data;
- compare repeated conditions and generate charts or statistical summaries;
- inspect current research before proposing a new class of intervention;
- suggest the next experiment within pre-approved safety limits;
- explain why a profile is being retained, changed, or rejected;
- maintain an experiment journal and version every sound and light profile;
- notice confounding factors and avoid overclaiming a result;
- prepare reports that the user can inspect or share with a researcher.

Codex does not directly bypass hard limits. A deterministic policy engine controls maximum sound level, allowed light transitions, stale-data rejection, rate limits, and failure behaviour. New experiment types require explicit user approval before they can affect the room.

## What the product learns

Over time, the system may learn patterns such as:

- whether silence or low-level masking works better in this bedroom;
- whether sound is useful only on externally noisy nights;
- how quickly audio should fade after probable sleep onset;
- which pre-bed dimming schedule is most comfortable;
- which dawn duration produces better morning alertness;
- how consistent bedtime and wake timing relate to the person’s outcomes;
- when the available data is too uncertain to justify a change.

It should not claim to learn a medical diagnosis from these observations. It may discover personal associations, but association does not by itself prove cause.

## Safety and trust principles

1. **Do nothing is a valid action.** Uncertainty must not force an intervention.
2. **Dark and quiet are the default core-sleep state.** Sound is optional and light remains off.
3. **Hard limits are deterministic.** Codex cannot override them.
4. **Every intervention is reproducible.** The system records the exact profile and version.
5. **Every conclusion shows uncertainty.** One unusual night does not rewrite the routine.
6. **The user remains in control.** Profiles, experiments, data retention, and device access can be stopped or revoked.
7. **Health data stays local by default.** Only the minimum required data is collected.
8. **The system is a wellness experiment, not a medical device by implication.** It does not diagnose or treat sleep disorders.

## Initial experiment sequence

The first version should deliberately be simpler than the complete vision:

1. Collect baseline watch, room, and morning-report data without automatic changes.
2. Test a fixed pre-bed dimming and dawn profile against the existing routine.
3. If environmental noise is a real problem, compare silence with one calibrated low-level masking profile.
4. Test different fade durations rather than different noise colours all at once.
5. Add conservative weekly recommendations from Codex.
6. Only then allow automatic selection among a small set of profiles already approved by the user.

This sequence establishes whether the environmental routine itself helps before asking whether adaptive selection adds further value.

## Long-term vision

The long-term product is a local, evolving sleep laboratory for one person. It combines wearable trends, physical measurements of the bedroom, carefully versioned sound and light profiles, and subjective outcomes. It learns slowly, explains its reasoning, and remains willing to decide that a simpler environment is better.

The differentiator is not that it produces more automation. It is that it conducts disciplined, personalized experiments while the user retains control of the bedroom and the data.

## Related research

- [Evidence review](./01-evidence-review.md)
- [Wearable sensing and platform feasibility](./02-wearable-sensing.md)
- [Product architecture](./03-product-architecture.md)
- [Safety, privacy, and regulation](./04-safety-privacy-regulation.md)
- [Validation plan](./05-validation-study.md)
- [Product roadmap](./06-product-roadmap.md)
- [Annotated source library](./sources.md)
