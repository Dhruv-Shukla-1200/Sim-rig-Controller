package com.example.simwheel

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.util.concurrent.TimeUnit

enum class ConnectionMode {
    USB,
    WIFI
}

class NetworkClient(
    private val wheelState: SimWheelState,
    private val steering: StateFlow<Float>,
    private val dropLocked: StateFlow<Boolean>
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var job: Job? = null

    private val client = OkHttpClient.Builder()
        .connectTimeout(3, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private var activeWebSocket: WebSocket? = null

    val connected = MutableStateFlow(false)
    val latencyMs = MutableStateFlow<Float?>(null)
    val connectionError = MutableStateFlow<String?>(null)

    // Current connection target configuration
    var mode: ConnectionMode = ConnectionMode.USB
    var wifiAddress: String = ""
    var pairCode: String = ""

    // Optional callback for server-requested haptic feedback.
    var onVibrate: ((Long) -> Unit)? = null

    private val sendIntervalMs = 1000L / 60 // 60 packets per second

    fun start() {
        stop()
        job = scope.launch {
            while (isActive) {
                connectionError.value = null
                try {
                    runWebSocketSession()
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    // connection failed or dropped; fall through and retry
                }
                connected.value = false
                latencyMs.value = null
                delay(1000) // wait 1s before auto-reconnecting
            }
        }
    }

    fun stop() {
        job?.cancel()
        job = null
        try {
            activeWebSocket?.send(zeroPacket())
            activeWebSocket?.close(1000, "App paused or stopped")
        } catch (_: Exception) {}
        activeWebSocket = null
        connected.value = false
        latencyMs.value = null
    }

    private suspend fun runWebSocketSession() {
        val url = buildUrl() ?: run {
            connectionError.value = "Invalid address or missing code"
            delay(1500)
            return
        }

        val request = Request.Builder().url(url).build()
        val sessionActive = MutableStateFlow(true)

        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                activeWebSocket = webSocket
                connected.value = true
                connectionError.value = null
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val data = JSONObject(text)
                    when (data.optString("type")) {
                        "ping" -> {
                            val ts = data.optLong("ts", -1L)
                            if (ts != -1L) {
                                val pong = JSONObject()
                                pong.put("type", "pong")
                                pong.put("ts", ts)
                                webSocket.send(pong.toString())
                            }
                        }
                        "latency" -> {
                            val rtt = data.optDouble("rtt", -1.0)
                            if (rtt >= 0) {
                                latencyMs.value = rtt.toFloat()
                            }
                        }
                        "vibrate" -> {
                            val duration = data.optLong("duration", 200L).coerceIn(1L, 1000L)
                            onVibrate?.invoke(duration)
                        }
                    }
                } catch (_: Exception) {}
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(code, reason)
                sessionActive.value = false
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                if (response?.code == 403) {
                    connectionError.value = "Wrong pair code"
                }
                sessionActive.value = false
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                sessionActive.value = false
            }
        }

        val ws = client.newWebSocket(request, listener)
        activeWebSocket = ws

        try {
            while (sessionActive.value && scope.isActive) {
                if (connected.value) {
                    ws.send(buildPacket())
                }
                delay(sendIntervalMs)
            }
        } finally {
            try {
                ws.send(zeroPacket())
                ws.close(1000, "Session ended")
            } catch (_: Exception) {}
            connected.value = false
        }
    }

    private fun buildUrl(): String? {
        return when (mode) {
            ConnectionMode.USB -> "ws://127.0.0.1:8080/ws/phone"
            ConnectionMode.WIFI -> {
                val cleanAddr = wifiAddress.trim()
                val cleanCode = pairCode.trim()
                if (cleanAddr.isEmpty() || cleanCode.isEmpty()) return null
                val normalizedAddr = if (cleanAddr.startsWith("ws://") || cleanAddr.startsWith("http://")) {
                    cleanAddr.substringAfter("://")
                } else cleanAddr
                "ws://$normalizedAddr/ws/phone?code=$cleanCode"
            }
        }
    }

    private fun round3(v: Float): Double = Math.round(v * 1000.0) / 1000.0

    private fun buildPacket(): String {
        // A detected drop (accelerometer free fall) overrides every input with zeros.
        if (dropLocked.value) return zeroPacket()
        val json = JSONObject()
        json.put("steering", round3(steering.value))
        json.put("throttle", round3(wheelState.throttle.value))
        json.put("brake", round3(wheelState.brake.value))
        json.put("gear_up", wheelState.gearUp.value)
        json.put("gear_down", wheelState.gearDown.value)
        json.put("handbrake", wheelState.handbrake.value)
        return json.toString()
    }

    private fun zeroPacket(): String {
        val json = JSONObject()
        json.put("steering", 0.0)
        json.put("throttle", 0.0)
        json.put("brake", 0.0)
        json.put("gear_up", false)
        json.put("gear_down", false)
        json.put("handbrake", false)
        return json.toString()
    }
}