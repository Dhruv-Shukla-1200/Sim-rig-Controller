package com.example.simwheel

import android.content.Context
import android.content.pm.ActivityInfo
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.util.Locale

private val AppBackground = Color(0xFF0B1016)
private val PanelColor = Color(0xFF151D26)
private val MutedText = Color(0xFF91A0AF)
private val AccentBlue = Color(0xFF58C6FF)

class MainActivity : ComponentActivity() {

    private lateinit var steeringSensor: SteeringSensor
    private val wheelState = SimWheelState()
    private lateinit var networkClient: NetworkClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val prefs = getSharedPreferences("simwheel_prefs", Context.MODE_PRIVATE)
        val initialAddress = prefs.getString("wifi_address", "192.168.1.") ?: "192.168.1."
        val initialMode = if (prefs.getString("mode", "USB") == "WIFI") ConnectionMode.WIFI else ConnectionMode.USB

        steeringSensor = SteeringSensor(this)
        networkClient = NetworkClient(wheelState, steeringSensor.steering).apply {
            mode = initialMode
            wifiAddress = initialAddress
            onVibrate = { duration -> triggerVibration(duration) }
        }

        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    background = AppBackground,
                    surface = PanelColor,
                    primary = AccentBlue,
                    onBackground = Color.White,
                    onSurface = Color.White
                )
            ) {
                val steering by steeringSensor.steering.collectAsState()
                val throttle by wheelState.throttle.collectAsState()
                val brake by wheelState.brake.collectAsState()
                val connected by networkClient.connected.collectAsState()
                val latency by networkClient.latencyMs.collectAsState()
                val errorMsg by networkClient.connectionError.collectAsState()

                var currentMode by remember { mutableStateOf(initialMode) }
                var addressText by remember { mutableStateOf(initialAddress) }
                var codeText by remember { mutableStateOf("") }

                fun saveAndApplyConnection(newMode: ConnectionMode, newAddress: String, newCode: String) {
                    prefs.edit()
                        .putString("wifi_address", newAddress)
                        .putString("mode", newMode.name)
                        .apply()
                    networkClient.mode = newMode
                    networkClient.wifiAddress = newAddress
                    networkClient.pairCode = newCode
                    networkClient.start()
                }

                BoxWithConstraints(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(AppBackground)
                        .systemBarsPadding()
                        .padding(horizontal = 10.dp, vertical = 8.dp)
                ) {
                    // Sizes scale with the available display, so the shift controls stay easy to hit.
                    val compact = maxWidth < 650.dp
                    val pedalWidth = if (compact) 62.dp else 82.dp
                    val gearWidth = if (compact) 70.dp else 88.dp
                    val gearHeight = (maxHeight * 0.60f).coerceIn(112.dp, 176.dp)

                    Row(
                        modifier = Modifier.fillMaxSize(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(if (compact) 6.dp else 10.dp)
                    ) {
                        PedalSlider(
                            label = "BRAKE",
                            value = brake,
                            color = Color(0xFFFF5C67),
                            onValueChange = { wheelState.brake.value = it },
                            modifier = Modifier.width(pedalWidth).fillMaxHeight(0.94f)
                        )

                        GearButton(
                            label = "Gear Down",
                            onPulse = { wheelState.gearDown.value = it },
                            modifier = Modifier.width(gearWidth).height(gearHeight)
                        )

                        Column(
                            modifier = Modifier
                                .weight(1f)
                                .fillMaxHeight()
                                .padding(horizontal = if (compact) 1.dp else 4.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.SpaceBetween
                        ) {
                            // Compact branding/header, without taking valuable space away from controls.
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Column {
                                    Text("SIMWHEEL", color = Color.White, fontSize = if (compact) 17.sp else 21.sp, fontWeight = FontWeight.Black, letterSpacing = 1.5.sp)
                                    Text("PHONE RACING CONTROLLER", color = MutedText, fontSize = 8.sp, letterSpacing = 1.2.sp)
                                }
                                Row(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(50))
                                        .background(if (connected) Color(0xFF12382F) else Color(0xFF352B1B))
                                        .padding(horizontal = 10.dp, vertical = 6.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    Box(Modifier.size(7.dp).clip(RoundedCornerShape(50)).background(if (connected) Color(0xFF35D0A0) else Color(0xFFFFC05C)))
                                    Text(if (connected) "ONLINE" else "OFFLINE", color = if (connected) Color(0xFF75E6C2) else Color(0xFFFFD18A), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                }
                            }

                            // USB / Wi-Fi selector
                            Row(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(16.dp))
                                    .background(Color(0xFF1B2631))
                                    .padding(4.dp),
                                horizontalArrangement = Arrangement.Center
                            ) {
                                ModePill("USB", currentMode == ConnectionMode.USB, compact) {
                                    currentMode = ConnectionMode.USB
                                    saveAndApplyConnection(ConnectionMode.USB, addressText, codeText)
                                }
                                ModePill("Wi-Fi", currentMode == ConnectionMode.WIFI, compact) {
                                    currentMode = ConnectionMode.WIFI
                                    saveAndApplyConnection(ConnectionMode.WIFI, addressText, codeText)
                                }
                            }

                            if (currentMode == ConnectionMode.WIFI) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    OutlinedTextField(
                                        value = addressText,
                                        onValueChange = { addressText = it },
                                        label = { Text("Laptop IP:Port", fontSize = 10.sp) },
                                        placeholder = { Text("192.168.1.X:8080", fontSize = 10.sp) },
                                        singleLine = true,
                                        modifier = Modifier.weight(1.35f),
                                        textStyle = LocalTextStyle.current.copy(fontSize = 12.sp),
                                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                                        shape = RoundedCornerShape(12.dp)
                                    )
                                    OutlinedTextField(
                                        value = codeText,
                                        onValueChange = { if (it.length <= 4 && it.all(Char::isDigit)) codeText = it },
                                        label = { Text("Pair code", fontSize = 10.sp) },
                                        placeholder = { Text("1234", fontSize = 10.sp) },
                                        singleLine = true,
                                        modifier = Modifier.weight(0.7f),
                                        textStyle = LocalTextStyle.current.copy(fontSize = 12.sp),
                                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                                        shape = RoundedCornerShape(12.dp)
                                    )
                                    Button(
                                        onClick = { saveAndApplyConnection(ConnectionMode.WIFI, addressText, codeText) },
                                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 12.dp),
                                        shape = RoundedCornerShape(12.dp)
                                    ) { Text("JOIN", fontSize = 11.sp, fontWeight = FontWeight.Bold) }
                                }
                            }

                            // Live telemetry panel
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(18.dp),
                                colors = CardDefaults.cardColors(containerColor = PanelColor)
                            ) {
                                Column(
                                    modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 9.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.SpaceBetween
                                    ) {
                                        Column {
                                            Text("CONNECTION", color = MutedText, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                                            val status = when {
                                                connected -> "Connected · ${if (currentMode == ConnectionMode.USB) "USB" else "Wi-Fi"}"
                                                errorMsg != null -> errorMsg!!.take(32)
                                                else -> "Waiting for controller…"
                                            }
                                            Text(status, color = if (connected) Color(0xFF75E6C2) else if (errorMsg != null) Color(0xFFFF7C83) else Color(0xFFFFD18A), fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                                        }
                                        if (connected && latency != null) {
                                            Column(horizontalAlignment = Alignment.End) {
                                                Text("PING", color = MutedText, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                                                Text("${latency!!.toInt()} ms", color = AccentBlue, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                                            }
                                        }
                                    }
                                    HorizontalDivider(color = Color(0xFF2B3743))
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        TelemetryValue("STEER", String.format(Locale.US, "%+.2f", steering), AccentBlue)
                                        TelemetryValue("THROTTLE", "${(throttle * 100).toInt()}%", Color(0xFF35D0A0))
                                        TelemetryValue("BRAKE", "${(brake * 100).toInt()}%", Color(0xFFFF5C67))
                                    }
                                }
                            }

                            Button(
                                onClick = { steeringSensor.recenter() },
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(14.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF253544)),
                                contentPadding = PaddingValues(vertical = 11.dp)
                            ) {
                                Text("◎   RECENTER STEERING", color = Color(0xFFD9EAF5), fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 0.7.sp)
                            }
                        }

                        GearButton(
                            label = "Gear Up",
                            onPulse = { wheelState.gearUp.value = it },
                            modifier = Modifier.width(gearWidth).height(gearHeight)
                        )

                        PedalSlider(
                            label = "THROTTLE",
                            value = throttle,
                            color = Color(0xFF35D0A0),
                            onValueChange = { wheelState.throttle.value = it },
                            modifier = Modifier.width(pedalWidth).fillMaxHeight(0.94f)
                        )
                    }
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
        steeringSensor.stop()
        networkClient.stop()
        super.onPause()
    }

    private fun triggerVibration(durationMs: Long) {
        val safeDuration = durationMs.coerceIn(1L, 1000L)
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val manager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                manager?.defaultVibrator?.vibrate(
                    VibrationEffect.createOneShot(safeDuration, VibrationEffect.DEFAULT_AMPLITUDE)
                )
            } else {
                @Suppress("DEPRECATION")
                val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator?.vibrate(
                        VibrationEffect.createOneShot(safeDuration, VibrationEffect.DEFAULT_AMPLITUDE)
                    )
                } else {
                    @Suppress("DEPRECATION")
                    vibrator?.vibrate(safeDuration)
                }
            }
        } catch (_: Exception) {
            // Haptics are optional; a device without a working vibrator can still play.
        }
    }
}

@Composable
private fun ModePill(label: String, selected: Boolean, compact: Boolean, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(if (selected) Color(0xFF17658A) else Color.Transparent)
            .clickable(onClick = onClick)
            .padding(horizontal = if (compact) 16.dp else 24.dp, vertical = 7.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(label, color = if (selected) Color.White else MutedText, fontSize = 12.sp, fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium)
    }
}

@Composable
private fun TelemetryValue(label: String, value: String, color: Color) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(label, color = MutedText, fontSize = 8.sp, fontWeight = FontWeight.Bold, letterSpacing = 0.8.sp)
        Text(value, color = color, fontSize = 15.sp, fontWeight = FontWeight.Bold)
    }
}
