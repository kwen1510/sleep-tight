# Connect a Galaxy Watch5 to Sleep Tight

For the complete phone + watch + scheduled Mac setup, start with [SETUP.md](./SETUP.md).

This prototype performs bounded Galaxy Watch5 heart-rate captures in a foreground service and sends valid readings directly to this Mac over an authenticated WebSocket. It is a local wellness/research tool, not a medical monitor.

## 1. Mac receiver

The receiver is installed as the macOS login service `com.sleeptight.receiver`. It starts automatically, advertises `_sleeptight._tcp.local`, and appends readings to `computer/data/heart-rate-YYYY-MM-DD.jsonl`.

Open the live dashboard at:

```text
http://127.0.0.1:8766/dashboard.html
```

If macOS asks whether Python may accept incoming connections, allow it on the private network. The watch and Mac must be on the same Wi-Fi network without client isolation.

## 2. Enable wireless debugging on the watch

On the Galaxy Watch5:

1. Connect to the same Wi-Fi network as the Mac.
2. Open **Settings → About watch → Software information**.
3. Tap **Software version** five times to enable Developer mode.
4. Open **Settings → Developer options**.
5. Enable **ADB debugging**, **Turn off automatic Wi-Fi**, and **Wireless debugging**.
6. Open **Wireless debugging → Pair new device**. Keep the pairing code and pairing address visible.

On the Mac:

```bash
adb pair WATCH_IP:PAIRING_PORT
```

Enter the code displayed by the watch. Then return to the main **Wireless debugging** screen and use its separate connection port:

```bash
adb connect WATCH_IP:CONNECTION_PORT
adb devices -l
```

The pairing and connection ports are different.

## 3. Build and install

```bash
cd "/Users/etdadmin/Desktop/Sleep Tight"
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
./gradlew :watch-app:assembleDebug
adb install -r watch-app/build/outputs/apk/debug/watch-app-debug.apk
```

Open **Sleep Tight HR** from the watch app launcher.

## 4. Configure the app

On the watch, enter:

- WebSocket URL: `auto://sleep-tight`
- Pairing token: preconfigured during installation

Tap **Update vitals now**, or add the **Sleep Tight** tile and tap **Sync Data**. Grant **Sensors** access. For reliable screen-off collection, open the app’s permission settings when prompted and set Sensors to **Allow all the time**. Allow notifications so the foreground-service status remains visible. The tile also shows the configured daily 21:55 update time.

Wear the watch snugly. The app may display `0 bpm` until the optical sensor has a usable reading. Once connected, the Mac terminal displays each transmitted reading.

## 5. Verify screen-off operation

With the receiver running and app started:

```bash
adb logcat -s SleepTightHR
```

Start **Sync Data**, turn off the watch screen, and confirm that events continue until the 10-minute capture finishes.

## 6. Finish safely

The bounded capture stops automatically, unregisters the sensor, closes the WebSocket, releases the wake lock, and removes the foreground service. After installation testing, disable Wireless debugging and **Turn off automatic Wi-Fi** to restore normal battery behaviour.

## Current scope

- Sends heart rate, sensor accuracy, device timestamp, UTC observation time, and sequence number.
- Discovers the Mac automatically on the local network and reconnects after network loss or IP-address changes.
- Uses plain `ws://` only on the trusted local network; the bearer token prevents accidental clients but does not encrypt traffic.
- Does not yet send IBI/HRV, movement, oxygen saturation, or skin temperature.

The next sensor step is Samsung Health Sensor SDK `HEART_RATE_CONTINUOUS`, which provides heart rate plus IBI at 1 Hz with lower-power batching. It requires Health Platform developer mode during testing and Samsung partner registration for distribution.

## Official references

- [Samsung: continuous heart rate with the screen off](https://developer.samsung.com/galaxy-watch/blog/en/2026/04/23/continuous-heart-rate-tracking-on-galaxy-watch-even-with-the-screen-off)
- [Android: debug Wear OS over Wi-Fi](https://developer.android.com/training/wearables/get-started/debug-wifi)
- [Samsung Health Sensor SDK](https://developer.samsung.com/health/sensor/overview.html)
- [Samsung sensor data specifications](https://developer.samsung.com/health/sensor/guide/data-specifications.html)
