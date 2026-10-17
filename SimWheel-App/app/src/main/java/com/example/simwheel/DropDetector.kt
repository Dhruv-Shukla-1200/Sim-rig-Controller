package com.example.simwheel

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlin.math.sqrt

/**
 * Reads the raw accelerometer to detect free fall (a dropped or thrown phone).
 *
 * At rest the accelerometer magnitude is about 9.8 m/s² (gravity). In free fall
 * the phone and gravity accelerate together, so the reading drops close to zero.
 * If the magnitude stays near zero for [FREE_FALL_MIN_NS], inputs are "locked":
 * [locked] becomes true and the network client sends all-zero packets, so a
 * dropped phone can never leave throttle stuck on in the game.
 */
class DropDetector(context: Context) : SensorEventListener {

    private val sensorManager =
        context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

    private val _locked = MutableStateFlow(false)
    /** True while a drop has been detected and inputs are being held at zero. */
    val locked: StateFlow<Boolean> = _locked

    /** Called once when a drop is first detected. */
    var onDrop: (() -> Unit)? = null

    private var belowSinceNs = 0L
    private var lockedUntilNs = 0L

    fun start() {
        accelerometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
    }

    fun stop() {
        sensorManager.unregisterListener(this)
        belowSinceNs = 0L
        _locked.value = false
    }

    override fun onSensorChanged(event: SensorEvent) {
        val x = event.values[0]
        val y = event.values[1]
        val z = event.values[2]
        val magnitude = sqrt(x * x + y * y + z * z)
        val now = event.timestamp   // nanoseconds

        if (magnitude < FREE_FALL_THRESHOLD) {
            if (belowSinceNs == 0L) belowSinceNs = now
            if (now - belowSinceNs >= FREE_FALL_MIN_NS) {
                lockedUntilNs = now + LOCK_HOLD_NS
                if (!_locked.value) {
                    _locked.value = true
                    onDrop?.invoke()
                }
            }
        } else {
            belowSinceNs = 0L
        }

        // Unlock once the phone has been out of free fall for LOCK_HOLD_NS.
        if (_locked.value && now > lockedUntilNs) {
            _locked.value = false
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    companion object {
        private const val FREE_FALL_THRESHOLD = 2.5f          // m/s² (about 0.25 g)
        private const val FREE_FALL_MIN_NS = 80_000_000L      // 80 ms below the threshold
        private const val LOCK_HOLD_NS = 1_500_000_000L       // hold zeros 1.5 s after the fall
    }
}
