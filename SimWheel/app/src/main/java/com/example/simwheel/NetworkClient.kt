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
import org.json.JSONObject
import java.net.InetSocketAddress
import java.net.Socket

class NetworkClient(
    private val wheelState: SimWheelState,
    private val steering: StateFlow<Float>
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var job: Job? = null

    private val host = "127.0.0.1"          // adb reverse makes the PC appear here
    private val port = 5555
    private val sendIntervalMs = 1000L / 60 // 60 packets per second

    val connected = MutableStateFlow(false)

    fun start() {
        if (job?.isActive == true) return
        job = scope.launch {
            while (isActive) {
                try {
                    runConnection()
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    // connection failed or dropped; fall through and retry
                }
                connected.value = false
                delay(1000) // wait 1 second before reconnecting
            }
        }
    }

    fun stop() {
        job?.cancel()
        job = null
    }

    private suspend fun runConnection() {
        Socket().use { socket ->
            socket.tcpNoDelay = true // don't batch small packets (lower lag)
            socket.connect(InetSocketAddress(host, port), 2000)

            val out = socket.getOutputStream()
            val startTime = System.currentTimeMillis()
            try {
                while (true) {
                    out.write(buildPacket().toByteArray())
                    out.flush()
                    if (!connected.value && System.currentTimeMillis() - startTime > 500) {
                        connected.value = true
                    }
                    delay(sendIntervalMs)
                }
            } finally {
                // Safety: tell the PC to zero everything when we stop or drop
                try {
                    out.write(zeroPacket().toByteArray())
                    out.flush()
                } catch (e: Exception) { }
            }
        }
    }

    private fun round3(v: Float): Double = Math.round(v * 1000.0) / 1000.0

    private fun buildPacket(): String {
        val json = JSONObject()
        json.put("steering", round3(steering.value))
        json.put("throttle", round3(wheelState.throttle.value))
        json.put("brake", round3(wheelState.brake.value))
        json.put("gear_up", wheelState.gearUp.value)
        json.put("gear_down", wheelState.gearDown.value)
        return json.toString() + "\n" // newline marks the end of each packet
    }

    private fun zeroPacket(): String {
        val json = JSONObject()
        json.put("steering", 0.0)
        json.put("throttle", 0.0)
        json.put("brake", 0.0)
        json.put("gear_up", false)
        json.put("gear_down", false)
        return json.toString() + "\n"
    }
}