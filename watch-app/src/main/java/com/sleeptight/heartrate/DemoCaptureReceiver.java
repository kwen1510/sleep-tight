package com.sleeptight.heartrate;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** ADB-shell-only entry point for short, clock-safe demonstrations. */
public final class DemoCaptureReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        long requested = intent == null ? 600_000L : intent.getLongExtra("duration_ms", 600_000L);
        long duration = Math.max(30_000L, Math.min(requested, 600_000L));
        Intent service = new Intent(context, HeartRateService.class)
                .putExtra("scheduled_capture", true)
                .putExtra("summary_after_ms", duration);
        context.startForegroundService(service);
    }
}
