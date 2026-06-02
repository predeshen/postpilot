package com.marketingai.app.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

data class VoiceOption(
    val id: String,
    val label: String,
    val description: String,
    val icon: ImageVector
)

private val voiceOptions = listOf(
    VoiceOption(
        id = "professional",
        label = "Professional",
        description = "Polished, authoritative, industry-focused language",
        icon = Icons.Default.Business
    ),
    VoiceOption(
        id = "casual",
        label = "Casual",
        description = "Friendly, relaxed, conversational tone",
        icon = Icons.Default.EmojiEmotions
    ),
    VoiceOption(
        id = "playful",
        label = "Playful",
        description = "Fun, witty, creative with humor",
        icon = Icons.Default.Celebration
    ),
    VoiceOption(
        id = "inspirational",
        label = "Inspirational",
        description = "Motivating, uplifting, empowering",
        icon = Icons.Default.AutoAwesome
    ),
    VoiceOption(
        id = "educational",
        label = "Educational",
        description = "Informative, clear, teaching-focused",
        icon = Icons.Default.School
    ),
    VoiceOption(
        id = "bold",
        label = "Bold",
        description = "Direct, confident, attention-grabbing",
        icon = Icons.Default.FlashOn
    )
)

@Composable
fun BrandVoiceSelector(
    selectedVoice: String,
    onVoiceSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        voiceOptions.forEach { option ->
            val isSelected = option.id == selectedVoice

            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onVoiceSelected(option.id) },
                colors = CardDefaults.cardColors(
                    containerColor = if (isSelected)
                        MaterialTheme.colorScheme.primaryContainer
                    else
                        MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        option.icon,
                        contentDescription = null,
                        tint = if (isSelected)
                            MaterialTheme.colorScheme.onPrimaryContainer
                        else
                            MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = option.label,
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold,
                            color = if (isSelected)
                                MaterialTheme.colorScheme.onPrimaryContainer
                            else
                                MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            text = option.description,
                            style = MaterialTheme.typography.bodySmall,
                            color = if (isSelected)
                                MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                            else
                                MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    if (isSelected) {
                        Icon(
                            Icons.Default.CheckCircle,
                            contentDescription = "Selected",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }
        }
    }
}
