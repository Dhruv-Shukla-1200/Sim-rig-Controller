package com.example.simwheel

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlin.math.PI
import kotlin.math.atan2
import kotlin.math.hypot

class SteeringSensor(context: Context) : SensorEventListener {

    private val sensorManager =
        context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val rotationSensor =
        sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)

    // Live steering value, -1.0 (full left) to 1.0 (full right)
    private val _steering = MutableStateFlow(0f)
    val steering: StateFlow<Float> = _steering

    private val maxAngleDeg = 90f   // full lock at +/-90 degrees
    private val direction = 1f      // change to -1f if left/right feel reversed

    private val rotationMatrix = FloatArray(9)
    private var rawAngleDeg = 0f
    private var offsetDeg = 0f
    private var smoothed = 0f
    private var firstReading = true

    fun start() {
        firstReading = true   // auto-recenter on the first reading
        sensorManager.registerListener(this, rotationSensor, SensorManager.SENSOR_DELAY_GAME)
    }

    fun stop() {
        sensorManager.unregisterListener(this)
    }

    // Makes the current tilt count as "straight ahead"
    fun recenter() {
        offsetDeg = rawAngleDeg
    }

    override fun onSensorChanged(event: SensorEvent) {
        SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values)

        // The phone's long edge is horizontal in landscape. Turning the "wheel"
        // tilts that edge up or down, so we measure how far it tilts from level.
        val vertical = rotationMatrix[7]
        val horizontal = hypot(rotationMatrix[1], rotationMatrix[4])
        rawAngleDeg = atan2(vertical, horizontal) * (180f / PI.toFloat()) * direction

        if (firstReading) {
            offsetDeg = rawAngleDeg
            firstReading = false
        }

        val normalized = ((rawAngleDeg - offsetDeg) / maxAngleDeg).coerceIn(-1f, 1f)

        // light smoothing to remove jitter
        smoothed += (normalized - smoothed) * 0.4f
        _steering.value = smoothed
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
}