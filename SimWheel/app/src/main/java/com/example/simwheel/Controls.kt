package com.example.simwheel
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

// Vertical pedal: touch/drag up = more, springs back to 0 on release.
// The whole wide box is touchable; the colored bar inside is just the visual.
@Composable
fun PedalSlider(
    label: String,
    value: Float,
    color: Color,
    onValueChange: (Float) -> Unit,
    modifier: Modifier = Modifier
) {
    val currentOnChange by rememberUpdatedState(onValueChange)

    Box(
        modifier = modifier
            .width(110.dp)
            .fillMaxHeight()
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0xFF2A2A2A))
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
                    currentOnChange(0f) // thumb lifted -> spring back to zero
                }
            }
    ) {
        Box(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth(0.6f)
                .fillMaxHeight(value.coerceIn(0f, 1f))
                .background(color)
        )
        Text(
            text = label,
            color = Color.White,
            modifier = Modifier.align(Alignment.TopCenter).padding(top = 8.dp)
        )
    }
}

// Round gear button: each tap sends one short "true" pulse, even if held.
@Composable
fun GearButton(
    label: String,
    onPulse: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    val currentOnPulse by rememberUpdatedState(onPulse)

    Box(
        modifier = modifier
            .size(90.dp)
            .clip(CircleShape)
            .background(Color(0xFF3D5AFE))
            .pointerInput(Unit) {
                detectTapGestures(
                    onPress = {
                        scope.launch {
                            currentOnPulse(true)
                            delay(80)
                            currentOnPulse(false)
                        }
                    }
                )
            },
        contentAlignment = Alignment.Center
    ) {
        Text(label, color = Color.White)
    }
}