package com.example.simwheel

import kotlinx.coroutines.flow.MutableStateFlow

class SimWheelState {
    val throttle = MutableStateFlow(0f)      // 0.0 to 1.0
    val brake = MutableStateFlow(0f)         // 0.0 to 1.0
    val gearUp = MutableStateFlow(false)     // true for a short pulse per tap
    val gearDown = MutableStateFlow(false)
    val handbrake = MutableStateFlow(false)  // true while the HANDBRAKE button is held

    /** Puts every control back to neutral (used on pause and after a detected drop). */
    fun releaseAll() {
        throttle.value = 0f
        brake.value = 0f
        gearUp.value = false
        gearDown.value = false
        handbrake.value = false
    }
}
