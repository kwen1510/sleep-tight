package com.sleeptight.heartrate;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import java.time.Duration;
import java.time.ZonedDateTime;

public final class BedtimeAlarmReceiver extends BroadcastReceiver {
    private static final int REQUEST_CODE = 2200;

    @Override public void onReceive(Context context, Intent intent) {
        scheduleNext(context);
        Intent service = new Intent(context, HeartRateService.class)
                .putExtra("scheduled_capture", true)
                .putExtra("summary_after_ms", 600_000L);
        context.startForegroundService(service);
    }

    public static ZonedDateTime scheduleNext(Context context) {
        var prefs = context.getSharedPreferences("settings", Context.MODE_PRIVATE);
        int hour = prefs.getInt("bedtime_hour", 21);
        int minute = prefs.getInt("bedtime_minute", 55);
        ZonedDateTime now = ZonedDateTime.now();
        ZonedDateTime capture = now.toLocalDate().atTime(hour, minute).atZone(now.getZone());
        if (!capture.isAfter(now.plusSeconds(30))) capture = capture.plusDays(1);
        AlarmManager alarms = context.getSystemService(AlarmManager.class);
        Intent intent = new Intent(context, BedtimeAlarmReceiver.class);
        PendingIntent pending = PendingIntent.getBroadcast(context, REQUEST_CODE, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        long trigger = capture.toInstant().toEpochMilli();
        if (Build.VERSION.SDK_INT < 31 || alarms.canScheduleExactAlarms()) {
            alarms.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pending);
        } else {
            alarms.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pending);
        }
        prefs.edit().putLong("next_capture_at", trigger).apply();
        return capture;
    }
}
