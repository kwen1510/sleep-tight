package com.sleeptight.heartrate;

import android.Manifest;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.InputDevice;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Space;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.EditText;
import android.widget.Toast;

import com.google.android.gms.wearable.MessageClient;
import com.google.android.gms.wearable.MessageEvent;
import com.google.android.gms.wearable.Wearable;

import org.json.JSONObject;

import java.time.Instant;
import java.util.UUID;

public final class MainActivity extends Activity implements MessageClient.OnMessageReceivedListener {
    private static final int REQUEST_SENSORS = 1;
    private static final int REQUEST_BACKGROUND = 2;
    private static final int REQUEST_NOTIFICATIONS = 3;
    private static final int REQUEST_HEART_RATE = 4;
    private static final String READ_HEART_RATE = "android.permission.health.READ_HEART_RATE";

    private TextView heartRateText;
    private TextView statusText;
    private ScrollView scrollView;
    private String connectionUrl;
    private String pairingToken;
    private boolean receiverRegistered;
    private Runnable pendingPermissionAction;
    private boolean syncScreenLockActive;
    private final Runnable releaseSyncScreenLock = this::unlockSyncScreen;

    private final BroadcastReceiver updates = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (HeartRateService.ACTION_HEART_RATE.equals(intent.getAction())) {
                heartRateText.setText(String.valueOf(Math.round(intent.getFloatExtra(HeartRateService.EXTRA_BPM, 0))));
            } else if (HeartRateService.ACTION_STATUS.equals(intent.getAction())) {
                String value = intent.getStringExtra(HeartRateService.EXTRA_STATUS);
                statusText.setText(displayStatus(value));
                if (isTerminalSyncStatus(value)) unlockSyncScreen();
            }
        }
    };

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        SharedPreferences prefs = getSharedPreferences("settings", MODE_PRIVATE);
        connectionUrl = prefs.getString("url", "auto://sleep-tight");
        pairingToken = prefs.getString("token", "");
        if (!prefs.contains("bedtime_schedule_enabled")) {
            prefs.edit().putInt("bedtime_hour", 21).putInt("bedtime_minute", 55)
                    .putBoolean("bedtime_schedule_enabled", true).apply();
        }
        if (prefs.getBoolean("bedtime_schedule_enabled", false)) {
            BedtimeAlarmReceiver.scheduleNext(this);
        }

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setGravity(Gravity.CENTER_HORIZONTAL);
        content.setPadding(dp(28), dp(16), dp(28), dp(42));

        TextView title = text("SLEEP TIGHT", 13);
        title.setTextColor(Color.rgb(255, 157, 105));
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setLetterSpacing(0.18f);
        title.setPadding(0, 0, 0, 0);
        TextView subtitle = text("VITALS PUSH", 10);
        subtitle.setTextColor(Color.rgb(126, 119, 125));
        subtitle.setLetterSpacing(0.12f);
        subtitle.setPadding(0, 0, 0, 0);
        heartRateText = text("--", 64);
        heartRateText.setTypeface(Typeface.create("sans-serif-light", Typeface.NORMAL));
        heartRateText.setPadding(0, 0, 0, 0);
        TextView bpmLabel = text("BEATS PER MINUTE", 9);
        bpmLabel.setTextColor(Color.rgb(126, 119, 125));
        bpmLabel.setLetterSpacing(0.12f);
        bpmLabel.setPadding(0, 0, 0, 0);
        statusText = text(displayStatus(prefs.getString("tile_status", "Stopped")), 12);
        statusText.setTextColor(Color.rgb(232, 220, 214));
        statusText.setTypeface(Typeface.DEFAULT_BOLD);
        statusText.setLetterSpacing(0.06f);
        statusText.setBackground(roundRect(0xFF1B181B, 0, 22));
        statusText.setPadding(dp(16), dp(10), dp(16), dp(10));
        Button updateNow = button("Sync data to Mac", true);
        EditText bedtime = new EditText(this);
        bedtime.setHint("Daily update HH:mm");
        bedtime.setText(String.format(java.util.Locale.US, "%02d:%02d", prefs.getInt("bedtime_hour", 21), prefs.getInt("bedtime_minute", 55)));
        bedtime.setTextColor(Color.WHITE);
        bedtime.setHintTextColor(Color.rgb(126, 119, 125));
        bedtime.setGravity(Gravity.CENTER);
        bedtime.setSingleLine(true);
        bedtime.setLayoutParams(fullWidth());
        Button schedule = button("Save daily 21:55 update", false);
        TextView connection = text("●  AUTOMATIC LOCAL CONNECTION", 10);
        connection.setTextColor(Color.rgb(126, 119, 125));
        connection.setLetterSpacing(0.05f);
        TextView privacy = text("A bounded heart-rate sample is sent only when you tap Sync Data or at 21:55.", 11);
        privacy.setTextColor(Color.rgb(101, 96, 101));

        content.addView(title);
        content.addView(subtitle);
        content.addView(space(12));
        content.addView(heartRateText);
        content.addView(bpmLabel);
        content.addView(space(12));
        content.addView(statusText);
        content.addView(space(22));
        content.addView(updateNow);
        content.addView(space(18));
        content.addView(bedtime);
        content.addView(space(8));
        content.addView(schedule);
        content.addView(space(22));
        content.addView(connection);
        content.addView(space(8));
        content.addView(privacy);

        scrollView = new ScrollView(this);
        scrollView.addView(content);
        setContentView(scrollView);

        updateNow.setOnClickListener(v -> prepareManualUpdate());
        schedule.setOnClickListener(v -> {
            try {
                java.time.LocalTime parsed = java.time.LocalTime.parse(bedtime.getText().toString().trim());
                continueAfterPermissions(() -> {
                    prefs.edit().putInt("bedtime_hour", parsed.getHour()).putInt("bedtime_minute", parsed.getMinute())
                            .putBoolean("bedtime_schedule_enabled", true).apply();
                    java.time.ZonedDateTime next = BedtimeAlarmReceiver.scheduleNext(this);
                    statusText.setText("SCHEDULED • " + next.toLocalTime() + " SAMPLE");
                    if (Build.VERSION.SDK_INT >= 31 && !getSystemService(android.app.AlarmManager.class).canScheduleExactAlarms()) {
                        startActivity(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:" + getPackageName())));
                    }
                });
            } catch (Exception error) {
                Toast.makeText(this, "Use a 24-hour time such as 21:55", Toast.LENGTH_LONG).show();
            }
        });

        if (getIntent().getBooleanExtra("tile_sync", false)) {
            content.post(this::prepareManualUpdate);
        }
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (intent.getBooleanExtra("tile_sync", false)) heartRateText.post(this::prepareManualUpdate);
    }

    private void prepareManualUpdate() {
        String url = connectionUrl.trim();
        String token = pairingToken.trim();
        if (!(url.startsWith("ws://") || url.startsWith("wss://") || url.startsWith("auto://")) || token.isEmpty()) {
            Toast.makeText(this, "Connection settings are incomplete", Toast.LENGTH_LONG).show();
            return;
        }
        getSharedPreferences("settings", MODE_PRIVATE).edit().putString("url", url).putString("token", token).apply();
        continueAfterPermissions(this::startManualUpdate);
    }

    private void startManualUpdate() {
        String correlationId = "watch-" + Instant.now().getEpochSecond() + "-" + UUID.randomUUID().toString().substring(0, 6);
        lockScreenForSync();
        statusText.setText("REQUESTING PHONE • MEASURING 10 MIN");
        try {
            JSONObject request = new JSONObject().put("correlation_id", correlationId).put("requested_at", Instant.now().toString());
            byte[] data = request.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
            Wearable.getNodeClient(this).getConnectedNodes()
                    .addOnSuccessListener(nodes -> {
                        if (nodes.isEmpty()) {
                            statusText.setText("PHONE UNAVAILABLE • USE PHONE BUTTON");
                            return;
                        }
                        for (var node : nodes) {
                            Wearable.getMessageClient(this).sendMessage(node.getId(), "/sleep-tight/sync-now", data)
                                    .addOnFailureListener(error -> statusText.setText("PHONE REQUEST FAILED • USE PHONE BUTTON"));
                        }
                    })
                    .addOnFailureListener(error -> statusText.setText("PHONE UNAVAILABLE • USE PHONE BUTTON"));
        } catch (Exception error) {
            statusText.setText("PHONE REQUEST FAILED • USE PHONE BUTTON");
        }
        Intent service = new Intent(this, HeartRateService.class)
                .putExtra("url", connectionUrl.trim())
                .putExtra("token", pairingToken.trim())
                .putExtra("scheduled_capture", true)
                .putExtra("manual_capture", true)
                .putExtra("correlation_id", correlationId)
                .putExtra("summary_after_ms", 600_000L);
        startForegroundService(service);
    }

    private void lockScreenForSync() {
        syncScreenLockActive = true;
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (Build.VERSION.SDK_INT >= 27) setTurnScreenOn(true);
        statusText.removeCallbacks(releaseSyncScreenLock);
        // The capture is 10 minutes and upload grace is 15 seconds. This final
        // timeout guarantees the display is never held awake indefinitely.
        statusText.postDelayed(releaseSyncScreenLock, 620_000L);
    }

    private void unlockSyncScreen() {
        if (!syncScreenLockActive) return;
        syncScreenLockActive = false;
        statusText.removeCallbacks(releaseSyncScreenLock);
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }

    private boolean isTerminalSyncStatus(String value) {
        if (value == null) return false;
        return value.startsWith("Updated ") ||
                value.startsWith("No heart-rate sample") ||
                value.contains("Mac unavailable") ||
                value.contains("send failed") ||
                value.startsWith("Could not start heart-rate sensor") ||
                value.startsWith("Heart-rate sensor unavailable") ||
                value.startsWith("Missing connection settings");
    }

    @Override public void onMessageReceived(MessageEvent event) {
        if (!"/sleep-tight/sync-status".equals(event.getPath())) return;
        runOnUiThread(() -> {
            try {
                JSONObject body = new JSONObject(new String(event.getData(), java.nio.charset.StandardCharsets.UTF_8));
                String state = body.optString("state", "unknown");
                if ("uploaded".equals(state)) statusText.setText("PHONE VITALS SENT • WATCH MEASURING");
                else if ("accepted".equals(state)) statusText.setText("PHONE READING HISTORY • WATCH MEASURING");
                else if ("failed".equals(state)) statusText.setText("PHONE SYNC FAILED • USE PHONE BUTTON");
            } catch (Exception ignored) { }
        });
    }

    private void continueAfterPermissions(Runnable action) {
        pendingPermissionAction = action;
        if (Build.VERSION.SDK_INT >= 35 &&
                checkSelfPermission(READ_HEART_RATE) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{READ_HEART_RATE}, REQUEST_HEART_RATE);
            return;
        }
        if (checkSelfPermission(Manifest.permission.BODY_SENSORS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.BODY_SENSORS}, REQUEST_SENSORS);
            return;
        }
        if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.BODY_SENSORS_BACKGROUND) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.BODY_SENSORS_BACKGROUND}, REQUEST_BACKGROUND);
            return;
        }
        if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQUEST_NOTIFICATIONS);
            return;
        }
        pendingPermissionAction = null;
        action.run();
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            Runnable action = pendingPermissionAction;
            if (action != null) continueAfterPermissions(action);
            return;
        }
        if (requestCode == REQUEST_BACKGROUND) {
            Toast.makeText(this, "Set Sensors to ‘Allow all the time’ for overnight tracking", Toast.LENGTH_LONG).show();
            Intent settings = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()));
            startActivity(settings);
        } else {
            Toast.makeText(this, "Permission is required", Toast.LENGTH_LONG).show();
        }
    }

    @Override protected void onResume() {
        super.onResume();
        Wearable.getMessageClient(this).addListener(this);
        if (!receiverRegistered) {
            IntentFilter filter = new IntentFilter();
            filter.addAction(HeartRateService.ACTION_HEART_RATE);
            filter.addAction(HeartRateService.ACTION_STATUS);
            registerReceiver(updates, filter, Context.RECEIVER_NOT_EXPORTED);
            receiverRegistered = true;
        }
    }

    @Override protected void onPause() {
        Wearable.getMessageClient(this).removeListener(this);
        if (receiverRegistered) {
            unregisterReceiver(updates);
            receiverRegistered = false;
        }
        super.onPause();
    }

    @Override protected void onDestroy() {
        if (statusText != null) statusText.removeCallbacks(releaseSyncScreenLock);
        super.onDestroy();
    }

    @Override public boolean dispatchGenericMotionEvent(MotionEvent event) {
        if (scrollView != null && event.getAction() == MotionEvent.ACTION_SCROLL &&
                (event.getSource() & InputDevice.SOURCE_ROTARY_ENCODER) != 0) {
            scrollView.scrollBy(0, Math.round(-event.getAxisValue(MotionEvent.AXIS_SCROLL) * dp(48)));
            return true;
        }
        return super.dispatchGenericMotionEvent(event);
    }

    private TextView text(String value, float size) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextColor(Color.WHITE);
        view.setTextSize(size);
        view.setGravity(Gravity.CENTER);
        view.setPadding(0, dp(6), 0, dp(6));
        view.setLayoutParams(fullWidth());
        return view;
    }

    private Space space(int height) {
        Space view = new Space(this);
        view.setLayoutParams(new LinearLayout.LayoutParams(1, dp(height)));
        return view;
    }

    private Button button(String label, boolean primary) {
        Button view = new Button(this);
        view.setText(label);
        view.setAllCaps(false);
        view.setTextSize(14);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setTextColor(primary ? 0xFF171115 : 0xFFF2E8E2);
        view.setBackground(roundRect(primary ? 0xFFFF9D69 : 0xFF171417, primary ? 0 : 0xFF41383D, 28));
        view.setMinHeight(dp(58));
        view.setLayoutParams(fullWidth());
        return view;
    }

    private GradientDrawable roundRect(int fill, int stroke, int radiusDp) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(fill);
        shape.setCornerRadius(dp(radiusDp));
        if (stroke != 0) shape.setStroke(dp(1), stroke);
        return shape;
    }

    private String displayStatus(String status) {
        if (status == null) return "READY WHEN YOU ARE";
        if (status.startsWith("Connected")) return "CONNECTED • LIVE";
        if (status.startsWith("Finding")) return "LOOKING FOR YOUR MAC…";
        if (status.startsWith("Connecting")) return "CONNECTING…";
        if (status.startsWith("Disconnected")) return "RECONNECTING…";
        if (status.startsWith("Stopped") || status.startsWith("Tap")) return "STOPPED • NO DATA COLLECTION";
        return status.toUpperCase();
    }

    private LinearLayout.LayoutParams fullWidth() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
