package com.sleeptight.sync

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.time.Duration
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

object SyncEngine {
    private val client = OkHttpClient()

    suspend fun run(
        context: Context,
        manual: Boolean = false,
        correlationId: String? = null,
        trigger: String = if (manual) "phone_button" else "scheduled"
    ): String = withContext(Dispatchers.IO) {
        val settings = SyncSettings.load(context)
        require(settings.token.isNotBlank()) { "Pairing token is empty" }
        val base = ApiDiscovery.resolve(context, settings.apiUrl)
        val lookback = if (manual) Duration.ofHours(24) else Duration.ofDays(8)
        val payload = HealthConnectExporter.export(context, lookback, correlationId, trigger).toString()
        val request = Request.Builder()
            .url("$base/api/v1/ingest/health")
            .header("Authorization", "Bearer ${settings.token}")
            .post(payload.toRequestBody("application/json".toMediaType()))
            .build()
        client.newCall(request).execute().use { response ->
            val body = response.body.string()
            check(response.isSuccessful) { "Mac returned ${response.code}: $body" }
            val acknowledgement = JSONObject(body)
            check(acknowledgement.optBoolean("accepted")) { "Mac did not accept this upload" }
            val receivedAt = Instant.parse(acknowledgement.getString("received_at"))
            val localTime = DateTimeFormatter.ofPattern("d MMM, HH:mm:ss")
                .withZone(ZoneId.systemDefault()).format(receivedAt)
            val total = acknowledgement.optInt("total_records", 0)
            val message = "Updated at $localTime over Wi-Fi · $total records"
            SyncSettings.saveLastReceipt(context, message)
            SyncScheduler.scheduleNext(context)
            message
        }
    }
}
