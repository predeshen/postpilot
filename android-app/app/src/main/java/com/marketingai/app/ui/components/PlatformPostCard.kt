package com.marketingai.app.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.marketingai.app.data.models.GeneratedPostResponse
import com.marketingai.app.ui.theme.FacebookColor
import com.marketingai.app.ui.theme.InstagramColor
import com.marketingai.app.ui.theme.TikTokColor

@Composable
fun PlatformPostCard(
    post: GeneratedPostResponse,
    onApprove: () -> Unit,
    onRegenerate: () -> Unit,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val platformColor = when (post.platform) {
        "tiktok" -> TikTokColor
        "instagram" -> InstagramColor
        "facebook" -> FacebookColor
        else -> MaterialTheme.colorScheme.primary
    }

    Card(
        modifier = modifier.fillMaxWidth(),
        onClick = onClick
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Header row: platform + status
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Platform badge
                SuggestionChip(
                    onClick = { },
                    label = {
                        Text(
                            text = post.platform.replaceFirstChar { it.uppercase() },
                            style = MaterialTheme.typography.labelSmall
                        )
                    },
                    colors = SuggestionChipDefaults.suggestionChipColors(
                        containerColor = platformColor.copy(alpha = 0.1f),
                        labelColor = platformColor
                    )
                )

                Spacer(modifier = Modifier.width(8.dp))

                // Pillar type
                post.pillarType?.let { pillar ->
                    SuggestionChip(
                        onClick = { },
                        label = {
                            Text(
                                text = pillar.replaceFirstChar { it.uppercase() },
                                style = MaterialTheme.typography.labelSmall
                            )
                        }
                    )
                }

                Spacer(modifier = Modifier.weight(1f))

                // Status indicator
                val statusColor = when (post.status) {
                    "draft" -> MaterialTheme.colorScheme.outline
                    "approved" -> MaterialTheme.colorScheme.primary
                    "published" -> MaterialTheme.colorScheme.tertiary
                    else -> MaterialTheme.colorScheme.error
                }
                Text(
                    text = post.status.replaceFirstChar { it.uppercase() },
                    style = MaterialTheme.typography.labelSmall,
                    color = statusColor,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Content preview
            Text(
                text = post.content,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis
            )

            // Hashtags
            if (post.hashtags.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                LazyRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    items(minOf(post.hashtags.size, 4)) { index ->
                        HashtagChip(hashtag = post.hashtags[index])
                    }
                    if (post.hashtags.size > 4) {
                        item {
                            Text(
                                text = "+${post.hashtags.size - 4}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                }
            }

            // Theme score
            post.themeScore?.let { score ->
                Spacer(modifier = Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        Icons.Default.Star,
                        contentDescription = null,
                        modifier = Modifier.size(14.dp),
                        tint = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "Theme: ${(score * 100).toInt()}%",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Action buttons (only for drafts)
            if (post.status == "draft") {
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    TextButton(onClick = onRegenerate) {
                        Icon(
                            Icons.Default.Refresh,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Regenerate")
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    FilledTonalButton(onClick = onApprove) {
                        Icon(
                            Icons.Default.Check,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Approve")
                    }
                }
            }
        }
    }
}
