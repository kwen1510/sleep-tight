package com.sleeptight.heartrate;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** ADB-shell-only foreground launcher for clock-safe demonstrations. */
public final class DemoCaptureActivity extends Activity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (getIntent().getBooleanExtra("configure_schedule", false)) {
            int hour = Math.max(0, Math.min(getIntent().getIntExtra("bedtime_hour", 21), 23));
            int minute = Math.max(0, Math.min(getIntent().getIntExtra("bedtime_minute", 55), 59));
            getSharedPreferences("settings", MODE_PRIVATE).edit()
                    .putInt("bedtime_hour", hour)
                    .putInt("bedtime_minute", minute)
                    .putBoolean("bedtime_schedule_enabled", true)
                    .apply();
            BedtimeAlarmReceiver.scheduleNext(this);
            finish();
            return;
        }
        long requested = getIntent().getLongExtra("duration_ms", 600_000L);
        long duration = Math.max(30_000L, Math.min(requested, 600_000L));
        startForegroundService(new Intent(this, HeartRateService.class)
                .putExtra("scheduled_capture", true)
                .putExtra("summary_after_ms", duration));
        finish();
    }
}
