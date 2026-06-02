package com.marketingai.app.ui.screens.content

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketingai.app.ui.components.HashtagChip
import com.marketingai.app.ui.theme.FacebookColor
import com.marketingai.app.ui.theme.InstagramColor
import com.marketingai.app.ui.theme.TikTokColor

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ContentPreviewScreen(
    postId: Int,
    onNavigateBack: () -> Unit,
    viewModel: ContentPreviewViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Content Preview") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (uiState.posts.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Text("Post not found")
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp)
            ) {
                // Variant tabs (A/B testing)
                if (uiState.posts.size > 1) {
                    Text(
                        text = "Variants",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    TabRow(
                        selectedTabIndex = uiState.selectedVariantIndex,
                        modifier = Modifier.clip(RoundedCornerShape(8.dp))
                    ) {
                        uiState.posts.forEachIndexed { index, _ ->
                            Tab(
                                selected = uiState.selectedVariantIndex == index,
                                onClick = { viewModel.selectVariant(index) },
                                text = { Text("Variant ${('A' + index)}") }
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }

                val currentPost = uiState.posts.getOrNull(uiState.selectedVariantIndex)
                currentPost?.let { post ->
                    // Platform-specific preview card
                    PlatformPreviewCard(post = post)

                    Spacer(modifier = Modifier.height(16.dp))

                    // Post details
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            // Status badge
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                StatusBadge(status = post.status)
                                Spacer(modifier = Modifier.weight(1f))
                                post.themeScore?.let { score ->
                                    AssistChip(
                                        onClick = { },
                                        label = { Text("Theme: ${(score * 100).toInt()}%") },
                                        leadingIcon = {
                                            Icon(
                                                Icons.Default.Star,
                                                contentDescription = null,
                                                modifier = Modifier.size(16.dp)
                                            )
                                        }
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(12.dp))

                            // Content text
                            Text(
                                text = post.content,
                                style = MaterialTheme.typography.bodyLarge
                            )

                            Spacer(modifier = Modifier.height(12.dp))

                            // Engagement hook
                            post.engagementHook?.let { hook ->
                                Card(
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.tertiaryContainer
                                    )
                                ) {
                                    Row(
                                        modifier = Modifier.padding(12.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Icon(
                                            Icons.Default.Bolt,
                                            contentDescription = null,
                                            tint = MaterialTheme.colorScheme.onTertiaryContainer,
                                            modifier = Modifier.size(20.dp)
                                        )
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(
                                            text = hook,
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.onTertiaryContainer
                                        )
                                    }
                                }
                                Spacer(modifier = Modifier.height(12.dp))
                            }

                            // Hashtags
                            if (post.hashtags.isNotEmpty()) {
                                Text(
                                    text = "Hashtags",
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.SemiBold
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                LazyRow(
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    items(post.hashtags.size) { index ->
                                        HashtagChip(hashtag = post.hashtags[index])
                                    }
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Action buttons
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        if (post.status == "draft") {
                            Button(
                                onClick = viewModel::approvePost,
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(Icons.Default.Check, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Approve")
                            }
                        }

                        if (post.status == "approved") {
                            Button(
                                onClick = viewModel::publishPost,
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(Icons.Default.Publish, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Publish")
                            }
                        }

                        OutlinedButton(
                            onClick = viewModel::regeneratePost,
                            modifier = Modifier.weight(1f),
                            enabled = !uiState.isRegenerating
                        ) {
                            if (uiState.isRegenerating) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(16.dp),
                                    strokeWidth = 2.dp
                                )
                            } else {
                                Icon(Icons.Default.Refresh, contentDescription = null)
                            }
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Regenerate")
                        }
                    }
                }
            }
        }

        // Messages
        uiState.actionMessage?.let { message ->
            Snackbar(modifier = Modifier.padding(16.dp)) {
                Text(message)
            }
        }
    }
}

@Composable
private fun PlatformPreviewCard(post: com.marketingai.app.data.models.GeneratedPostResponse) {
    val platformColor = when (post.platform) {
        "tiktok" -> TikTokColor
        "instagram" -> InstagramColor
        "facebook" -> FacebookColor
        else -> MaterialTheme.colorScheme.primary
    }

    val dimensions = when (post.platform) {
        "tiktok" -> "1080 x 1920"
        "instagram" -> "1080 x 1080"
        "facebook" -> "1200 x 630"
        else -> "1080 x 1080"
    }

    val aspectRatio = when (post.platform) {
        "tiktok" -> 9f / 16f
        "instagram" -> 1f
        "facebook" -> 1200f / 630f
        else -> 1f
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = platformColor.copy(alpha = 0.05f)
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = post.platform.replaceFirstChar { it.uppercase() },
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = platformColor
                )
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    text = dimensions,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Spacer(modifier = Modifier.height(12.dp))

            // Preview area placeholder
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(aspectRatio)
                    .clip(RoundedCornerShape(8.dp))
                    .background(platformColor.copy(alpha = 0.1f)),
                contentAlignment = Alignment.Center
            ) {
                if (post.imagePath != null) {
                    // Would load image with Coil here
                    Icon(
                        Icons.Default.Image,
                        contentDescription = null,
                        modifier = Modifier.size(48.dp),
                        tint = platformColor.copy(alpha = 0.5f)
                    )
                } else {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            Icons.Default.Image,
                            contentDescription = null,
                            modifier = Modifier.size(48.dp),
                            tint = platformColor.copy(alpha = 0.3f)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Image Preview",
                            style = MaterialTheme.typography.bodySmall,
                            color = platformColor.copy(alpha = 0.5f)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusBadge(status: String) {
    val (color, icon) = when (status) {
        "draft" -> MaterialTheme.colorScheme.outline to Icons.Default.Edit
        "approved" -> MaterialTheme.colorScheme.primary to Icons.Default.CheckCircle
        "published" -> MaterialTheme.colorScheme.tertiary to Icons.Default.Public
        "rejected" -> MaterialTheme.colorScheme.error to Icons.Default.Cancel
        else -> MaterialTheme.colorScheme.outline to Icons.Default.Help
    }

    AssistChip(
        onClick = { },
        label = { Text(status.replaceFirstChar { it.uppercase() }) },
        leadingIcon = {
            Icon(icon, contentDescription = null, modifier = Modifier.size(16.dp))
        },
        colors = AssistChipDefaults.assistChipColors(
            labelColor = color,
            leadingIconContentColor = color
        )
    )
}
