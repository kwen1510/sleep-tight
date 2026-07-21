# Adaptive light, sound, and sleep-stage control

## Product decision

The first safe controller separates three phases:

1. **Wind-down:** immediately use dim, blue-depleted amber/ember light, then fade toward darkness over 30 minutes.
2. **Sleep:** keep the lamp effectively off. Do not illuminate REM or other sleep stages.
3. **Morning review:** use Samsung Health's completed sleep record—sleep score, stages, heart rate, blood oxygen, and skin temperature where available—to compare nights and personalize the next wind-down.

Heart rate is an arousal signal, not a mood detector. The initial absolute heart-rate mapping is only a starting point; personalization should eventually use deviation from the user's own sleeping baseline.

## Light evidence

Expert consensus recommends a maximum melanopic equivalent daylight illuminance (EDI) of 10 lux at the eye for at least three hours before bedtime and less than 1 lux during sleep, with the sleep environment as dark as possible. Color does not replace intensity calibration: even warm light can be disruptive if it is bright.

- Brown et al. (2022), *Recommendations for daytime, evening, and nighttime indoor light exposure*: https://doi.org/10.1371/journal.pbio.3001571
- CIE, *Proper Light at the Proper Time*: https://www.cie.co.at/publications/cie-position-statement-integrative-lighting-recommending-proper-light-proper-time-3rd
- Rahman et al. (2017), blue-depleted evening ambient light: https://pmc.ncbi.nlm.nih.gov/articles/PMC5536841/

The screen simulation cannot guarantee melanopic EDI. A physical implementation needs the bulb's spectral output plus a calibrated measurement at eye/pillow level.

## What the Galaxy Watch can provide

Samsung's real-time Health Sensor SDK supports continuous heart rate with inter-beat intervals, accelerometer, PPG, and skin temperature on compatible models. These signals can support experimental sleep/wake inference, but they do not provide a validated real-time REM flag.

Samsung Health Data SDK exposes completed sleep sessions with Awake, Light, Deep, and REM stages. This is appropriate for next-morning analysis, not for claiming live stage detection.

- Samsung Health Sensor SDK overview: https://developer.samsung.com/health/sensor/overview.html
- Samsung sensor data specifications: https://developer.samsung.com/health/sensor/guide/data-specifications.html
- Samsung rich sleep data code lab: https://developer.samsung.com/codelab/health/sleep-data.html
- Android Health Connect `SleepSessionRecord`: https://developer.android.com/reference/androidx/health/connect/client/records/SleepSessionRecord

## Can we reconstruct the stages?

Approximately, yes; directly, no. Clinical stages are defined from EEG, eye movement, and muscle tone. A watch instead estimates them from indirect autonomic and movement patterns. Samsung has not published the production classifier used by Samsung Health, so its exact reconstruction is not available.

A defensible experimental pipeline would:

1. collect synchronized 25 Hz accelerometer and PPG/IBI data, rejecting loose-watch and motion-corrupted periods;
2. divide the night into 30-second epochs;
3. derive movement, pulse-rate variability, respiratory modulation, signal-quality, and temperature-trend features;
4. classify Wake, Light (N1/N2), Deep (N3), and REM using a temporal model that considers surrounding epochs; and
5. smooth impossible stage jumps and report probabilities rather than certain labels.

Published PPG-plus-accelerometer systems use this general approach, but four-stage agreement with polysomnography is only moderate. Samsung Health stage labels can be useful as *weak personalization labels*, but they cannot independently validate our model because they are themselves estimates. Proper validation requires simultaneous polysomnography scored from EEG/EOG/EMG.

For this product, the safer first live target is **sleep/wake plus arousal probability**, not a claimed live REM detector. A four-stage research model can be added later with a several-minute lag and an explicit confidence score. It should inform next-night personalization, not turn the lamp on during sleep.

- Fonseca et al. (2023), 30-second four-stage classification from wrist PPG/IBI and accelerometry: https://doi.org/10.1038/s41598-023-36444-2
- Beattie et al. (2017), Wake/Light/Deep/REM estimation from wrist optical plethysmography and accelerometry: https://pubmed.ncbi.nlm.nih.gov/29087960/
- Samsung smartwatch versus polysomnography validation: https://e-jsm.org/journal/view.php?number=358

## Sound evidence and limits

Continuous broadband noise may mask an inconsistent environment, but systematic reviews find mixed, low-certainty evidence. Silence is the default when the room is already quiet. Pink and brown noise are preference-based masking options, not guaranteed sleep treatments.

Phase-locked pink-noise bursts studied for slow-wave sleep require real-time EEG timing. A wrist watch without EEG cannot reproduce that protocol, so the product must not advertise ordinary continuous pink noise as closed-loop slow-wave stimulation.

The dashboard generates sounds locally with Web Audio—no downloaded or copyrighted recordings:

- **Pink noise:** softer high-frequency balance than white noise.
- **Brown noise:** more low-frequency energy and a deeper character.
- **Synthetic ocean:** filtered pink noise with slow amplitude modulation.
- **Silence:** preferred when masking is unnecessary.

The default is 8% browser volume with a 45-minute fade, but percentage is not dBA. Calibrate the complete room level at the pillow and keep it at or below 30 dBA, following WHO bedroom guidance.

- Riedy et al. (2021), *Noise as a sleep aid: a systematic review*: https://pubmed.ncbi.nlm.nih.gov/33007706/
- Capezuti et al. (2022), *Systematic review: auditory stimulation and sleep*: https://pmc.ncbi.nlm.nih.gov/articles/PMC9163611/
- WHO noise guidance: https://www.who.int/Europe/news-room/fact-sheets/item/noise
- Henin et al. (2019), closed-loop stimulation and slow oscillations: https://pmc.ncbi.nlm.nih.gov/articles/PMC6831893/

## Next engineering step

Connect a supported smart bulb and add two one-time calibration values: measured melanopic EDI at a known brightness/color setting and measured dBA at the pillow for a known speaker volume. Only then can the controller translate its relative percentages into defensible room targets.
