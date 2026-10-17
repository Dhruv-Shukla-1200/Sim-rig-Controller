package com.example.simwheel

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Vertical pedal. Touch/drag upward increases input; releasing returns it to zero. */
@Composable
fun PedalSlider(
    label: String,
    value: Float,
    color: Color,
    onValueChange: (Float) -> Unit,
    modifier: Modifier = Modifier
) {
    val currentOnChange by rememberUpdatedState(onValueChange)
    val safeValue = value.coerceIn(0f, 1f)

    Box(
        modifier = modifier
            .fillMaxHeight()
            .clip(RoundedCornerShape(20.dp))
            .background(Color(0xFF171D24))
            .pointerInput(Unit) {
                awaitEachGesture {
                    val down = awaitFirstDown()
                    currentOnChange((1f - down.position.y / size.height).coerceIn(0f, 1f))
                    do {
                        val event = awaitPointerEvent()
                        val change = event.changes.firstOrNull { it.id == down.id }
                        if (change != null && change.pressed) {
                            currentOnChange((1f - change.position.y / size.height).coerceIn(0f, 1f))
                            change.consume()
                        }
                    } while (change != null && change.pressed)
                    currentOnChange(0f)
                }
            }
    ) {
        // Subtle inset track and live fill.
        Box(
            Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth(0.52f)
                .fillMaxHeight(safeValue)
                .clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp))
                .background(color)
        )
        Column(
            modifier = Modifier.align(Alignment.TopCenter).padding(top = 10.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(label, color = Color(0xFFCAD4DF), fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
            Text("${(safeValue * 100).toInt()}%", color = Color.White, fontSize = 15.sp, fontWeight = FontWeight.Bold)
        }
        Box(
            Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 8.dp)
                .size(width = 24.dp, height = 4.dp)
                .clip(CircleShape)
                .background(Color.White.copy(alpha = 0.7f))
        )
    }
}

/** Large tactile gear control. A tap creates a short pulse for the game/server. */
@Composable
fun GearButton(
    label: String,
    onPulse: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    val currentOnPulse by rememberUpdatedState(onPulse)
    var pressed by remember { mutableStateOf(false) }
    val scale by animateFloatAsState(if (pressed) 0.94f else 1f, label = "gearPressScale")
    val isUp = label.contains("up", ignoreCase = true)
    val accent = if (isUp) Color(0xFF35D0A0) else Color(0xFFFFB454)

    Column(
        modifier = modifier
            .scale(scale)
            .clip(RoundedCornerShape(22.dp))
            .background(if (pressed) Color(0xFF34414D) else Color(0xFF202A34))
            .pointerInput(Unit) {
                detectTapGestures(
                    onPress = {
                        pressed = true
                        scope.launch {
                            currentOnPulse(true)
                            delay(85)
                            currentOnPulse(false)
                        }
                        tryAwaitRelease()
                        pressed = false
                    }
                )
            }
            .padding(vertical = 10.dp, horizontal = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Box(
            modifier = Modifier
                .size(42.dp)
                .clip(CircleShape)
                .background(accent.copy(alpha = if (pressed) 0.32f else 0.16f)),
            contentAlignment = Alignment.Center
        ) {
            Text(if (isUp) "↑" else "↓", color = accent, fontSize = 30.sp, fontWeight = FontWeight.Black)
        }
        Spacer(Modifier.height(8.dp))
        Text(if (isUp) "GEAR UP" else "GEAR DOWN", color = Color.White, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 0.5.sp)
        Text(if (isUp) "SHIFT +" else "SHIFT −", color = Color(0xFF8D9BA9), fontSize = 9.sp, fontWeight = FontWeight.Medium)
    }
}

/** Press-and-hold handbrake. Sends true while a finger is down, false on release. */
@Composable
fun HandbrakeButton(
    onHold: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val currentOnHold by rememberUpdatedState(onHold)
    var pressed by remember { mutableStateOf(false) }
    val scale by animateFloatAsState(if (pressed) 0.94f else 1f, label = "handbrakePressScale")
    val accent = Color(0xFFFF5C67)

    Column(
        modifier = modifier
            .scale(scale)
            .clip(RoundedCornerShape(18.dp))
            .background(if (pressed) Color(0xFF5A2A30) else Color(0xFF202A34))
            .pointerInput(Unit) {
                awaitEachGesture {
                    val down = awaitFirstDown()
                    pressed = true
                    currentOnHold(true)
                    try {
                        do {
                            val event = awaitPointerEvent()
                            val change = event.changes.firstOrNull { it.id == down.id }
                            change?.consume()
                        } while (change != null && change.pressed)
                    } finally {
                        pressed = false
                        currentOnHold(false)
                    }
                }
            }
            .padding(vertical = 6.dp, horizontal = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text("HANDBRAKE", color = accent, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 0.5.sp)
    }
}


