package com.example.simwheel

import kotlinx.coroutines.flow.MutableStateFlow

class SimWheelState {
    val throttle = MutableStateFlow(0f)      // 0.0 to 1.0
    val brake = MutableStateFlow(0f)         // 0.0 to 1.0
    val gearUp = MutableStateFlow(false)     // true for a short pulse per tap
    val gearDown = MutableStateFlow(false)
}