# Sleep Tight data-extraction contract

This contract separates data transport from scientific validity. “Available” means the system can request and store the value; it does not mean the value is a clinical measurement.

## Implemented through Health Connect

- sleep sessions, duration, and vendor-estimated stages;
- heart-rate records and resting heart rate;
- steps and exercise sessions;
- active and total calories;
- oxygen saturation and respiratory rate when a source app writes them;
- skin-temperature baseline/deviation when a source app writes it; and
- floors climbed.

One phone sync attempts every category independently. A denied permission, unsupported record type, or read exception is recorded per category and does not prevent the remaining categories from uploading.

## Implemented directly from the watch

- timestamped live heart rate and sensor accuracy;
- a scheduled pre-bed capture window; and
- sample count, minimum, maximum, mean, and median heart rate.

## Manual contextual inputs

- sleepiness, tension, and mood;
- caffeine after 15:00;
- alcohol, illness, pain, and late meal; and
- a short note.

## Conditional or unavailable

- Samsung sleep score is not represented by the standard Health Connect sleep record;
- IBI/HRV, wrist acceleration, raw PPG, and EDA require a Samsung Health Sensor SDK integration and partner approval for normal distribution;
- room light spectrum/intensity, sound level, and temperature require environmental sensors; and
- smartwatch data cannot provide validated real-time REM/deep-sleep or nightmare detection.

Every nightly snapshot contains a machine-readable `extraction.coverage` object with availability, attempt status, record count, extraction error, and future-integration reason.
