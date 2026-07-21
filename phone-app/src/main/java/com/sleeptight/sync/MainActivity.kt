package com.sleeptight.sync

import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Space
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.LocalTime

class MainActivity : ComponentActivity() {
    private val canvas = Color.rgb(8, 7, 10)
    private val surface = Color.rgb(23, 20, 23)
    private val surfaceRaised = Color.rgb(30, 26, 30)
    private val ink = Color.rgb(246, 237, 231)
    private val muted = Color.rgb(166, 157, 162)
    private val line = Color.rgb(65, 56, 61)
    private val accent = Color.rgb(255, 157, 105)
    private val success = Color.rgb(143, 212, 176)
    private val warning = Color.rgb(239, 194, 118)

    private lateinit var url: EditText
    private lateinit var token: EditText
    private lateinit var time: EditText
    private lateinit var syncTitle: TextView
    private lateinit var syncDetail: TextView
    private lateinit var syncDot: View
    private lateinit var permissionDetail: TextView
    private lateinit var scheduleDetail: TextView
    private lateinit var syncButton: Button
    private lateinit var connectionPanel: LinearLayout

    private val permissionLauncher = registerForActivityResult(
        PermissionController.createRequestPermissionResultContract()
    ) { updatePermissionStatus() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = canvas
        window.navigationBarColor = canvas
        val settings = SyncSettings.load(this)

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(28), dp(24), dp(40))
        }

        content.addView(text("SLEEP TIGHT", 12, accent, true).apply { letterSpacing = .18f })
        content.addView(text("Your day, safely synced.", 34, ink, true).apply {
            setPadding(0, dp(9), 0, 0)
        })
        content.addView(text(
            "Send the latest Health Connect records to your Mac over your private Wi-Fi.",
            16, muted, false
        ).apply { setPadding(0, dp(9), 0, dp(26)) })

        val statusCard = card().apply {
            addView(horizontal().apply {
                syncDot = View(this@MainActivity).apply {
                    background = circle(muted)
                    layoutParams = LinearLayout.LayoutParams(dp(10), dp(10)).apply { marginEnd = dp(12) }
                }
                addView(syncDot)
                addView(LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.VERTICAL
                    layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
                    syncTitle = text("Ready to sync", 18, ink, true)
                    syncDetail = text(SyncSettings.lastReceipt(this@MainActivity)
                        ?: "No upload has reached this Mac yet.", 13, muted, false).apply {
                        setPadding(0, dp(4), 0, 0)
                    }
                    addView(syncTitle)
                    addView(syncDetail)
                })
            })
        }
        content.addView(statusCard)

        syncButton = primaryButton("Sync data now") { save(); syncNow() }
        content.addView(syncButton)
        content.addView(text("Reads a rolling 24-hour window. Nothing is sent to a cloud account.", 12, muted, false).apply {
            gravity = Gravity.CENTER
            setPadding(dp(8), dp(10), dp(8), dp(26))
        })

        content.addView(sectionLabel("ACCESS"))
        val permissionCard = card().apply {
            permissionDetail = text("Checking Health Connect permissions…", 14, muted, false)
            addView(permissionDetail)
            addView(secondaryButton("Review health permissions") {
                permissionLauncher.launch(HealthConnectExporter.permissions)
            }.apply { layoutParams = fullWidth(dp(52)).apply { topMargin = dp(16) } })
        }
        content.addView(permissionCard)

        content.addView(sectionLabel("DAILY AUTOMATION").apply { setPadding(0, dp(28), 0, dp(10)) })
        val scheduleCard = card().apply {
            addView(text("Automatic evening update", 17, ink, true))
            scheduleDetail = text("Phone sync at ${settings.syncTime} · Codex runs at 22:05", 13, muted, false).apply {
                setPadding(0, dp(4), 0, dp(14))
            }
            addView(scheduleDetail)
            time = field(settings.syncTime.toString(), InputType.TYPE_CLASS_DATETIME).apply {
                hint = "HH:mm"
                contentDescription = "Daily sync time in 24-hour format"
            }
            addView(time)
            addView(secondaryButton("Save daily update time") {
                save()
                val next = SyncScheduler.scheduleNext(this@MainActivity)
                val saved = SyncSettings.load(this@MainActivity).syncTime
                scheduleDetail.text = "Phone sync at $saved · next run $next"
                setSyncState("Schedule saved", "Daily update set for $saved.", success)
            }.apply { layoutParams = fullWidth(dp(52)).apply { topMargin = dp(12) } })
        }
        content.addView(scheduleCard)

        val connectionToggle = textButton("Connection settings")
        content.addView(connectionToggle.apply {
            setPadding(0, dp(28), 0, dp(12))
            contentDescription = "Show connection settings"
        })
        connectionPanel = card().apply {
            visibility = View.GONE
            addView(fieldLabel("Mac address"))
            url = field(settings.apiUrl, InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI)
            addView(url)
            addView(fieldLabel("Pairing token").apply { setPadding(0, dp(18), 0, dp(7)) })
            token = field(settings.token, InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
            addView(token)
            addView(secondaryButton("Save connection") {
                save()
                setSyncState("Connection saved", "The next sync will use these settings.", success)
            }.apply { layoutParams = fullWidth(dp(52)).apply { topMargin = dp(16) } })
        }
        content.addView(connectionPanel)
        connectionToggle.setOnClickListener {
            val show = connectionPanel.visibility != View.VISIBLE
            connectionPanel.visibility = if (show) View.VISIBLE else View.GONE
            connectionToggle.text = if (show) "Hide connection settings" else "Connection settings"
            connectionToggle.contentDescription = if (show) "Hide connection settings" else "Show connection settings"
        }

        content.addView(text("Sleep Tight keeps device records on this phone and your Mac.", 12, muted, false).apply {
            gravity = Gravity.CENTER
            setPadding(dp(12), dp(32), dp(12), 0)
        })

        val scroll = ScrollView(this).apply {
            isFillViewport = true
            setBackgroundColor(canvas)
            addView(content)
            setOnApplyWindowInsetsListener { _, insets ->
                content.setPadding(
                    dp(24), dp(28) + insets.systemWindowInsetTop,
                    dp(24), dp(40) + insets.systemWindowInsetBottom
                )
                insets
            }
        }
        setContentView(scroll)
        SyncScheduler.scheduleNext(this)
        updatePermissionStatus()
    }

    private fun save() {
        val parsed = try {
            LocalTime.parse(time.text.toString().trim())
        } catch (_: Exception) {
            LocalTime.of(21, 55)
        }
        time.setText(parsed.toString())
        SyncSettings.save(this, SyncSettings(url.text.toString().trim(), token.text.toString().trim(), parsed))
    }

    private fun syncNow() {
        if (!syncButton.isEnabled) return
        syncButton.isEnabled = false
        setSyncState("Syncing your day…", "Reading the last 24 hours and finding your Mac.", warning)
        val correlationId = "phone-${Instant.now().epochSecond}"
        lifecycleScope.launch {
            try {
                val receipt = SyncEngine.run(
                    this@MainActivity, manual = true,
                    correlationId = correlationId, trigger = "phone_button"
                )
                setSyncState("Synced with your Mac", receipt, success)
            } catch (error: Exception) {
                setSyncState("Could not sync", error.message ?: "Check Wi-Fi and try again.", warning)
            } finally {
                syncButton.isEnabled = true
            }
        }
    }

    private fun updatePermissionStatus() {
        if (HealthConnectClient.getSdkStatus(this) != HealthConnectClient.SDK_AVAILABLE) {
            permissionDetail.text = "Health Connect needs to be installed or updated before this phone can share records."
            return
        }
        lifecycleScope.launch {
            val granted = HealthConnectClient.getOrCreate(this@MainActivity)
                .permissionController.getGrantedPermissions()
                .intersect(HealthConnectExporter.permissions).size
            val total = HealthConnectExporter.permissions.size
            permissionDetail.text = if (granted == total) {
                "All $total requested health categories are available."
            } else {
                "$granted of $total health categories are available. Tap below to review access."
            }
        }
    }

    private fun setSyncState(title: String, detail: String, colour: Int) {
        syncTitle.text = title
        syncDetail.text = detail
        syncDot.background = circle(colour)
        syncTitle.announceForAccessibility("$title. $detail")
    }

    private fun card() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(20), dp(20), dp(20), dp(20))
        background = rounded(surface, line, 20)
        layoutParams = fullWidth()
    }

    private fun horizontal() = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        layoutParams = fullWidth()
    }

    private fun text(value: String, size: Int, colour: Int, bold: Boolean) = TextView(this).apply {
        text = value
        textSize = size.toFloat()
        setTextColor(colour)
        if (bold) setTypeface(typeface, Typeface.BOLD)
        layoutParams = fullWidth()
    }

    private fun sectionLabel(value: String) = text(value, 11, accent, true).apply {
        letterSpacing = .14f
        setPadding(0, 0, 0, dp(10))
    }

    private fun fieldLabel(value: String) = text(value, 12, muted, true).apply {
        setPadding(0, 0, 0, dp(7))
    }

    private fun field(value: String, type: Int) = EditText(this).apply {
        setText(value)
        inputType = type
        textSize = 16f
        setTextColor(ink)
        setHintTextColor(muted)
        setSelectAllOnFocus(false)
        setPadding(dp(16), 0, dp(16), 0)
        background = rounded(surfaceRaised, line, 14)
        layoutParams = fullWidth(dp(54))
    }

    private fun primaryButton(value: String, action: () -> Unit) = Button(this).apply {
        text = value
        isAllCaps = false
        textSize = 16f
        setTypeface(typeface, Typeface.BOLD)
        setTextColor(Color.rgb(31, 19, 14))
        background = rounded(accent, 0, 18)
        stateListAnimator = null
        setOnClickListener { action() }
        layoutParams = fullWidth(dp(60)).apply { topMargin = dp(16) }
    }

    private fun secondaryButton(value: String, action: () -> Unit) = Button(this).apply {
        text = value
        isAllCaps = false
        textSize = 14f
        setTypeface(typeface, Typeface.BOLD)
        setTextColor(ink)
        background = rounded(surfaceRaised, line, 14)
        stateListAnimator = null
        setOnClickListener { action() }
    }

    private fun textButton(value: String) = Button(this).apply {
        text = value
        isAllCaps = false
        textSize = 14f
        gravity = Gravity.START or Gravity.CENTER_VERTICAL
        setTextColor(muted)
        background = null
        stateListAnimator = null
        minHeight = dp(48)
        layoutParams = fullWidth(dp(56))
    }

    private fun rounded(fill: Int, stroke: Int, radius: Int) = GradientDrawable().apply {
        shape = GradientDrawable.RECTANGLE
        setColor(fill)
        cornerRadius = dp(radius).toFloat()
        if (stroke != 0) setStroke(dp(1), stroke)
    }

    private fun circle(fill: Int) = GradientDrawable().apply {
        shape = GradientDrawable.OVAL
        setColor(fill)
    }

    private fun fullWidth(height: Int = ViewGroup.LayoutParams.WRAP_CONTENT) =
        LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, height)

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
}
