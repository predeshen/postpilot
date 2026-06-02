package com.marketingai.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

private val presetColors = listOf(
    "#FF0050", "#E4405F", "#1877F2", "#6750A4",
    "#006B5E", "#FF6D00", "#4CAF50", "#2196F3",
    "#9C27B0", "#F44336", "#FF9800", "#FFEB3B",
    "#00BCD4", "#795548", "#607D8B", "#E91E63",
    "#3F51B5", "#009688", "#CDDC39", "#FF5722"
)

@Composable
fun ColorPicker(
    onColorSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var customColorHex by remember { mutableStateOf("") }
    var selectedPreset by remember { mutableStateOf<String?>(null) }

    Column(modifier = modifier) {
        Text(
            text = "Pick a color",
            style = MaterialTheme.typography.titleSmall
        )
        Spacer(modifier = Modifier.height(12.dp))

        // Preset color grid
        LazyVerticalGrid(
            columns = GridCells.Fixed(5),
            modifier = Modifier.height(200.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(presetColors) { colorHex ->
                val color = try {
                    Color(android.graphics.Color.parseColor(colorHex))
                } catch (e: Exception) {
                    Color.Gray
                }
                val isSelected = selectedPreset == colorHex

                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(color)
                        .then(
                            if (isSelected) {
                                Modifier.border(3.dp, MaterialTheme.colorScheme.outline, CircleShape)
                            } else {
                                Modifier.border(1.dp, Color.Gray.copy(alpha = 0.3f), CircleShape)
                            }
                        )
                        .clickable {
                            selectedPreset = colorHex
                            onColorSelected(colorHex)
                        },
                    contentAlignment = Alignment.Center
                ) {
                    if (isSelected) {
                        Icon(
                            Icons.Default.Check,
                            contentDescription = "Selected",
                            tint = Color.White,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Custom color input
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = customColorHex,
                onValueChange = { customColorHex = it },
                label = { Text("Custom hex") },
                placeholder = { Text("#FF5722") },
                singleLine = true,
                modifier = Modifier.weight(1f)
            )
            Spacer(modifier = Modifier.width(8.dp))
            FilledIconButton(
                onClick = {
                    val hex = if (customColorHex.startsWith("#")) customColorHex else "#$customColorHex"
                    onColorSelected(hex)
                    customColorHex = ""
                },
                enabled = customColorHex.length >= 6
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add custom color")
            }
        }
    }
}
