# Designing a Wearable-Adaptive Sleep Environment

## A critical literature review of evening light, consumer sleep sensing, music, and broadband sound

**Prepared for:** Sleep Tight project  
**Review date:** 15 July 2026  
**Review type:** Structured critical narrative review with GRADE-informed evidence appraisal  

---

## Abstract

Sleep Tight proposes a bedroom system in which a smartwatch contributes physiological data to the control of lighting and sound. This review examines four linked questions: which light exposures support a gradual transition toward sleep; what consumer wearables can validly infer about sleep quality; whether music or broadband sound improves sleep; and how these elements can be combined without disrupting sleep. Searches emphasized peer-reviewed systematic reviews, meta-analyses, randomized and crossover human studies, polysomnography validation studies, consensus standards, and official technical documentation. The evidence supports a conservative design. Evening light should be quantified at the eye using melanopic equivalent daylight illuminance (melanopic EDI), not described only by hue or correlated colour temperature. Expert consensus recommends less than 10 lux melanopic EDI during the three hours before habitual sleep and less than 1 lux during sleep, while maintaining bright daytime exposure. Blue-depleted or spectrally tuned evening lighting can reduce melatonin suppression and alerting effects at matched photopic illuminance, but no robust evidence establishes a uniquely calming red, amber, or other decorative hue. During intended sleep, darkness is the safest default.

Consumer watches infer rather than measure sleep stages. They combine wrist movement with photoplethysmography-derived pulse and, in some devices, inter-beat intervals, oxygen saturation, respiratory rate, and temperature. Recent comparisons with polysomnography show high sensitivity for sleep but substantially poorer specificity for wake, and variable multi-stage performance. Watches are appropriate for longitudinal trends, personal baselines, probable sleep/wake state, and morning review; they should not be treated as real-time ground truth for REM or deep sleep, nor used to diagnose a sleep disorder.

Music has moderate-certainty evidence for improving subjective sleep quality in adults with insomnia symptoms, but objective actigraphy or polysomnography improvements are much less consistent. The literature commonly uses personally acceptable, predictable, low-arousal music for approximately 30-45 minutes before bed; slow instrumental music around 60-80 beats per minute is common, but evidence does not prove that this tempo is uniquely therapeutic. Evidence for continuous white, pink, or mixed broadband noise is very low certainty. A 2026 seven-night polysomnography crossover study found that continuous pink noise at 40 or 50 dBA reduced REM sleep and worsened subjective outcomes, while earplugs protected sleep more effectively from intermittent environmental noise. Therefore, silence and source-noise control should precede masking. If masking is necessary, it should be optional, calibrated at the pillow, and tested at the minimum effective level rather than run automatically all night.

The end result is a phase-based product: bright days; a user-selected, low-melanopic, slowly dimming evening scene; darkness during sleep; optional pre-sleep music; silence by default overnight; and a scheduled dawn simulation near waking. Wearable data should personalize future nights slowly and conservatively. Acute changes in heart rate should generally produce no light or sound action because they may represent normal REM physiology, movement, sensor artefact, illness, or an arousal that additional stimulation could worsen.

## Executive conclusion

The proposed system is technically feasible, but its scientifically defensible value lies in creating a consistent and pleasant sleep routine and learning from repeated outcomes - not in reacting to every heartbeat or claiming precise sleep-stage control.

### What the evidence supports

1. **Use light dose, not colour names.** Measure melanopic EDI and photopic illuminance at the user's eye position. Hue is an interface preference layered on top of a biological exposure constraint.
2. **Protect darkness during sleep.** Routine mid-sleep lamp activation is not supported and may be harmful.
3. **Use the watch for trends and coarse states.** Heart rate, inter-beat intervals, movement, respiratory estimates, and temperature trends can improve context, but wrist devices cannot directly observe EEG-defined stages.
4. **Use music before sleep, not as a mandatory all-night stimulus.** Music may improve perceived sleep quality, especially when it is familiar, low-arousal, and incorporated into a stable bedtime ritual.
5. **Do not default to continuous white, pink, or brown noise.** The evidence is weak, exposure reporting is poor, and new controlled evidence raises concern about REM sleep at 40-50 dBA.
6. **Personalize across nights, not within seconds.** Adjust one bounded profile after several usable nights and morning ratings. An uncertain or missing signal must lead to no action.

### Proposed first product profile

| Phase | Light | Sound | Wearable use |
|---|---|---|---|
| Daytime | Encourage strong daytime light exposure; outside light when practical | No sleep intervention | Establish ordinary daytime physiology |
| 3 h before bed | Keep melanopic EDI below 10 lux where practical; reduce brightness progressively | Ordinary environment | Begin individual baseline |
| Final 30-45 min | User-preferred amber/ember appearance within low-melanopic limit; fade smoothly toward darkness | Optional familiar low-arousal music, then fade out | Detect settling only; no abrupt control |
| Intended sleep | Less than 1 lux melanopic EDI; preferably darkness | Silence by default; masking only for a demonstrated external-noise problem | Record movement, HR/IBI and quality; no stage-triggered light |
| Night disturbance | Very dim, low-mounted safety light only after explicit user/room event | Do not raise volume from heart rate alone | Mark uncertain arousal; avoid compounding it |
| Final 20-30 min before wake | Optional scheduled dawn simulation | Optional gentle alarm | Wake window based on schedule, not a claimed exact stage |

## 1. Review question and scope

The product contains a causal chain with four separate links:

1. a bedroom light or sound profile changes arousal, circadian physiology, or sleep;
2. a smartwatch measures signals that represent the user's sleep state or sleep quality;
3. the state estimate arrives with sufficient reliability and latency to guide an intervention; and
4. the intervention improves a meaningful outcome without causing arousal, circadian disruption, hearing discomfort, or anxiety.

Evidence for one link does not validate the full chain. For example, a watch may measure pulse accurately while still classifying REM poorly; pink noise may mask traffic while simultaneously altering sleep architecture; and a red-looking bulb may still deliver enough irradiance to be biologically active. This review therefore keeps measurement, intervention, and closed-loop control distinct.

The intended use is general wellness in adults sleeping at home. It is not a review of treatment for diagnosed insomnia, sleep apnea, circadian rhythm disorders, bipolar disorder, dementia, or paediatric sleep. Those groups may respond differently and require clinical oversight.

## 2. Methods

### 2.1 Search approach

A structured rapid search was performed through 15 July 2026 using PubMed/MEDLINE, PubMed Central, journal and publisher pages, and authoritative guidance or platform documentation. Existing references in the Sleep Tight research library were checked and expanded. Search concepts combined terms for:

- evening light, spectral tuning, blue depletion, melanopic EDI, melatonin, sleep onset, light during sleep, and dawn simulation;
- smartwatch, wearable, wrist PPG, accelerometry, inter-beat interval, sleep staging, consumer sleep tracker, and polysomnography;
- music, insomnia, sleep quality, tempo, personalised music, white noise, pink noise, brown noise, environmental noise, earplugs, and auditory stimulation; and
- closed-loop acoustic stimulation, slow oscillation, EEG, memory, and arousal.

Reference lists of high-level reviews were used to identify pivotal primary studies. Device APIs and current signal availability were checked only in official documentation.

### 2.2 Inclusion priorities

Priority was given to:

1. peer-reviewed systematic reviews and meta-analyses;
2. randomized or controlled human trials with objective or validated subjective sleep outcomes;
3. prospective validation against laboratory polysomnography;
4. consensus or professional guidance with an explicit evidence basis; and
5. official manufacturer documentation for current API capability.

Preprints, marketing pages, anecdotal recommendations, and studies concerned only with daytime task performance were not used to support product efficacy. A retracted 2022 meta-analysis of acoustic stimulation was explicitly excluded from the evidence synthesis.

### 2.3 Evidence appraisal

Conclusions are labelled using a pragmatic GRADE-informed scale:

- **High:** consistent high-quality evidence where further work is unlikely to change the conclusion.
- **Moderate:** reasonably consistent evidence, but with limitations in generalisability, precision, or implementation.
- **Low:** limited, heterogeneous, indirect, or mainly subjective evidence.
- **Very low:** substantial uncertainty, high risk of bias, conflicting results, or inadequate exposure characterization.

This is a single-reviewer critical narrative review, not a registered systematic review. It does not claim exhaustive retrieval, duplicate screening, or formal meta-analysis. Its strength is transparent triangulation of high-level reviews, key controlled studies, validation studies, standards, and current technical feasibility.

## 3. Light: from visual ambience to circadian dose

### 3.1 Why colour is an incomplete description

Human vision and circadian photoreception weight wavelength differently. The melanopsin-containing intrinsically photosensitive retinal ganglion cells that contribute to circadian phase shifting, melatonin suppression, and alerting responses are especially sensitive to short-wavelength blue-cyan light, with an action spectrum near 490 nm after ocular filtering. However, biological response depends jointly on spectrum, irradiance, duration, timing, pupil size, prior light history, age, and the individual's circadian phase.

Correlated colour temperature (CCT) and visual hue are therefore insufficient. Two lamps that both appear warm can have different spectral power distributions and melanopic content, while a very dim cooler light can deliver less melanopic stimulus than a bright amber light. The correct engineering quantities are spectral power distribution, photopic illuminance, melanopic daylight efficacy ratio, and melanopic EDI measured at the eye.

Brown et al.'s peer-reviewed expert consensus recommends daytime exposure above 250 lux melanopic EDI at the eye, evening exposure below 10 lux melanopic EDI for at least the three hours before habitual sleep, and below 1 lux melanopic EDI during sleep [1]. These are consensus targets for healthy adults, not individually guaranteed thresholds.

**Evidence judgement:** Moderate for the direction and importance of melanopic dose; low-to-moderate for a single universal threshold because individual sensitivity varies markedly.

### 3.2 Evening intensity, spectrum, and timing

Gooley et al. compared evening room light below 200 lux with dim light below 3 lux in 116 healthy young adults. Room light delayed melatonin onset in 99% of participants and shortened melatonin duration by about 90 minutes [2]. The study demonstrates that ordinary indoor light can be biologically consequential; it does not imply that every person needs complete darkness throughout the evening.

Rahman et al. conducted a randomized crossover laboratory study in 16 adults using equal-illuminance 50-lux evening exposures. A blue-depleted LED caused less melatonin suppression and lower physiological alertness than standard 4100 K fluorescent light, although headline sleep outcomes did not differ reliably [3]. A later randomized study in 72 men isolated melanopic irradiance from display luminance and colour appearance. Lower melanopic exposure shortened sleep latency and reduced melatonin suppression relative to higher melanopic exposure [4]. Together, these studies support spectral tuning while showing why visual appearance alone is not enough.

A systematic review and meta-analysis of short-wavelength reduction interventions found possible sleep benefits but heterogeneous interventions and outcomes [5]. Small blue-blocking-lens trials in insomnia have reported subjective and actigraphic improvements [6], while other healthy-adult trials have been mixed [7]. Blue reduction is thus plausible but not a standalone treatment for chronic insomnia.

Bright-light therapy is a different intervention. A 2023 meta-analysis of 22 insomnia studies found improvements mainly in wake after sleep onset, with little consistent effect on sleep latency, total sleep time, or efficiency; timing determined whether the circadian phase advanced or delayed [8]. Bright evening light can intentionally delay the clock and is useful in some clinical or shift-work contexts, but that is the opposite of the usual bedtime goal.

**Evidence judgement:** Moderate that lower evening melanopic exposure reduces melatonin suppression and acute alerting effects; low-to-moderate that it produces large, durable improvements in everyday sleep quality by itself.

### 3.3 Is red or amber light intrinsically calming?

The literature does not establish a unique calming colour. Small short-duration studies of red, green, and blue illumination report autonomic changes, but samples are small, exposures are often poorly matched photometrically, sequences are not always counterbalanced, and changes in heart-rate variability do not directly establish relaxation or better sleep [9,10]. Expectations and cultural associations also influence perceived ambience.

Amber, ember, or very warm white is a sensible interface choice because it can be generated with relatively little short-wavelength output and is commonly experienced as comfortable at night. Its benefit should nevertheless be stated accurately: it is a practical way to achieve a low-melanopic environment, not a proven sedative wavelength. User preference may improve adherence and perceived calm, but brightness and timing remain primary.

**Evidence judgement:** Very low that a particular visible hue independently calms people or improves sleep after melanopic dose and illuminance are controlled.

### 3.4 How quickly should light fade?

No strong clinical literature identifies an optimal 20-, 30-, 45-, or 60-minute dimming curve. Research typically compares static exposures, broad evening environments, or scheduled bright-light treatment. A gradual fade is therefore a human-factors and comfort decision nested within evidence-based exposure limits.

For product design, an exponential or ease-in/ease-out fade over 30-45 minutes is reasonable because it avoids visible steps and can become a learned bedtime cue. The system should already have reduced melanopic exposure during the preceding hours. A dramatic last-minute colour change cannot undo a bright evening.

**Evidence judgement:** Low for gradual dimming as a behavioural cue; very low for any particular mathematical fade curve.

### 3.5 Light during sleep

Darkness is the safest default. In a randomized crossover laboratory study of 20 healthy adults, one night under approximately 100 lux room light increased sleeping heart rate, reduced heart-rate variability, and increased next-morning insulin resistance relative to dim light below 3 lux [11]. This is a small acute study and does not quantify long-term risk from every night-light scenario, but it provides direct evidence against routine mid-sleep illumination.

The consensus target is below 1 lux melanopic EDI during sleep [1]. A product may provide a very dim, low-mounted, motion-triggered safety light when a user gets out of bed. Such a feature should be triggered by an explicit event and should not be confused with sleep enhancement.

**Evidence judgement:** Moderate that darkness is preferable and ordinary room light during sleep can acutely perturb physiology.

### 3.6 Dawn simulation

Small randomized crossover experiments suggest that a dawn beginning approximately 30 minutes before a fixed wake time can improve subjective alertness and aspects of post-waking performance [12]. Evidence is promising but based on small samples and heterogeneous outcomes. Scheduling against a required wake time is more reliable than attempting to identify a precise light-sleep stage from a consumer watch.

**Evidence judgement:** Low-to-moderate for improved morning alertness; insufficient for claims of improved overnight sleep architecture.

### 3.7 Light design conclusion

The light system should implement a biological exposure envelope and then allow aesthetic preference within it:

- encourage meaningful daytime light exposure;
- begin evening reduction early, aiming below 10 lux melanopic EDI at the eyes during the final three hours;
- use low-melanopic warm/amber scenes because they are practical and pleasant, not because amber is a proven sedative;
- fade to darkness before or at intended sleep;
- keep sleep below 1 lux melanopic EDI;
- reserve very dim safety light for explicit movement or user commands; and
- optionally run a scheduled 20-30 minute dawn profile.

## 4. What a smartwatch can and cannot know about sleep

### 4.1 Polysomnography and indirect sensing

Clinical sleep stages are scored in 30-second epochs using EEG brain activity, electro-oculography, chin electromyography, and supporting respiratory and cardiac signals. A smartwatch normally lacks EEG, eye-movement, and muscle-tone channels. It observes indirect correlates:

- accelerometer and gyroscope movement;
- PPG pulse waveform;
- heart rate and inter-beat intervals;
- pulse-rate variability as a proxy for aspects of HRV;
- respiratory modulation of the PPG signal;
- oxygen saturation where available;
- peripheral skin temperature trends; and
- context such as clock time and habitual schedule.

The watch therefore estimates sleep and stage probabilities. A proprietary label is an algorithmic output, not a direct physiological measurement.

### 4.2 Overall performance against polysomnography

Lee et al.'s 2025 peer-reviewed meta-analysis included 24 studies and 798 participants across multiple consumer wrist devices. Pooled estimates differed significantly from PSG for total sleep time, sleep efficiency, sleep latency, and wake after sleep onset, with substantial heterogeneity [13]. This supports trend use but rejects interchangeability with PSG.

Schyvens et al. compared six current wrist devices with PSG. All were generally sensitive to sleep, but wake specificity ranged only from 29.39% to 52.15% [14]. The practical failure mode is highly relevant to an adaptive bedroom: a quiet person lying awake can be called asleep, and an algorithm may attribute normal stillness to light or deep sleep.

A 2023 multicentre study tested 11 consumer systems, including Galaxy Watch5, Pixel Watch, Fitbit Sense 2, Apple Watch 8, and Oura Ring 3, across 75 participants. Macro F1 scores for epoch-level stage classification varied from 0.26 to 0.69, and performance changed with BMI, sleep efficiency, and apnea-hypopnea index [15]. A 2024 three-device validation similarly found stage sensitivity varying by device and stage [16]. Algorithms and firmware evolve, so results for one model and software version cannot be assumed to transfer indefinitely.

Fitbit-specific meta-analysis demonstrates the common pattern: sleep sensitivity is high, specificity is lower, total sleep and efficiency tend to be overestimated, and wake after sleep onset underestimated [17]. Multimodal devices using motion plus cardiac signals often improve over motion-only systems, but they do not become diagnostic PSG substitutes.

**Evidence judgement:** Moderate-to-high that consumer wearables can characterize sleep timing and longitudinal trends; moderate that they detect sleep sensitively; low for accurate wake detection in quiet users; low-to-moderate and device-dependent for four-stage classification.

### 4.3 Galaxy Watch evidence and signal access

The Galaxy Watch5 was among the devices in the multicentre PSG comparison [15]. A separate study of 195 sleep-clinic participants compared Galaxy Watch nocturnal respiratory estimates with a nasal thermocouple. Average and continuous respiratory rate showed low overall error in normal-to-moderate obstructive sleep apnea, but accuracy declined in severe apnea [18]. This is useful evidence for one derived signal, not proof that the watch can diagnose apnea or accurately stage sleep.

Samsung's current Health Sensor SDK documentation states that compatible Galaxy Watch4 and later devices can expose continuous accelerometer, heart rate including inter-beat intervals, raw green/red/infrared PPG, skin temperature, SpO2, ECG, and other signals [19]. This is official technical documentation, not peer-reviewed evidence of clinical validity. Samsung Health's completed sleep records can provide vendor-estimated stages after the night, but the production classifier and its real-time internals are not published.

For Sleep Tight, the direct WebSocket heart-rate stream proves transport feasibility but is not enough for robust sleep inference. The next research build should collect synchronized accelerometer and quality-controlled IBI/PPG features, retain signal-quality flags, and treat temperature and SpO2 as slow contextual trends rather than immediate triggers.

### 4.4 Can stages be reconstructed from wrist data?

Research algorithms demonstrate feasibility. Fonseca et al. used wrist accelerometry and PPG-derived cardiac activity to classify wake, combined N1/N2, N3, and REM in 30-second epochs, validating on a held-out clinical dataset [20]. Other PPG-only experiments report promising four-class accuracy but often use small or selected samples [21]. These models exploit temporal context because sleep stages follow structured transitions; an isolated heart-rate sample is not informative enough.

A defensible experimental pipeline would:

1. synchronize clocks and capture raw or near-raw signals;
2. detect poor skin contact, motion corruption, and missing data;
3. compute 30-second movement and cardiac features;
4. use several minutes of temporal context;
5. output calibrated probabilities, not categorical certainty;
6. include an explicit unknown state; and
7. validate against simultaneous PSG in data not used for training.

For bedroom control, a simpler target is preferable: probable awake, settling, stable sleep, probable arousal, and unknown. Even those states should be smoothed and should not routinely cause mid-sleep stimulation.

### 4.5 What heart rate means at night

Heart rate is neither a mood sensor nor a direct sleep-quality score. It varies with stage, posture, thermoregulation, respiration, dreams, alcohol, fever, medication, fitness, stress, and sensor artefact. REM sleep can include autonomic variability that resembles arousal. A rule such as "heart rate rose, therefore increase calming sound" is physiologically ambiguous and can create a positive feedback problem: the sound itself may cause further arousal.

The appropriate features are deviations from a personal baseline, persistence across multiple samples, concurrence with movement or signal quality, and next-morning context. Acute heart-rate alerts should remain separate from a wellness controller and follow platform medical-safety conventions.

### 4.6 Device-use conclusion

The watch should contribute to:

- session start and end;
- personal resting and sleeping baselines;
- probable sleep/wake and sustained arousal trends;
- morning summaries of sleep timing, resting HR/HRV trend, movement, and data completeness; and
- multi-night comparison of fixed environmental profiles.

It should not autonomously claim:

- exact real-time REM, light, or deep sleep;
- diagnosis of insomnia, sleep apnea, arrhythmia, or another disorder;
- causal attribution of a high heart rate to anxiety; or
- proof that an intervention improved sleep merely because a vendor sleep score increased.

## 5. Music and sound

### 5.1 Music before sleep

The strongest sound-related evidence is for music as a pre-sleep ritual, not all-night broadband noise. A 2022 Cochrane review included 13 randomized trials and 1,007 adults with insomnia symptoms. Music probably improved subjective sleep quality with moderate-certainty evidence, while evidence for subjective sleep latency, duration, and efficiency was low certainty and objective measures showed no clear improvement [22]. This subjective-objective gap is important: feeling calmer and sleeping better are meaningful wellness outcomes, but they are not proof of altered sleep architecture.

A randomized trial in 112 adults with depression-related insomnia found a clinically relevant PSQI improvement after four weeks of bedtime music, but no actigraphic change and diminished benefit four weeks after stopping [23]. A 2024 trial in 75 university students found that both classical and jazz bedtime routines improved self-reported sleep and insomnia relative to a breathing/relaxation control, with no superior genre [24]. A 2024 meta-analysis in adults with mental-health problems found a moderate effect after excluding an extreme outlier, but the evidence remained heterogeneous [25].

Reviews commonly describe low-arousal instrumental music around 60-80 beats per minute, simple structure, smooth dynamics, and 30-45 minute sessions [26,27]. These are recurring intervention characteristics, not isolated causal ingredients. Trials rarely manipulate tempo while holding familiarity, preference, loudness, harmony, and expectation constant. Personally acceptable and predictable music may matter as much as genre or tempo.

**Evidence judgement:** Moderate for improvement in subjective sleep quality among adults with sleep complaints; low for objective sleep architecture or a uniquely effective tempo/genre.

### 5.2 Practical music specification

An evidence-aligned profile should:

- be optional and chosen or approved by the user;
- favour low arousal, predictable dynamics, and minimal abrupt events;
- avoid spoken advertisements, notifications, and large loudness jumps;
- begin during the final 30-45 minutes before bed;
- fade to silence at or shortly after intended sleep onset;
- use a room speaker or pillow speaker rather than sealed earbuds for all-night wear; and
- record the actual sound level at the pillow rather than relying on a software percentage.

Lyrics are not universally harmful, but language comprehension and autobiographical associations can maintain attention. Instrumental material is a conservative default; personally familiar vocal music may still be preferable for some users. The system should not claim that 60 beats per minute mechanically entrains the heart into sleep.

### 5.3 White, pink, and brown noise

Noise colour describes spectral power distribution:

- **White noise:** approximately equal power per hertz; relatively bright because high-frequency energy accumulates across wider bands.
- **Pink noise:** power decreases roughly 3 dB per octave, producing approximately equal power per octave.
- **Brown or red noise:** power decreases roughly 6 dB per octave, emphasizing low frequencies.

These are spectra, not single frequencies. A product specification must state bandwidth, filtering, level, speaker response, and measurement position. Brown noise can interact strongly with room modes and walls; a nominal digital spectrum does not guarantee the same pillow spectrum in different bedrooms.

Riedy et al.'s systematic review of 38 studies rated evidence that continuous broadband noise improves sleep as very low quality because of heterogeneous exposures, weak controls, and conflicting outcomes [28]. Capezuti et al. reviewed 34 studies involving 1,103 participants and found no strong overall evidence, despite positive findings in some short studies [29]. Many papers did not adequately report sound pressure level or spectral characteristics.

The most consequential recent result is Basner et al.'s 2026 seven-night randomized laboratory crossover study in 25 healthy adults. Intermittent environmental events at 45-65 dBA reduced N3 sleep. Continuous pink noise at 40 or 50 dBA provided only minor masking benefits, reduced REM sleep, worsened subjective sleep, alertness and mood, and performed worse overall than earplugs [30]. This small controlled study does not settle every noise colour, level, or population, but it directly contradicts the assumption that all-night pink noise is harmless.

**Evidence judgement:** Very low for continuous broadband noise as a general sleep enhancer; low and context-specific for masking environmental noise; moderate concern against indiscriminate 40-50 dBA all-night pink noise.

### 5.4 Environmental noise and level calibration

Environmental noise itself disrupts sleep. A 2022 update to the WHO review included more than 100,000 responses and found exposure-response relationships between transportation noise and high sleep disturbance [31]. WHO guidance recommends less than 30 dBA inside bedrooms at night for good-quality sleep [32]. This is an environmental target, not proof that adding a 30 dBA noise generator improves sleep.

The correct hierarchy is:

1. reduce the source: close windows, repair rattles, change room layout, isolate mechanical noise;
2. improve passive attenuation: curtains, seals, earplugs when safe and comfortable;
3. use masking only if intermittent sound remains a demonstrated problem; and
4. select the lowest masking level that materially reduces salience.

If the unmasked room is already near or below 30 dBA, silence is preferable. If external peaks require 40-50 dBA continuous masking, current evidence favours trying source control or earplugs before accepting that exposure. A phone sound-meter app can support rough setup but is not a calibrated Class 1 or Class 2 instrument, especially at low frequencies.

### 5.5 Nature sounds and amplitude modulation

Rain, ocean, fan, and wind sounds are often filtered noise with slow amplitude modulation. They may feel less artificial and improve adherence, but the evidence base usually combines them with other audio or reports preference rather than isolating spectral or modulation effects. Modulation should remain shallow and slow enough to avoid salient peaks; obvious short loops can become attention-capturing.

There is no high-quality evidence for an optimal ocean-wave period or amplitude-modulation depth for sleep. These should be personalised and tested against silence, with peak level constrained.

**Evidence judgement:** Low for preference and relaxation; very low for a specific modulation frequency or objectively improved sleep.

### 5.6 Binaural beats and rhythmic claims

Binaural beats require separate tones at each ear and therefore headphones, which complicates safe overnight use. Recent reviews describe possible effects on anxiety or subjective sleep in small heterogeneous studies, but protocols and outcomes vary and blinding is difficult [33]. Claims that a beat frequency directly forces the brain into delta or theta sleep exceed the evidence.

**Evidence judgement:** Very low for sleep improvement and insufficient for routine product inclusion.

### 5.7 Closed-loop auditory stimulation

EEG-timed closed-loop auditory stimulation is scientifically distinct from continuous pink noise. Laboratory systems detect the phase of cortical slow oscillations during non-REM sleep and deliver brief sounds at predicted up-states while monitoring arousal. A 2021 meta-analysis of 10 studies and 177 participants found only a small, borderline overall memory effect and concluded evidence was insufficient to recommend commercial devices [34]. A later meta-analytic review reported declining effects over time, blinding problems, and poor reliability of memory outcomes [35]. A 2023 randomized nap study showed strong physiological perturbation without improved motor memory and emphasized calibration to avoid sleep disruption [36].

One published 2022 meta-analysis reporting larger benefits was retracted in 2026 and is excluded from this review [37]. This illustrates why the product should not borrow the language of neural closed-loop stimulation for a smartwatch-driven speaker.

Heart-rate oscillations may eventually contribute timing information, but current experimental work does not establish that a networked watch-to-computer-to-speaker pathway can replace EEG phase detection. The target oscillation is sub-second, whereas consumer sensing, Bluetooth/Wi-Fi transport, browser audio scheduling, and OS power management add variable latency.

**Evidence judgement:** Low that EEG-based stimulation reliably enhances selected slow-wave measures; very low for durable functional benefit; no adequate evidence for watch-only phase-locked stimulation.

## 6. Integrated control design

### 6.1 Control objective

The controller should maximize comfort, routine consistency, and morning-rated benefit subject to strict non-disturbance constraints. It should not maximize vendor deep-sleep minutes or respond to noisy physiology in real time.

A safe action hierarchy is:

1. do nothing;
2. continue the scheduled fade;
3. reduce sound or light;
4. mark an event for morning review;
5. only activate a safety feature after an explicit event or command.

Increasing overnight stimulation should require stronger evidence than decreasing it.

### 6.2 State model

The recommended live states are:

- **Awake/wind-down:** user has begun a session and remains active.
- **Settling:** sustained low movement and cardiovascular descent relative to personal baseline.
- **Probable stable sleep:** several minutes of low movement with plausible cardiac data.
- **Probable arousal:** sustained change supported by movement and cardiac features.
- **Unknown:** poor contact, missing packets, contradictory signals, or low confidence.

Unknown must never be silently converted into sleep. Proprietary REM/light/deep labels may be imported next morning for exploratory analysis but should not control the lamp.

### 6.3 Recommended first-night parameters

These are conservative engineering starting points, not clinically proven optima:

- Begin the dedicated wind-down scene 45 minutes before intended lights-out.
- Ensure the broader final three-hour environment is below 10 lux melanopic EDI at the eyes where practical.
- Fade the dedicated scene smoothly to off by lights-out.
- Keep the sleep environment below 1 lux melanopic EDI.
- Offer 30-45 minutes of user-approved low-arousal music, ending in silence.
- Do not enable broadband noise automatically.
- If masking is requested, calibrate at the pillow and begin below 30 dBA where measurable; reject the profile if it must become intrusive or approach the 40-50 dBA exposure associated with poorer outcomes in the 2026 trial.
- Use a fixed wake time and an optional 20-30 minute dawn ramp.

### 6.4 Personalisation policy

Personalisation should occur after at least three usable nights under the same profile. Change only one dimension at a time: fade start, visual preference within the melanopic limit, music choice, music duration, or masking on/off. Evaluate using:

- morning sleep-quality rating before showing the watch score;
- morning alertness;
- estimated sleep latency and remembered awakenings;
- wearable total sleep timing and resting HR/HRV trend;
- data completeness;
- environmental light and sound exposure; and
- adverse events or irritation.

The product should retain a fixed-profile control condition. If adaptive and fixed profiles perform similarly, adaptation adds complexity without demonstrated benefit.

### 6.5 Safety envelope

- No routine light during intended sleep.
- No volume increase based on heart rate alone.
- No headphones required for overnight playback.
- No diagnostic or treatment claims.
- No inference when signal quality is poor.
- User can stop sensing and actuation immediately.
- Alerts about possible medical abnormalities must be separated from wellness control.
- Users with suspected sleep apnea, severe insomnia, bipolar-spectrum illness, photosensitivity, hearing impairment, or other significant conditions should seek appropriate clinical guidance.

## 7. Evidence quality summary

| Claim | Best evidence | Confidence | Product implication |
|---|---|---:|---|
| Lower evening melanopic exposure reduces melatonin suppression and alerting effects | Consensus plus controlled spectral studies | Moderate | Measure melanopic EDI; dim early |
| A particular decorative hue is uniquely calming | Small heterogeneous autonomic studies | Very low | Treat hue as preference, not therapy |
| Darkness is preferable during sleep | Consensus plus controlled acute study | Moderate | Lamp off during core sleep |
| Scheduled dawn can improve morning alertness | Small crossover trials | Low-moderate | Optional fixed wake ramp |
| Watches estimate sleep timing and trends | Multiple PSG validations and meta-analysis | Moderate-high | Use longitudinally |
| Watches detect quiet wake or exact stages reliably | Device-dependent PSG studies | Low | Use confidence and unknown states |
| Bedtime music improves perceived sleep quality | Cochrane review and RCTs | Moderate | Optional 30-45 min pre-sleep music |
| 60-80 BPM is uniquely effective | Recurring protocol feature, not isolated causal evidence | Low | Starting range only; preference matters |
| Continuous broadband noise generally improves sleep | Conflicting systematic reviews | Very low | Silence by default |
| Pink noise at 40-50 dBA is harmless all night | Controlled 2026 trial found reduced REM | Evidence of concern | Avoid indiscriminate exposure |
| Earplugs can outperform masking for intermittent noise | Controlled 2026 trial | Low-moderate | Try attenuation before masking |
| Watch-only closed-loop sound enhances deep sleep | No adequate validation | Very low | Do not claim or deploy |

## 8. Research gaps and proposed validation

The most important missing studies for this product are not another generic sleep-score comparison. They are direct tests of the complete system:

1. **Photometric calibration:** measure spectral output, melanopic EDI, and photopic lux at the actual eye position across bulb settings.
2. **Acoustic calibration:** measure LAeq, LCeq, and peaks at the pillow across speaker settings and document room spectra.
3. **Signal feasibility:** quantify overnight packet loss, battery use, IBI quality, movement artefact, and clock drift.
4. **Fixed-profile crossover:** compare baseline, dim-light routine, and dim-light plus optional music over randomized repeated blocks.
5. **Masking study only when relevant:** compare silence, source control/earplugs, and minimum-effective masking in users with a real intermittent-noise problem.
6. **Adaptive-value study:** compare the best fixed profile with slow weekly personalisation while keeping safety bounds identical.
7. **PSG track:** only if stage-dependent claims remain a goal, validate the complete model and latency against simultaneously scored PSG.

Morning subjective ratings should be collected before revealing wearable scores to reduce expectation and anchoring. Proprietary stage minutes should remain exploratory. All firmware, algorithms, audio profiles, and bulb spectra must be versioned.

## 9. Final answer

At the end of the literature, the best product is quieter and less reactive than the original concept.

The strongest design is a **wearable-informed bedtime environment**, not a heartbeat-controlled sleep machine. It uses low-melanopic, low-intensity light to make the evening visually comfortable and progressively darker; it allows personally meaningful, low-arousal music during the final part of the bedtime routine; it keeps the bedroom dark and normally silent during sleep; and it uses a scheduled dawn near the required wake time. The smartwatch records movement and cardiac context, helps identify probable settling and broad sleep/wake trends, and supports comparison across nights. It does not determine with certainty whether the user is in REM or deep sleep, and an isolated heart-rate change does not justify light or sound.

If environmental noise is the problem, fix or attenuate the noise first. Continuous white, pink, or brown noise should be an opt-in experiment at the minimum effective calibrated level, not a universal therapy. The 2026 pink-noise trial makes an all-night 40-50 dBA default particularly difficult to justify.

The product's most credible promise is:

> Sleep Tight creates a consistent, low-disturbance bedtime and wake environment, then uses wearable trends and morning feedback to learn which safe routine feels best for the individual.

It should not promise to diagnose sleep disorders, detect exact stages in real time, increase deep sleep, or treat insomnia without separate clinical-grade validation.

## References

1. Brown TM, Brainard GC, Cajochen C, et al. Recommendations for daytime, evening, and nighttime indoor light exposure to best support physiology, sleep, and wakefulness in healthy adults. *PLoS Biology*. 2022;20:e3001571. Peer-reviewed consensus. https://doi.org/10.1371/journal.pbio.3001571
2. Gooley JJ, Chamberlain K, Smith KA, et al. Exposure to room light before bedtime suppresses melatonin onset and shortens melatonin duration in humans. *Journal of Clinical Endocrinology & Metabolism*. 2011;96:E463-E472. https://doi.org/10.1210/jc.2010-2098
3. Rahman SA, St Hilaire MA, Gronfier C, et al. The effects of spectral tuning of evening ambient light on melatonin suppression, alertness and sleep. *Physiology & Behavior*. 2017;177:221-229. https://doi.org/10.1016/j.physbeh.2017.05.002
4. Schöllhorn I, Stefani O, Lucas RJ, et al. Melanopic irradiance defines the impact of evening display light on sleep latency, melatonin and alertness. *Communications Biology*. 2023. https://pubmed.ncbi.nlm.nih.gov/36854795/
5. Shechter A, Kim EW, St-Onge MP, Westwood AJ. Interventions to reduce short-wavelength blue light exposure at night and their effects on sleep: a systematic review and meta-analysis. *Sleep Advances*. 2020;1:zpaa002. https://doi.org/10.1093/sleepadvances/zpaa002
6. Shechter A, et al. Blocking nocturnal blue light for insomnia: a randomized controlled trial. *Journal of Psychiatric Research*. 2018;96:196-202. https://pmc.ncbi.nlm.nih.gov/articles/PMC5703049/
7. Bigalke JA, Greenlund IM, Nicevski JR, Carter JR. Effect of evening blue light blocking glasses on subjective and objective sleep in healthy adults: a randomized control trial. *Sleep Health*. 2021. https://pubmed.ncbi.nlm.nih.gov/33707105/
8. Chambe J, Reynaud E, Maruani J, et al. Light therapy in insomnia disorder: a systematic review and meta-analysis. *Journal of Sleep Research*. 2023;32:e13895. https://doi.org/10.1111/jsr.13895
9. Grote V, et al. Impact of colored light on cardiorespiratory coordination. *Evidence-Based Complementary and Alternative Medicine*. 2014. https://pubmed.ncbi.nlm.nih.gov/24489590/
10. Yuda E, et al. Suppression of vagal cardiac modulation by blue light in healthy subjects. *Journal of Physiological Anthropology*. 2016. https://pubmed.ncbi.nlm.nih.gov/27716445/
11. Mason IC, Grimaldi D, Reid KJ, et al. Light exposure during sleep impairs cardiometabolic function. *PNAS*. 2022;119:e2113290119. https://doi.org/10.1073/pnas.2113290119
12. Thompson A, et al. Effects of dawn simulation on markers of sleep inertia and post-waking performance in humans. *European Journal of Applied Physiology*. 2014;114:1049-1056. https://doi.org/10.1007/s00421-014-2831-z
13. Lee YJ, Lee JY, Cho JH, et al. Performance of consumer wrist-worn sleep tracking devices compared to polysomnography: a meta-analysis. *Journal of Clinical Sleep Medicine*. 2025;21:573-582. https://doi.org/10.5664/jcsm.11460
14. Schyvens AM, Peters B, Van Oost NC, et al. A performance validation of six commercial wrist-worn wearable sleep-tracking devices for sleep stage scoring compared to polysomnography. *Sleep Advances*. 2025;6:zpaf021. https://doi.org/10.1093/sleepadvances/zpaf021
15. Lee T, Cho Y, Cha KS, et al. Accuracy of 11 wearable, nearable, and airable consumer sleep trackers: prospective multicenter validation study. *JMIR mHealth and uHealth*. 2023;11:e50983. https://pubmed.ncbi.nlm.nih.gov/37917155/
16. Robbins R, et al. Accuracy of three commercial wearable devices for sleep tracking in healthy adults. 2024. https://pubmed.ncbi.nlm.nih.gov/39460013/
17. Haghayegh S, Khoshnevis S, Smolensky MH, Diller KR, Castriotta RJ. Accuracy of wristband Fitbit models in assessing sleep: systematic review and meta-analysis. *Journal of Medical Internet Research*. 2019;21:e16273. https://doi.org/10.2196/16273
18. Jung H, Kim D, Choi J, Joo EY. Validating a consumer smartwatch for nocturnal respiratory rate measurements in sleep monitoring. *Sensors*. 2023;23:7976. https://doi.org/10.3390/s23187976
19. Samsung Electronics. Samsung Health Sensor SDK overview and data specifications. Official technical documentation; not peer-reviewed. Accessed 15 July 2026. https://developer.samsung.com/health/sensor/overview.html
20. Fonseca P, Ross M, Cerny A, et al. A computationally efficient algorithm for wearable sleep staging in clinical populations. *Scientific Reports*. 2023;13:9182. https://doi.org/10.1038/s41598-023-36444-2
21. Korkalainen H, et al. Multi-stage sleep classification using photoplethysmographic sensor. *Royal Society Open Science*. 2023;10:221517. https://doi.org/10.1098/rsos.221517
22. Jespersen KV, et al. Listening to music for insomnia in adults. *Cochrane Database of Systematic Reviews*. 2022. https://pubmed.ncbi.nlm.nih.gov/36000763/
23. Lund HN, Pedersen IN, Johnsen SP, et al. Music to improve sleep quality in adults with depression-related insomnia: randomized controlled trial. 2022. https://pubmed.ncbi.nlm.nih.gov/35697087/
24. Yan D, Wu Y, Luo R, et al. Bedtime music therapy for college students with insomnia: a randomized assessor-blinded controlled trial. *Sleep Medicine*. 2024. https://doi.org/10.1016/j.sleep.2024.07.018
25. Zhao N, Lund HN, Jespersen KV. A systematic review and meta-analysis of music interventions to improve sleep in adults with mental health problems. *European Psychiatry*. 2024;67:e62. https://doi.org/10.1192/j.eurpsy.2024.1773
26. Petrovsky DV, et al. Effects of music interventions on sleep in older adults: a systematic review. *Geriatric Nursing*. 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8316320/
27. Pan W, Wang X. Elements of music that work to improve sleep: a narrative review. *Frontiers in Sleep*. 2025. https://doi.org/10.3389/frsle.2025.1707162
28. Riedy SM, Smith MG, Rocha S, Basner M. Noise as a sleep aid: a systematic review. *Sleep Medicine Reviews*. 2021;55:101385. https://doi.org/10.1016/j.smrv.2020.101385
29. Capezuti E, Pain K, Alamag E, et al. Systematic review: auditory stimulation and sleep. *Journal of Clinical Sleep Medicine*. 2022;18:1697-1709. https://doi.org/10.5664/jcsm.9860
30. Basner M, Smith MG, Cordoza M, et al. Efficacy of pink noise and earplugs for mitigating the effects of intermittent environmental noise exposure on sleep. *Sleep*. 2026;49:zsag001. https://doi.org/10.1093/sleep/zsag001
31. Smith MG, Cordoza M, Basner M. Environmental noise and effects on sleep: an update to the WHO systematic review and meta-analysis. *Environmental Health Perspectives*. 2022;130:076001. https://doi.org/10.1289/EHP10197
32. World Health Organization Regional Office for Europe. Noise fact sheet and Night Noise Guidelines for Europe. Authoritative guidance; not journal peer-reviewed. https://www.who.int/Europe/news-room/fact-sheets/item/noise
33. Daengruan P, et al. Music and binaural beat interventions for young adults: a systematic review of effects on anxiety, sleep, and cognition. 2026. https://pubmed.ncbi.nlm.nih.gov/41656644/
34. Wunderlin M, Züst MA, Hertenstein E, et al. Modulating overnight memory consolidation by acoustic stimulation during slow-wave sleep: a systematic review and meta-analysis. *Sleep*. 2021;44:zsaa296. https://doi.org/10.1093/sleep/zsaa296
35. Harlow IM, Jané M, Read CA, Chrobak JJ. Memory retention following acoustic stimulation in slow-wave sleep: a meta-analytic review of replicability and measurement quality. 2023. https://pubmed.ncbi.nlm.nih.gov/41426467/
36. Leminen M, et al. The effects of closed-loop auditory stimulation on sleep oscillatory dynamics in relation to motor procedural memory consolidation. *Sleep*. 2023;46:zsad206. https://pubmed.ncbi.nlm.nih.gov/37531587/
37. Stanyer EC, et al. The impact of acoustic stimulation during sleep on memory and sleep architecture: a meta-analysis. *Journal of Sleep Research*. 2022;31:e13385. **Retracted in 2026; excluded from synthesis.** https://pubmed.ncbi.nlm.nih.gov/34850995/
38. Khosla S, Deak MC, Gault D, et al. Consumer sleep technology: an American Academy of Sleep Medicine position statement. *Journal of Clinical Sleep Medicine*. 2018;14:877-880. https://doi.org/10.5664/jcsm.7128

## Appendix A. Peer-review and source-status guide

The references above fall into four categories:

- **Peer-reviewed evidence syntheses:** systematic reviews and meta-analyses in academic journals. These provide the broadest evidence but inherit limitations of the underlying studies.
- **Peer-reviewed primary studies:** randomized, crossover, laboratory, or prospective validation studies. These supply exposure details and direct measurements but may be small or device-specific.
- **Peer-reviewed consensus/position statements:** expert recommendations published in academic journals. These synthesize evidence but are not treatment-effect trials.
- **Authoritative non-peer-reviewed sources:** WHO guidance and official device documentation. These are appropriate for public-health targets or API capability, not for proving intervention efficacy.

Publication in a peer-reviewed journal does not guarantee high-quality evidence. Sample size, controls, blinding, outcome validity, exposure calibration, conflicts of interest, replication, and retraction status all matter.

## Appendix B. Measurement checklist

### Light

- Spectral power distribution or validated bulb spectral data
- Photopic lux at the user's eye position
- Melanopic EDI at the same position and gaze direction
- Distance, angle, reflections, and screen contribution
- Start time, duration, and fade curve
- Daytime and prior-light context

### Sound

- A-weighted equivalent level at pillow (LAeq)
- C-weighted level where low-frequency energy matters (LCeq)
- Maximum and event levels
- One-third-octave or spectral profile at the pillow
- Speaker location and room response
- Loop duration, modulation depth, and fade timing

### Wearable

- Model, firmware, SDK, and algorithm version
- Sampling rate and timestamps
- Signal-quality flags and missingness
- Battery impact and reconnects
- Raw versus derived signals
- Personal baseline window
- Confidence and unknown-state rate

