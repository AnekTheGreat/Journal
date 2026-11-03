package app.ujournal

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val Bg = Color(0xFFF4EBDD)
val CardC = Color(0xFFFBF6EC)
val Tan = Color(0xFFC8AD8D)
val Sand = Color(0xFFE6D5BC)
val Ink = Color(0xFF4A3F35)
val Muted = Color(0xFF9C8B77)

@Composable
fun UTheme(content: @Composable () -> Unit) = MaterialTheme(
    colorScheme = lightColorScheme(
        primary = Tan, onPrimary = Color.White,
        background = Bg, onBackground = Ink,
        surface = CardC, onSurface = Ink,
        secondaryContainer = Sand, onSecondaryContainer = Ink
    ),
    content = content
)
