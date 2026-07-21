package com.sleeptight.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.OutOfQuotaPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.time.Duration
import java.time.ZonedDateTime
import java.util.concurrent.TimeUnit

object SyncScheduler {
    private const val WORK = "sleep-tight-daily-health-sync"

    fun scheduleNext(context: Context): ZonedDateTime {
        val time = SyncSettings.load(context).syncTime
        val now = ZonedDateTime.now()
        var next = now.toLocalDate().atTime(time).atZone(now.zone)
        if (!next.isAfter(now.plusMinutes(1))) next = next.plusDays(1)
        val delay = Duration.between(now, next).toMillis()
        val request = OneTimeWorkRequestBuilder<HealthSyncWorker>()
            .setInitialDelay(delay, TimeUnit.MILLISECONDS)
            .setInputData(Data.Builder().putString("scheduled_for", next.toString()).build())
            .build()
        WorkManager.getInstance(context).enqueueUniqueWork(WORK, ExistingWorkPolicy.REPLACE, request)
        return next
    }

    fun runManual(context: Context, correlationId: String, trigger: String, replyNodeId: String? = null) {
        val input = Data.Builder()
            .putBoolean("manual", true)
            .putString("correlation_id", correlationId)
            .putString("trigger", trigger)
            .putString("reply_node_id", replyNodeId)
            .build()
        val request = OneTimeWorkRequestBuilder<HealthSyncWorker>()
            .setInputData(input)
            .setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST)
            .build()
        WorkManager.getInstance(context).enqueueUniqueWork(
            "sleep-tight-manual-$correlationId", ExistingWorkPolicy.KEEP, request
        )
    }
}

class HealthSyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result = try {
        val manual = inputData.getBoolean("manual", false)
        val correlationId = inputData.getString("correlation_id")
        val trigger = inputData.getString("trigger") ?: if (manual) "manual_worker" else "scheduled"
        val message = SyncEngine.run(applicationContext, manual, correlationId, trigger)
        inputData.getString("reply_node_id")?.let {
            WatchSyncListenerService.reply(applicationContext, it, correlationId ?: "unknown", "uploaded", message)
        }
        Result.success()
    } catch (error: Exception) {
        inputData.getString("reply_node_id")?.let {
            WatchSyncListenerService.reply(applicationContext, it, inputData.getString("correlation_id") ?: "unknown", "failed", error.message ?: "sync failed")
        }
        if (runAttemptCount < 3) Result.retry() else {
            SyncScheduler.scheduleNext(applicationContext)
            Result.failure(Data.Builder().putString("error", error.message).build())
        }
    }
}
