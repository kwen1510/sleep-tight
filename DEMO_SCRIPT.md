# Sleep Tight 3-Minute Demo Script

Use this as the recording outline for the public YouTube demo.

## 0:00-0:20 — Problem And Product

Show the GitHub Pages walkthrough:

https://kwen1510.github.io/sleep-tight/

Say:

> Sleep Tight is a local-first bedtime personalization prototype. A phone, Galaxy Watch, and Mac work together before bed so Codex can choose a gentle light and sound routine from the user's recent signals.

## 0:20-0:55 — Workflow

Click the main slides object.

Say:

> At 9:55 p.m., the phone exports the last 24 hours of vitals and the watch records a bounded 10-minute calibrated heart-rate window. At 10:05 p.m., Codex Scheduled reads the latest local data, analyzes sleep quality where possible, and chooses tonight's wind-down plan.

## 0:55-1:25 — Data Arriving On The Mac

Open the main dashboard.

Say:

> The Mac receiver is the local controller. It receives Health Connect-style phone records, watch heart-rate readings, timestamps, permissions, and extraction coverage. If real devices are not connected, the demo uses clearly labelled synthetic data so judges can still test the pipeline.

## 1:25-1:55 — Room Response

Open the lamp simulation.

Say:

> Codex does not improvise medical interventions during sleep. It chooses from bounded routines before sleep starts. Here the lamp fades warmer and lower, and the background sound fades out to facilitate winding down.

## 1:55-2:25 — Monthly Learning

Open the sleep report.

Say:

> Over time, Sleep Tight compares what happened across nights. The monthly report shows what Codex would learn, which routines helped, and how it would personalize the next month. This report is synthetic for the hackathon demo.

## 2:25-2:45 — Future Nudges

Open the future nudge simulator.

Say:

> The future version nudges the user during the day, because daytime behaviour affects the bedtime routine. The goal is not just a nicer lamp scene, but a loop that helps the user's habits support sleep.

## 2:45-3:00 — Codex And GPT-5.6

Say:

> GPT-5.6 shaped the core decision: the safest practical signals are right before sleep, not guessed sleep stages during the night. Codex was central to building the phone, watch, Mac receiver, dashboards, lamp simulation, monthly report, setup scripts, tests, and README.

End on the GitHub Pages walkthrough or README.
