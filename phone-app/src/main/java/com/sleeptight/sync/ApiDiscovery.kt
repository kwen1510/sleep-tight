package com.sleeptight.sync

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeout
import kotlin.coroutines.resume

object ApiDiscovery {
    suspend fun resolve(context: Context, configured: String): String {
        if (!configured.startsWith("auto://")) return configured.trimEnd('/')
        return withTimeout(12_000) {
            suspendCancellableCoroutine { continuation ->
                val nsd = context.getSystemService(Context.NSD_SERVICE) as NsdManager
                lateinit var listener: NsdManager.DiscoveryListener
                fun finish(value: String) {
                    try { nsd.stopServiceDiscovery(listener) } catch (_: Exception) { }
                    if (continuation.isActive) continuation.resume(value)
                }
                listener = object : NsdManager.DiscoveryListener {
                    override fun onDiscoveryStarted(type: String) = Unit
                    override fun onDiscoveryStopped(type: String) = Unit
                    override fun onServiceLost(service: NsdServiceInfo) = Unit
                    override fun onStopDiscoveryFailed(type: String, code: Int) = Unit
                    override fun onStartDiscoveryFailed(type: String, code: Int) = finish("")
                    override fun onServiceFound(service: NsdServiceInfo) {
                        if (!service.serviceType.startsWith("_sleeptight-api._tcp")) return
                        @Suppress("DEPRECATION")
                        nsd.resolveService(service, object : NsdManager.ResolveListener {
                            override fun onResolveFailed(info: NsdServiceInfo, code: Int) = Unit
                            override fun onServiceResolved(info: NsdServiceInfo) {
                                val host = info.host?.hostAddress ?: return
                                val formatted = if (host.contains(':')) "[$host]" else host
                                finish("http://$formatted:${info.port}")
                            }
                        })
                    }
                }
                continuation.invokeOnCancellation {
                    try { nsd.stopServiceDiscovery(listener) } catch (_: Exception) { }
                }
                nsd.discoverServices("_sleeptight-api._tcp.", NsdManager.PROTOCOL_DNS_SD, listener)
            }
        }.ifBlank { throw IllegalStateException("Sleep Tight Mac was not found on this Wi-Fi network") }
    }
}
