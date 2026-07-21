package com.sleeptight.heartrate;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class BootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (context.getSharedPreferences("settings", Context.MODE_PRIVATE).getBoolean("bedtime_schedule_enabled", false)) {
            BedtimeAlarmReceiver.scheduleNext(context);
        }
    }
}
