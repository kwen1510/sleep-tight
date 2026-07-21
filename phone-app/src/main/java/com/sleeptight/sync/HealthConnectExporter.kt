package com.sleeptight.sync

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.*
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import org.json.JSONArray
import org.json.JSONObject
import java.time.Duration
import java.time.Instant
import kotlin.reflect.KClass

object HealthConnectExporter {
    val recordTypes: Set<KClass<out Record>> = setOf(
        SleepSessionRecord::class, HeartRateRecord::class, RestingHeartRateRecord::class,
        StepsRecord::class, ExerciseSessionRecord::class, ActiveCaloriesBurnedRecord::class,
        TotalCaloriesBurnedRecord::class, OxygenSaturationRecord::class,
        RespiratoryRateRecord::class, SkinTemperatureRecord::class, FloorsClimbedRecord::class
    )
    val permissions: Set<String> = recordTypes.map(HealthPermission::getReadPermission).toSet() +
        HealthPermission.PERMISSION_READ_HEALTH_DATA_IN_BACKGROUND

    suspend fun export(
        context: Context,
        lookback: Duration = Duration.ofDays(8),
        correlationId: String? = null,
        trigger: String = "scheduled"
    ): JSONObject {
        val client = HealthConnectClient.getOrCreate(context)
        val granted = client.permissionController.getGrantedPermissions()
        val end = Instant.now()
        val start = end.minus(lookback)
        val recentStart = if (lookback <= Duration.ofDays(1)) start else end.minus(Duration.ofDays(2))
        val device = JSONObject()
            .put("platform", "android")
            .put("sdk", android.os.Build.VERSION.SDK_INT)
            .put("trigger", trigger)
            .put("manual", trigger != "scheduled")
        if (!correlationId.isNullOrBlank()) device.put("correlation_id", correlationId)
        val root = JSONObject()
            .put("schema", 1).put("type", "health_sync").put("source", "health_connect")
            .put("generated_at", end.toString()).put("window_start", start.toString())
            .put("window_end", end.toString())
            .put("device", device)
        val permissionJson = JSONObject()
        recordTypes.forEach { permissionJson.put(it.simpleName ?: it.qualifiedName ?: "unknown", granted.contains(HealthPermission.getReadPermission(it))) }
        permissionJson.put("background_read", granted.contains(HealthPermission.PERMISSION_READ_HEALTH_DATA_IN_BACKGROUND))
        root.put("permissions", permissionJson)
        val errors = JSONObject()

        root.put("sleep_sessions", safeRead(client, SleepSessionRecord::class, start, end, granted, errors, "sleep_sessions").mapJson { sleep(it) })
        root.put("heart_rate_samples", safeRead(client, HeartRateRecord::class, recentStart, end, granted, errors, "heart_rate_samples").flatMap { record ->
            record.samples.map { sample -> JSONObject().put("record_id", "${record.metadata.id}:${sample.time}").put("time", sample.time.toString()).put("bpm", sample.beatsPerMinute).put("source", record.metadata.dataOrigin.packageName) }
        }.takeLast(20_000).toJsonArray())
        root.put("resting_heart_rate_records", safeRead(client, RestingHeartRateRecord::class, start, end, granted, errors, "resting_heart_rate_records").mapJson {
            JSONObject().put("record_id", it.metadata.id).put("time", it.time.toString()).put("bpm", it.beatsPerMinute).put("source", it.metadata.dataOrigin.packageName)
        })
        root.put("steps_records", safeRead(client, StepsRecord::class, start, end, granted, errors, "steps_records").mapJson {
            interval(it.startTime, it.endTime, it.metadata.dataOrigin.packageName).put("record_id", it.metadata.id).put("count", it.count)
        })
        root.put("exercise_sessions", safeRead(client, ExerciseSessionRecord::class, start, end, granted, errors, "exercise_sessions").mapJson {
            interval(it.startTime, it.endTime, it.metadata.dataOrigin.packageName).put("record_id", it.metadata.id).put("exercise_type", it.exerciseType).put("title", it.title)
        })
        root.put("active_calories_records", safeRead(client, ActiveCaloriesBurnedRecord::class, start, end, granted, errors, "active_calories_records").mapJson {
            interval(it.startTime, it.endTime, it.metadata.dataOrigin.packageName).put("record_id", it.metadata.id).put("kilocalories", it.energy.inKilocalories)
        })
        root.put("total_calories_records", safeRead(client, TotalCaloriesBurnedRecord::class, start, end, granted, errors, "total_calories_records").mapJson {
            interval(it.startTime, it.endTime, it.metadata.dataOrigin.packageName).put("record_id", it.metadata.id).put("kilocalories", it.energy.inKilocalories)
        })
        root.put("oxygen_saturation_samples", safeRead(client, OxygenSaturationRecord::class, start, end, granted, errors, "oxygen_saturation_samples").mapJson {
            JSONObject().put("record_id", it.metadata.id).put("time", it.time.toString()).put("percentage", it.percentage.value).put("source", it.metadata.dataOrigin.packageName)
        })
        root.put("respiratory_rate_samples", safeRead(client, RespiratoryRateRecord::class, start, end, granted, errors, "respiratory_rate_samples").mapJson {
            JSONObject().put("record_id", it.metadata.id).put("time", it.time.toString()).put("breaths_per_minute", it.rate).put("source", it.metadata.dataOrigin.packageName)
        })
        root.put("skin_temperature_records", safeRead(client, SkinTemperatureRecord::class, start, end, granted, errors, "skin_temperature_records").mapJson {
            interval(it.startTime, it.endTime, it.metadata.dataOrigin.packageName).put("record_id", it.metadata.id)
                .put("baseline_celsius", it.baseline?.inCelsius)
                .put("deltas", JSONArray(it.deltas.map { delta -> JSONObject().put("time", delta.time.toString()).put("celsius", delta.delta.inCelsius) }))
        })
        root.put("floors_climbed_records", safeRead(client, FloorsClimbedRecord::class, start, end, granted, errors, "floors_climbed_records").mapJson {
            interval(it.startTime, it.endTime, it.metadata.dataOrigin.packageName).put("record_id", it.metadata.id).put("floors", it.floors)
        })
        root.put("extraction_errors", errors)
        root.put("attempted_categories", JSONArray(listOf(
            "sleep_sessions", "heart_rate_samples", "resting_heart_rate_records", "steps_records",
            "exercise_sessions", "active_calories_records", "total_calories_records",
            "oxygen_saturation_samples", "respiratory_rate_samples", "skin_temperature_records",
            "floors_climbed_records"
        )))
        return root
    }

    private suspend fun <T : Record> safeRead(
        client: HealthConnectClient, type: KClass<T>, start: Instant, end: Instant,
        granted: Set<String>, errors: JSONObject, category: String
    ): List<T> = try {
        read(client, type, start, end, granted)
    } catch (error: Exception) {
        errors.put(category, "${error.javaClass.simpleName}: ${error.message ?: "read failed"}")
        emptyList()
    }

    private suspend fun <T : Record> read(client: HealthConnectClient, type: KClass<T>, start: Instant, end: Instant, granted: Set<String>): List<T> {
        if (!granted.contains(HealthPermission.getReadPermission(type))) return emptyList()
        val all = mutableListOf<T>()
        var token: String? = null
        do {
            val page = client.readRecords(ReadRecordsRequest(type, TimeRangeFilter.between(start, end), pageSize = 1000, pageToken = token))
            all += page.records
            token = page.pageToken
        } while (token != null)
        return all
    }

    private fun sleep(record: SleepSessionRecord): JSONObject {
        val stages = JSONArray(record.stages.map {
            JSONObject().put("start_time", it.startTime.toString()).put("end_time", it.endTime.toString()).put("stage", it.stage)
        })
        return interval(record.startTime, record.endTime, record.metadata.dataOrigin.packageName)
            .put("record_id", record.metadata.id)
            .put("duration_minutes", Duration.between(record.startTime, record.endTime).toMinutes())
            .put("score", JSONObject.NULL).put("title", record.title).put("notes", record.notes).put("stages", stages)
    }

    private fun interval(start: Instant, end: Instant, source: String) = JSONObject()
        .put("start_time", start.toString()).put("end_time", end.toString()).put("source", source)

    private fun <T> List<T>.mapJson(block: (T) -> JSONObject) = map(block).toJsonArray()
    private fun List<JSONObject>.toJsonArray() = JSONArray(this)
}
