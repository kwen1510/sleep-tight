# Safety, privacy, security, and regulatory boundaries

## 1. Safety positioning

This system should improve a bedroom routine, not respond medically to vital signs. Consumer sleep technologies are not substitutes for clinical evaluation. The American Academy of Sleep Medicine states that unvalidated consumer technology should not be used to diagnose or treat sleep disorders.

Users with persistent insomnia, excessive daytime sleepiness, witnessed pauses in breathing/gasping, or concerning cardiovascular symptoms should be directed to a qualified clinician regardless of what the watch reports. The app should not suppress or reinterpret platform health alerts.

## 2. Light guardrails

- Default to darkness during sleep.
- Measure/calibrate illuminance at pillow/eye position; app brightness percentage is not a physical dose.
- Use slow transitions and cap pre-bed brightness.
- Keep a hardware/manual way to turn the lamp on.
- Do not use flashing light or stage-triggered pulses.
- Treat photosensitivity, bipolar-spectrum conditions, severe eye disease, migraine sensitivity, and circadian-rhythm treatment as reasons to seek professional advice before bright-light programs.

The light-during-sleep evidence does not supply a universal consumer threshold, but it supports minimizing rather than optimizing overnight light.

## 3. Sound guardrails

The WHO community-noise guidance recommends less than 30 dB(A) indoors in bedrooms for good-quality sleep; this is an environmental target, not a device prescription. A product cannot infer the sound level at the ear from the computer’s volume slider.

- Prefer reducing the noise source, insulation, or appropriate earplugs before adding masking sound.
- Use a calibrated room microphone only with explicit consent and local processing.
- Play through a distant speaker, not all-night earbuds.
- Start below the disturbing noise and find the minimum effective masking level.
- Do not increase volume automatically during sleep.
- Fade down/off and provide a hard limit.
- Exclude infants/children from initial product claims and studies; the evidence and risk profile differ.

## 4. Singapore regulatory context

Singapore’s Health Sciences Authority says software intended for medical purposes — including investigation, detection, diagnosis, monitoring, treatment, or management of a medical condition or physiological process — is generally a medical device. Products intended only to maintain or support general well-being without specific medical claims may fall outside that definition.

Therefore, intended use and marketing language matter. “Creates a personalized bedtime environment” is a wellness claim. “Treats insomnia using your vital signs” or “detects and prevents apnea” can move the product toward medical-device regulation. Obtain Singapore regulatory counsel before trials beyond low-risk wellness research or before commercial launch.

References: [HSA regulatory overview](https://www.hsa.gov.sg/medical-devices/regulatory-overview/) and [HSA digital health](https://www.hsa.gov.sg/medical-devices/digital-health/).

For US planning, the FDA’s January 2026 general-wellness guidance similarly distinguishes low-risk healthy-lifestyle functions unrelated to diagnosis, cure, mitigation, prevention, or treatment of disease. It is jurisdiction-specific and not a Singapore safe harbour. Reference: [FDA general-wellness guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices).

## 5. Privacy design

Sleep, heart-rate, and inferred-routine data are sensitive even when stored at home: they can reveal health patterns, occupancy, relationships, and daily schedules. Apply Singapore PDPA principles and platform health-data rules from the first prototype.

Minimum design:

- explicit, granular consent by signal and purpose;
- collect only signals needed for a stated feature;
- local processing and storage by default;
- separate identity from research session IDs;
- short raw-data retention; longer retention only for derived, user-approved summaries;
- export and deletion controls;
- no advertising, data-broker, or unrelated analytics use;
- encrypt in transit and at rest;
- never put health events or access tokens in ordinary analytics/crash logs;
- document every onward transfer, including Home Assistant add-ons and cloud lamp services.

Reference: [PDPC healthcare-sector advisory guidelines](https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/advisory-guidelines-for-the-healthcare-sector-sep-2023.pdf).

## 6. WebSocket and smart-home security

Follow OWASP’s WebSocket guidance:

- use `wss://` even on a home LAN;
- authenticate the handshake and authorize each command;
- validate `Origin` where browser clients are involved;
- use short-lived tokens, rotate/revoke them, and never place them in URLs;
- validate message structure and limit size/rate;
- prevent replay with event IDs, sequence windows, and session nonces;
- log connection/security events without logging physiological payloads;
- patch the computer, phone, Home Assistant, router, lamp bridge, and dependencies.

Place IoT devices on a restricted network segment if possible. Give the sleep controller access only to the bedroom entities it needs. A compromised vital-data stream must not gain arbitrary Home Assistant service access.

Reference: [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html).

## 7. Claims checklist

Before any public claim, record:

1. exact intended user and use environment;
2. whether the claim describes comfort/wellness or a disease/condition;
3. objective evidence for the complete system, not only a lamp or watch component;
4. foreseeable misuse and vulnerable groups;
5. jurisdiction-specific regulatory classification;
6. whether the UI communicates uncertainty and avoids false reassurance.
