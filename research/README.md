# Sleep Tight research library

Last reviewed: 14 July 2026 (Singapore)

## Executive conclusion

The product is technically feasible, but the scientifically defensible first version is **not** “detect an exact sleep stage from a watch and stimulate it.” Consumer wrist wearables infer sleep from movement and optical pulse signals; they are good enough for broad sleep/wake trends but have much weaker wake specificity and stage agreement than polysomnography. A safe MVP should therefore use the watch for personalized baselines, coarse state changes, and anomaly/quality signals while keeping the bedroom dark and quiet by default.

The best-supported initial interventions are:

1. a scheduled, gradually dimming warm light before bed;
2. darkness during intended sleep;
3. optional, low-level sound masking only when the user has disruptive environmental noise;
4. a scheduled dawn simulation near the requested wake time;
5. conservative, slow adjustments based on multi-night trends and user feedback.

Continuous white or pink noise should not be marketed as inherently sleep-enhancing. Two systematic reviews found weak or very-low-quality evidence, and a 2026 laboratory study found that continuous pink noise reduced REM sleep in its tested conditions. Phase-locked auditory stimulation is a distinct research technique: it uses EEG to time brief sounds to brain slow waves. A smartwatch does not provide the signal or timing precision needed to reproduce it.

## Documents

- [dashboard.html](./dashboard.html) — interactive evidence ranking, practical nightly protocol, smartwatch markers, and key-paper highlights
- [10-personal-sleep-experiment-protocol.md](./10-personal-sleep-experiment-protocol.md) — required watch access, phased N-of-1 experiments, daily Codex analysis, and safety rules
- [09-deep-literature-review.md](./09-deep-literature-review.md) — full critical review of light, wearable sleep measurement, music, broadband noise, and integrated control
- [evidence-matrix.csv](./evidence-matrix.csv) — study-by-study design, sample, peer-review status, evidence judgement, and product decision
- [01-evidence-review.md](./01-evidence-review.md) — what the science supports, contradicts, or leaves uncertain
- [02-wearable-sensing.md](./02-wearable-sensing.md) — useful signals, accuracy limits, and Apple/Wear OS access
- [03-product-architecture.md](./03-product-architecture.md) — recommended local-first system and control policy
- [04-safety-privacy-regulation.md](./04-safety-privacy-regulation.md) — safety envelope, Singapore context, security, and claims
- [05-validation-study.md](./05-validation-study.md) — an N-of-1 MVP study and a later controlled trial
- [06-product-roadmap.md](./06-product-roadmap.md) — staged build plan and decisions
- [07-adaptive-sleep-environment-idea.md](./07-adaptive-sleep-environment-idea.md) — the complete product idea and personal learning loop
- [sources.md](./sources.md) — annotated primary/authoritative bibliography and open-access links

The publication-ready PDF is available at [../output/pdf/sleep-tight-critical-literature-review.pdf](../output/pdf/sleep-tight-critical-literature-review.pdf).

## Recommended product statement

> Sleep Tight personalizes a calm bedtime and wake environment from your schedule, recent wearable trends, bedroom conditions, and morning feedback. It is a general-wellness product and does not diagnose or treat sleep disorders.

Avoid promises such as “detects deep sleep in real time,” “optimizes your sleep stages,” “treats insomnia,” or “prevents sleep apnea” unless the specific system has been clinically validated and reviewed under the applicable medical-device regime.

## Research method and limits

This is a narrative product review, not a registered systematic review. It prioritizes systematic reviews, meta-analyses, controlled human studies, platform-owner documentation, and government/professional guidance. Search was current through 14 July 2026. Device APIs, policies, and regulations can change; confirm them before implementation or launch. Medical and legal sections are product-research guidance, not individual medical or legal advice.
