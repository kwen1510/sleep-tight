package com.sleeptight.sync

import android.content.Context
import java.time.LocalTime

data class SyncSettings(val apiUrl: String, val token: String, val syncTime: LocalTime) {
    companion object {
        private const val PREFS = "sleep_tight_sync"

        fun load(context: Context): SyncSettings {
            val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            return SyncSettings(
                prefs.getString("api_url", "auto://sleep-tight") ?: "auto://sleep-tight",
                prefs.getString("token", "") ?: "",
                LocalTime.parse(prefs.getString("sync_time", "21:55"))
            )
        }

        fun save(context: Context, value: SyncSettings) {
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString("api_url", value.apiUrl)
                .putString("token", value.token)
                .putString("sync_time", value.syncTime.toString())
                .apply()
        }

        fun saveLastReceipt(context: Context, value: String) {
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString("last_receipt", value)
                .apply()
        }

        fun lastReceipt(context: Context): String? =
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString("last_receipt", null)
    }
}
