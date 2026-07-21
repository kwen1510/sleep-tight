package com.sleeptight.heartrate;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.util.Log;

import org.json.JSONObject;

import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

public final class HeartRateService extends Service implements SensorEventListener {
    public static final String ACTION_HEART_RATE = "com.sleeptight.heartrate.HEART_RATE";
    public static final String ACTION_STATUS = "com.sleeptight.heartrate.STATUS";
    public static final String EXTRA_BPM = "bpm";
    public static final String EXTRA_STATUS = "status";

    private static final String TAG = "SleepTightHR";
    private static final String CHANNEL = "vitals-sync";
    private static final int NOTIFICATION_ID = 7;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final AtomicLong sequence = new AtomicLong();
    private final Runnable reconnect = this::connect;
    private final Runnable rediscover = this::discoverComputer;
    private final OkHttpClient client = new OkHttpClient.Builder()
            .pingInterval(20, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build();

    private SensorManager sensorManager;
    private Sensor heartRateSensor;
    private PowerManager.WakeLock wakeLock;
    private NsdManager nsdManager;
    private NsdManager.DiscoveryListener discoveryListener;
    private volatile WebSocket socket;
    private volatile boolean socketOpen;
    private String url;
    private String token;
    private long lastSentAt;
    private long lastScheduledSampleAt;
    private long lastTileAt;
    private boolean autoDiscovery;
    private volatile boolean stopping;
    private final List<Float> scheduledSamples = Collections.synchronizedList(new ArrayList<>());
    private volatile boolean scheduledCapture;
    private volatile boolean scheduledOnly;
    private volatile boolean trackingStarted;
    private volatile Instant scheduledWindowStart;
    private volatile boolean manualCapture;
    private volatile String correlationId;
    private volatile boolean completedCapture;
    private volatile int lastSummaryBpm;
    private volatile long captureDeadlineElapsed;
    private volatile long uploadDeadlineElapsed;
    private final Runnable sendScheduledSummary = this::sendPreBedSummary;
    private final Runnable captureProgress = this::reportCaptureProgress;

    @Override public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        nsdManager = (NsdManager) getSystemService(Context.NSD_SERVICE);
        if (sensorManager != null) {
            // A non-wakeup HR sensor delivers live foreground readings. The wakeup
            // variant may batch samples, which makes a short manual capture appear stuck.
            heartRateSensor = sensorManager.getDefaultSensor(Sensor.TYPE_HEART_RATE, false);
            if (heartRateSensor == null) heartRateSensor = sensorManager.getDefaultSensor(Sensor.TYPE_HEART_RATE, true);
            if (heartRateSensor == null) heartRateSensor = sensorManager.getDefaultSensor(Sensor.TYPE_HEART_RATE);
        }
        PowerManager power = (PowerManager) getSystemService(POWER_SERVICE);
        wakeLock = power.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SleepTight::HeartRate");
        wakeLock.setReferenceCounted(false);
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        stopping = false;
        startForeground(NOTIFICATION_ID, notification("Connecting…"), ServiceInfo.FOREGROUND_SERVICE_TYPE_HEALTH);
        if (intent != null) {
            url = intent.getStringExtra("url");
            token = intent.getStringExtra("token");
            if (intent.getBooleanExtra("scheduled_capture", false)) {
                // Every watch sync is deliberately bounded. The service must not turn
                // into a permanent background heart-rate session.
                scheduledOnly = true;
                scheduledCapture = true;
                completedCapture = false;
                manualCapture = intent.getBooleanExtra("manual_capture", false);
                correlationId = intent.getStringExtra("correlation_id");
                scheduledWindowStart = Instant.now();
                scheduledSamples.clear();
                lastScheduledSampleAt = 0;
                long duration = Math.max(10_000L, intent.getLongExtra("summary_after_ms", 60_000L));
                captureDeadlineElapsed = SystemClock.elapsedRealtime() + duration;
                uploadDeadlineElapsed = captureDeadlineElapsed + 15_000L;
                handler.removeCallbacks(sendScheduledSummary);
                handler.removeCallbacks(captureProgress);
                handler.postDelayed(sendScheduledSummary, duration);
                handler.post(captureProgress);
                saveTileStatus(duration >= 600_000L ? "Measuring 10 min" : "Measuring 60 sec", 0);
            }
        }
        if (url == null || token == null) {
            var prefs = getSharedPreferences("settings", MODE_PRIVATE);
            url = prefs.getString("url", null);
            token = prefs.getString("token", null);
        }

        if (url == null || token == null) {
            broadcastStatus("Missing connection settings");
            stopSelf();
            return START_NOT_STICKY;
        }
        autoDiscovery = url.startsWith("auto://");

        if (!wakeLock.isHeld()) wakeLock.acquire();
        if (heartRateSensor == null) {
            broadcastStatus("Heart-rate sensor unavailable");
            stopSelf();
            return START_NOT_STICKY;
        }
        sensorManager.unregisterListener(this);
        if (!sensorManager.registerListener(this, heartRateSensor, SensorManager.SENSOR_DELAY_UI)) {
            finishCaptureFailure("Could not start heart-rate sensor • retry", "Sensor unavailable • retry");
            return START_NOT_STICKY;
        }
        trackingStarted = true;
        if (autoDiscovery) discoverComputer(); else connect();
        return START_STICKY;
    }

    private void discoverComputer() {
        if (stopping) return;
        handler.removeCallbacks(rediscover);
        stopDiscovery();
        broadcastStatus("Finding Sleep Tight computer…");
        updateNotification("Finding computer…");
        discoveryListener = new NsdManager.DiscoveryListener() {
            @Override public void onDiscoveryStarted(String serviceType) { }

            @Override public void onServiceFound(NsdServiceInfo service) {
                if (!service.getServiceType().startsWith("_sleeptight._tcp")) return;
                nsdManager.resolveService(service, new NsdManager.ResolveListener() {
                    @Override public void onResolveFailed(NsdServiceInfo info, int errorCode) {
                        handler.postDelayed(rediscover, 3000);
                    }

                    @Override public void onServiceResolved(NsdServiceInfo info) {
                        if (info.getHost() == null || info.getPort() <= 0) return;
                        String host = info.getHost().getHostAddress();
                        if (host.contains(":")) host = "[" + host + "]";
                        url = "ws://" + host + ":" + info.getPort();
                        stopDiscovery();
                        connect();
                    }
                });
            }

            @Override public void onServiceLost(NsdServiceInfo service) { }
            @Override public void onDiscoveryStopped(String serviceType) { }
            @Override public void onStartDiscoveryFailed(String serviceType, int errorCode) {
                stopDiscovery();
                handler.postDelayed(rediscover, 5000);
            }
            @Override public void onStopDiscoveryFailed(String serviceType, int errorCode) { }
        };
        try {
            nsdManager.discoverServices("_sleeptight._tcp.", NsdManager.PROTOCOL_DNS_SD, discoveryListener);
        } catch (RuntimeException error) {
            Log.w(TAG, "Discovery failed", error);
            handler.postDelayed(rediscover, 5000);
        }
    }

    private void stopDiscovery() {
        NsdManager.DiscoveryListener current = discoveryListener;
        discoveryListener = null;
        if (current == null || nsdManager == null) return;
        try { nsdManager.stopServiceDiscovery(current); }
        catch (RuntimeException ignored) { }
    }

    private void connect() {
        if (stopping) return;
        handler.removeCallbacks(reconnect);
        WebSocket previous = socket;
        socket = null;
        if (previous != null) previous.cancel();
        socketOpen = false;
        broadcastStatus("Connecting to computer…");
        Request request;
        try {
            request = new Request.Builder().url(url).header("Authorization", "Bearer " + token).build();
        } catch (IllegalArgumentException error) {
            broadcastStatus("Invalid WebSocket URL");
            return;
        }
        socket = client.newWebSocket(request, new WebSocketListener() {
            @Override public void onOpen(WebSocket webSocket, Response response) {
                if (socket != webSocket || stopping) {
                    webSocket.close(1000, "superseded");
                    return;
                }
                socketOpen = true;
                if (scheduledCapture) reportCaptureProgress();
                else {
                    broadcastStatus("Connected — ready");
                    updateNotification("Connected — ready");
                    saveTileStatus("Connected", 0);
                }
                webSocket.send("{\"type\":\"hello\",\"device\":\"galaxy-watch\",\"schema\":1}");
            }

            @Override public void onMessage(WebSocket webSocket, String text) {
                if (socket != webSocket || stopping) return;
                try {
                    JSONObject body = new JSONObject(text);
                    if (!"ingest_ack".equals(body.optString("type")) ||
                            !"watch".equals(body.optString("source")) ||
                            !body.optBoolean("accepted")) return;
                    String localTime = DateTimeFormatter.ofPattern("HH:mm:ss")
                            .withZone(ZoneId.systemDefault())
                            .format(Instant.parse(body.getString("received_at")));
                    String confirmed = "Updated " + localTime;
                    getSharedPreferences("settings", MODE_PRIVATE).edit()
                            .putString("last_upload_at", body.getString("received_at"))
                            .apply();
                    broadcastStatus(confirmed + " • Mac confirmed over Wi-Fi");
                    updateNotification(confirmed + " • Mac confirmed");
                    saveTileStatus(confirmed, lastSummaryBpm);
                    if (scheduledOnly) handler.postDelayed(HeartRateService.this::stopSelf, 500);
                } catch (Exception error) {
                    Log.w(TAG, "Could not read Mac acknowledgement", error);
                }
            }

            @Override public void onFailure(WebSocket webSocket, Throwable error, Response response) {
                // cancel() on a superseded socket invokes this callback. It must not
                // clear or reconnect the newer, healthy socket.
                if (stopping || socket != webSocket) return;
                socketOpen = false;
                socket = null;
                Log.w(TAG, "WebSocket failed", error);
                if (scheduledCapture) reportCaptureProgress();
                else broadcastStatus("Disconnected — retrying");
                updateNotification("Disconnected — retrying");
                handler.removeCallbacks(reconnect);
                handler.postDelayed(autoDiscovery ? rediscover : reconnect, 5000);
            }

            @Override public void onClosed(WebSocket webSocket, int code, String reason) {
                if (stopping || socket != webSocket) return;
                socketOpen = false;
                socket = null;
                handler.postDelayed(autoDiscovery ? rediscover : reconnect, 5000);
            }
        });
    }

    @Override public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() != Sensor.TYPE_HEART_RATE || event.values.length == 0) return;
        float bpm = event.values[0];
        Intent update = new Intent(ACTION_HEART_RATE).setPackage(getPackageName()).putExtra(EXTRA_BPM, bpm);
        sendBroadcast(update);

        long now = SystemClock.elapsedRealtime();
        if (bpm > 0 && now - lastTileAt >= 30_000) {
            lastTileAt = now;
            saveTileStatus("Connected", Math.round(bpm));
        }
        if (scheduledCapture && bpm > 0 && now - lastScheduledSampleAt >= 900) {
            scheduledSamples.add(bpm);
            lastScheduledSampleAt = now;
        }
        if (!socketOpen || bpm <= 0 || now - lastSentAt < 900) return;
        lastSentAt = now;
        try {
            JSONObject message = new JSONObject();
            message.put("schema", 1);
            message.put("type", "heart_rate");
            message.put("sequence", sequence.incrementAndGet());
            message.put("observed_at", Instant.now().toString());
            message.put("sensor_timestamp_ns", event.timestamp);
            message.put("bpm", Math.round(bpm * 10.0) / 10.0);
            message.put("accuracy", event.accuracy);
            if (scheduledCapture) message.put("capture_mode", manualCapture ? "manual_10_minute" : "scheduled_pre_bed");
            if (correlationId != null) message.put("correlation_id", correlationId);
            if (!socket.send(message.toString())) {
                socketOpen = false;
                broadcastStatus("Send failed — reconnecting");
            }
        } catch (Exception error) {
            Log.e(TAG, "Could not encode heart-rate event", error);
        }
    }

    private void sendPreBedSummary() {
        handler.removeCallbacks(captureProgress);
        List<Float> values;
        synchronized (scheduledSamples) { values = new ArrayList<>(scheduledSamples); }
        if (values.isEmpty()) {
            finishCaptureFailure(
                    "No heart-rate sample after capture • tighten watch and retry",
                    "No HR sample • retry");
            return;
        }
        if (!socketOpen) {
            if (SystemClock.elapsedRealtime() < uploadDeadlineElapsed) {
                broadcastStatus("Measured " + values.size() + " samples • connecting to Mac");
                updateNotification("Measurement ready — connecting to Mac…");
                handler.postDelayed(sendScheduledSummary, 2_000);
            } else {
                finishCaptureFailure(
                        "Measured " + values.size() + " samples • Mac unavailable • retry",
                        "Mac unavailable • retry");
            }
            return;
        }
        Collections.sort(values);
        double sum = 0;
        for (float value : values) sum += value;
        lastSummaryBpm = Math.round(values.get(values.size() / 2));
        try {
            JSONObject message = new JSONObject();
            message.put("schema", 1);
            message.put("type", "pre_bed_summary");
            message.put("window_start", (scheduledWindowStart == null ? Instant.now() : scheduledWindowStart).toString());
            message.put("window_end", Instant.now().toString());
            message.put("sample_count", values.size());
            message.put("min_bpm", Math.round(values.get(0) * 10.0) / 10.0);
            message.put("max_bpm", Math.round(values.get(values.size() - 1) * 10.0) / 10.0);
            message.put("mean_bpm", Math.round((sum / values.size()) * 10.0) / 10.0);
            message.put("median_bpm", Math.round(values.get(values.size() / 2) * 10.0) / 10.0);
            message.put("scheduled", true);
            message.put("manual", manualCapture);
            message.put("capture_mode", manualCapture ? "manual_10_minute" : "scheduled_pre_bed");
            if (correlationId != null) message.put("correlation_id", correlationId);
            if (!socket.send(message.toString())) {
                socketOpen = false;
                if (SystemClock.elapsedRealtime() < uploadDeadlineElapsed) {
                    broadcastStatus("Measurement ready • reconnecting to Mac");
                    handler.postDelayed(sendScheduledSummary, 2_000);
                } else {
                    finishCaptureFailure("Measurement complete • send failed • retry", "Send failed • retry");
                }
                return;
            }
        } catch (Exception error) {
            Log.e(TAG, "Could not encode pre-bed summary", error);
        }
        scheduledCapture = false;
        scheduledSamples.clear();
        broadcastStatus("Sent over Wi-Fi • waiting for Mac confirmation");
        updateNotification("Waiting for Mac confirmation…");
        completedCapture = true;
        saveTileStatus("Awaiting Mac", lastSummaryBpm);
        if (getSharedPreferences("settings", MODE_PRIVATE).getBoolean("bedtime_schedule_enabled", false)) {
            BedtimeAlarmReceiver.scheduleNext(this);
        }
        manualCapture = false;
        correlationId = null;
        if (scheduledOnly) handler.postDelayed(() -> {
            saveTileStatus("Sent • confirm on Mac", lastSummaryBpm);
            stopSelf();
        }, 10_000);
    }

    private void reportCaptureProgress() {
        if (!scheduledCapture || stopping) return;
        long millis = Math.max(0L, captureDeadlineElapsed - SystemClock.elapsedRealtime());
        long seconds = (millis + 999L) / 1_000L;
        int count;
        synchronized (scheduledSamples) { count = scheduledSamples.size(); }
        String connection = socketOpen ? "Mac connected" : "finding Mac";
        String status = seconds > 0
                ? "Measuring " + seconds + " sec • " + count + " samples • " + connection
                : "Finalising " + count + " samples";
        broadcastStatus(status);
        updateNotification(status);
        if (seconds > 0) handler.postDelayed(captureProgress, 1_000L);
    }

    private void finishCaptureFailure(String status, String tileStatus) {
        handler.removeCallbacks(captureProgress);
        handler.removeCallbacks(sendScheduledSummary);
        scheduledCapture = false;
        scheduledSamples.clear();
        completedCapture = true;
        broadcastStatus(status);
        updateNotification(status);
        saveTileStatus(tileStatus, -1);
        if (getSharedPreferences("settings", MODE_PRIVATE).getBoolean("bedtime_schedule_enabled", false)) {
            BedtimeAlarmReceiver.scheduleNext(this);
        }
        manualCapture = false;
        correlationId = null;
        if (scheduledOnly) handler.postDelayed(this::stopSelf, 1_500L);
    }

    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) { }

    private void broadcastStatus(String value) {
        sendBroadcast(new Intent(ACTION_STATUS).setPackage(getPackageName()).putExtra(EXTRA_STATUS, value));
    }

    private void createNotificationChannel() {
        NotificationChannel channel = new NotificationChannel(CHANNEL, "Vitals sync", NotificationManager.IMPORTANCE_LOW);
        getSystemService(NotificationManager.class).createNotificationChannel(channel);
    }

    private Notification notification(String status) {
        return new Notification.Builder(this, CHANNEL)
                .setContentTitle("Sleep Tight Sync")
                .setContentText(status)
                .setSmallIcon(android.R.drawable.ic_menu_info_details)
                .setOngoing(true)
                .build();
    }

    private void updateNotification(String status) {
        getSystemService(NotificationManager.class).notify(NOTIFICATION_ID, notification(status));
    }

    private void saveTileStatus(String status, int bpm) {
        var edit = getSharedPreferences("settings", MODE_PRIVATE).edit().putString("tile_status", status);
        if (bpm > 0) edit.putInt("tile_bpm", bpm);
        else if (bpm < 0) edit.putInt("tile_bpm", 0);
        edit.apply();
        androidx.wear.tiles.TileService.getUpdater(this).requestUpdate(SleepTightTileService.class);
    }

    @Override public void onDestroy() {
        stopping = true;
        handler.removeCallbacksAndMessages(null);
        stopDiscovery();
        if (sensorManager != null) sensorManager.unregisterListener(this);
        WebSocket current = socket;
        if (current != null) current.close(1000, "stopped");
        socket = null;
        socketOpen = false;
        if (!completedCapture) saveTileStatus("Stopped", -1);
        if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
        client.dispatcher().executorService().shutdown();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
