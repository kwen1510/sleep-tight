# Sleep Tight

## Start Here: Let Codex Set Up The Demo

Open Codex in this repository, copy the full prompt below, and let it prepare the Mac receiver, install the required pieces, launch the local demo pages, and walk you through connecting the phone and Galaxy Watch.

```text
You are helping me set up Sleep Tight from this GitHub repository.

Goal:
Run the full Sleep Tight hackathon demo locally, connect my Android phone and Samsung Galaxy Watch where possible, and give me clear step-by-step instructions until the Mac dashboard, lamp simulation, sleep report, and future nudge demo all work.

Please do the following:
1. Inspect the repository structure and explain the three-part system: Android phone app, Galaxy Watch app, and Mac local receiver.
2. Install or verify the local dependencies needed for the Mac receiver and demo pages.
3. Start the Mac receiver/background app so it can accept phone and watch data.
4. Launch the local demo pages:
   - Main slides: computer/platform-demo.html
   - Main dashboard: computer/dashboard.html
   - Lamp simulation: computer/wind-down-demo.html
   - Sleep report: computer/sleep-report.html
   - Future nudge simulator: research/codex-nudge-simulator.html
5. Help me connect the Android phone app so it can export the last 24 hours of Health Connect vitals to the Mac.
6. Help me connect the Galaxy Watch app so it can capture the final 10-minute pre-sleep heart-rate window and send it to the Mac.
7. Verify that the dashboard receives data. If real device data is unavailable, use the synthetic demo data and clearly label it as synthetic.
8. Explain the nightly workflow in presentation terms: 9:55 p.m. device handoff, 10:05 p.m. Codex Scheduled analysis, lamp and background sound wind-down, monthly learning logs, and future daytime nudges.
9. Do not treat this as medical advice. Keep the setup local-first and privacy-conscious.

When you are done, give me:
- the local URLs to open;
- what data the phone is sending;
- what data the watch is sending;
- how to confirm the Mac receiver is working;
- a short talk track I can use for a hackathon demo.
```

Sleep Tight is a local-first bedtime personalization prototype. A phone, Galaxy Watch, and Mac work together each night so Codex can use the day's vitals and the final pre-sleep heart-rate window to choose a gentle light and background-sound plan.

The project avoids reacting to uncertain real-time sleep stages. Instead, it focuses on the period right before sleep, where recent behaviour, stress signals, heart rate, and routine consistency are more useful for choosing a safe wind-down environment.

## Nightly Workflow

```mermaid
flowchart LR
    subgraph Devices["9:55 p.m. device handoff"]
        Phone["Android phone<br/>exports last 24h vitals"]
        Watch["Galaxy Watch<br/>records calibrated HR<br/>for 10 minutes"]
    end

    subgraph Mac["MacBook local controller"]
        Receiver["Background app<br/>receives JSONL data"]
        Codex["10:05 p.m. Codex Scheduled<br/>reads latest app data<br/>and analyzes sleep quality if available"]
        Plan["Personalized plan<br/>sound profile + lamp fade"]
    end

    subgraph Bedroom["Wind-down environment"]
        Lamp["Lamp dims warmer<br/>and lower"]
        Sound["Background sound plays<br/>then fades out"]
    end

    subgraph Learning["Longer-term learning"]
        Logs["Monthly logs<br/>what AI learnt"]
        Nudges["Future daytime nudges<br/>routine reminders"]
    end

    Phone --> Receiver
    Watch --> Receiver
    Receiver --> Codex
    Codex --> Plan
    Plan --> Lamp
    Plan --> Sound
    Lamp --> Logs
    Sound --> Logs
    Logs --> Codex
    Logs -. future .-> Nudges
```

## How It Works

1. At 9:55 p.m. daily, the phone sends the past 24 hours of vitals to the MacBook. At the same time, the Galaxy Watch starts a 10-minute calibrated heart-rate recording and sends the summary to the MacBook. The Mac app runs in the background.
2. At 10:05 p.m., Codex Scheduled runs on the Mac. It pulls the most updated data from the application, analyzes sleep quality where sleep records or sleep scores are available, suggests the type of background sound to use, and decides how the lamp should tone down.
3. The light starts dimming and the music plays to facilitate sleep.
4. Monthly logs summarize what the AI has learnt across the nights.
5. Future plans add daytime nudges that remind the user to follow habits that support the evening routine.

## How GPT-5.6 Shaped The Build

The starting idea was to run an agent overnight and let it make sleep better in the background. GPT-5.6 research changed the design direction: the strongest practical signals for this prototype come from the period right before sleep, not from trying to infer sleep stages and react while someone is already asleep.

That led to a safer workflow: look at the day's vitals, capture a final pre-bed heart-rate window, then hyper-personalize the user's wind-down environment before sleep starts.

The implementation was split into three applications:

- an Android phone app that exports Health Connect records;
- a Samsung Galaxy Watch app that runs on a timer and captures heart rate;
- a Mac app that receives local data, builds the nightly snapshot, and coordinates the recommendation.

To make the physical experience demonstrable without smart-home hardware, Codex designed a simulated lamp and background-sound scene. It also generated a 30-day simulated review so the repo can show what Codex would learn after repeated nights and how that learning would personalize the experience.

## Device Data

The phone exports granted Health Connect data, including sleep sessions and stages, heart-rate samples, resting heart rate, steps, exercise sessions, active and total calories, oxygen saturation, respiratory rate, skin temperature, floors climbed, permissions, attempted categories, and extraction errors.

The watch sends timestamped pre-bed heart-rate readings, sensor accuracy, device timestamps, sequence numbers, capture mode, correlation IDs, and a summary with window start/end, sample count, minimum, maximum, mean, and median BPM.

## Repository Map

- `phone-app/` — Android phone sync application.
- `watch-app/` — Galaxy Watch heart-rate capture application.
- `computer/` — Mac receiver, dashboard, nightly orchestration, room-command output, and monthly reporting.
- `tools/` — setup, testing, simulation, and analysis utilities.
- `research/` — evidence review, product architecture, validation plan, and future-work notes.

## Local Setup

```bash
./setup-sleep-tight --time 22:05
```

See [SETUP.md](./SETUP.md) for the full phone, watch, and Mac setup.
