package com.example.simwheel
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import java.util.Locale

class MainActivity : ComponentActivity() {

    private lateinit var steeringSensor: SteeringSensor
    private val wheelState = SimWheelState()
    private lateinit var networkClient: NetworkClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        steeringSensor = SteeringSensor(this)
        networkClient = NetworkClient(wheelState, steeringSensor.steering)

        setContent {
            MaterialTheme {
                val steering by steeringSensor.steering.collectAsState()
                val throttle by wheelState.throttle.collectAsState()
                val brake by wheelState.brake.collectAsState()
                val connected by networkClient.connected.collectAsState()

                Row(
                    modifier = Modifier
                        .fillMaxSize()
                        .systemBarsPadding()
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // LEFT: brake slider (outermost), gear down just inside
                    PedalSlider(
                        label = "BRAKE",
                        value = brake,
                        color = Color(0xFFE53935),
                        onValueChange = { wheelState.brake.value = it }
                    )
                    Spacer(Modifier.width(12.dp))
                    GearButton("Gear\nDown", onPulse = { wheelState.gearDown.value = it })

                    // CENTER: live readouts + recenter
                    Column(
                        modifier = Modifier.weight(1f),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text("Steering: " + String.format(Locale.US, "%.2f", steering))
                        Text("Throttle: ${(throttle * 100).toInt()}%")
                        Text("Brake: ${(brake * 100).toInt()}%")
                        Text(if (connected) "PC: connected" else "PC: not connected")
                        Spacer(Modifier.height(16.dp))
                        Button(onClick = { steeringSensor.recenter() }) {
                            Text("Recenter")
                        }
                    }

                    // RIGHT: gear up just inside, throttle slider outermost
                    GearButton("Gear\nUp", onPulse = { wheelState.gearUp.value = it })
                    Spacer(Modifier.width(12.dp))
                    PedalSlider(
                        label = "THROTTLE",
                        value = throttle,
                        color = Color(0xFF43A047),
                        onValueChange = { wheelState.throttle.value = it }
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        steeringSensor.start()
        networkClient.start()
    }

    override fun onPause() {
        super.onPause()
        steeringSensor.stop()
        networkClient.stop()
    }
}