package com.sleeptight.sync

import android.content.Context
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.Wearable
import com.google.android.gms.wearable.WearableListenerService
import org.json.JSONObject
import java.time.Instant

class WatchSyncListenerService : WearableListenerService() {
    override fun onMessageReceived(event: MessageEvent) {
        if (event.path != REQUEST_PATH) return
        val body = try { JSONObject(String(event.data, Charsets.UTF_8)) } catch (_: Exception) { JSONObject() }
        val correlationId = body.optString("correlation_id").ifBlank { "watch-${Instant.now().epochSecond}" }
        reply(this, event.sourceNodeId, correlationId, "accepted", "Phone is reading the last 24 hours")
        SyncScheduler.runManual(this, correlationId, "watch_button", event.sourceNodeId)
    }

    companion object {
        const val REQUEST_PATH = "/sleep-tight/sync-now"
        const val REPLY_PATH = "/sleep-tight/sync-status"

        fun reply(context: Context, nodeId: String, correlationId: String, state: String, message: String) {
            val body = JSONObject()
                .put("correlation_id", correlationId)
                .put("state", state)
                .put("message", message.take(500))
                .put("at", Instant.now().toString())
                .toString().toByteArray(Charsets.UTF_8)
            Wearable.getMessageClient(context).sendMessage(nodeId, REPLY_PATH, body)
        }
    }
}
