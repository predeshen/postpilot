package com.marketingai.app.ui.screens.analytics

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketingai.app.ui.theme.FacebookColor
import com.marketingai.app.ui.theme.InstagramColor
import com.marketingai.app.ui.theme.TikTokColor

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalyticsScreen(
    onNavigateBack: () -> Unit,
    viewModel: AnalyticsViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Analytics") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::refresh) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
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
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Performance metrics
                uiState.performanceMetrics?.let { metrics ->
                    item {
                        Text(
                            text = "Performance Overview",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            MetricCard(
                                title = "Total Posts",
                                value = metrics.totalPosts.toString(),
                                icon = Icons.Default.Article,
                                modifier = Modifier.weight(1f)
                            )
                            MetricCard(
                                title = "Published",
                                value = metrics.publishedPosts.toString(),
                                icon = Icons.Default.Public,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }

                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            MetricCard(
                                title = "Engagement",
                                value = "${(metrics.averageEngagementRate * 100).toInt()}%",
                                icon = Icons.Default.Favorite,
                                modifier = Modifier.weight(1f)
                            )
                            MetricCard(
                                title = "Top Platform",
                                value = metrics.topPerformingPlatform?.replaceFirstChar { it.uppercase() } ?: "-",
                                icon = Icons.Default.Star,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }

                    // Posts by platform
                    if (metrics.postsByPlatform.isNotEmpty()) {
                        item {
                            Card(modifier = Modifier.fillMaxWidth()) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    Text(
                                        text = "Posts by Platform",
                                        style = MaterialTheme.typography.titleMedium,
                                        fontWeight = FontWeight.SemiBold
                                    )
                                    Spacer(modifier = Modifier.height(12.dp))

                                    metrics.postsByPlatform.forEach { (platform, count) ->
                                        val color = when (platform) {
                                            "tiktok" -> TikTokColor
                                            "instagram" -> InstagramColor
                                            "facebook" -> FacebookColor
                                            else -> MaterialTheme.colorScheme.primary
                                        }
                                        Row(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .padding(vertical = 6.dp),
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text(
                                                text = platform.replaceFirstChar { it.uppercase() },
                                                style = MaterialTheme.typography.bodyMedium,
                                                modifier = Modifier.width(100.dp)
                                            )
                                            LinearProgressIndicator(
                                                progress = {
                                                    if (metrics.totalPosts > 0) {
                                                        count.toFloat() / metrics.totalPosts
                                                    } else 0f
                                                },
                                                modifier = Modifier
                                                    .weight(1f)
                                                    .height(10.dp),
                                                color = color
                                            )
                                            Spacer(modifier = Modifier.width(12.dp))
                                            Text(
                                                text = count.toString(),
                                                style = MaterialTheme.typography.titleSmall,
                                                fontWeight = FontWeight.Bold
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Posts by status
                    if (metrics.postsByStatus.isNotEmpty()) {
                        item {
                            Card(modifier = Modifier.fillMaxWidth()) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    Text(
                                        text = "Posts by Status",
                                        style = MaterialTheme.typography.titleMedium,
                                        fontWeight = FontWeight.SemiBold
                                    )
                                    Spacer(modifier = Modifier.height(12.dp))

                                    metrics.postsByStatus.forEach { (status, count) ->
                                        Row(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .padding(vertical = 4.dp),
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text(
                                                text = status.replaceFirstChar { it.uppercase() },
                                                style = MaterialTheme.typography.bodyMedium,
                                                modifier = Modifier.width(100.dp)
                                            )
                                            LinearProgressIndicator(
                                                progress = {
                                                    if (metrics.totalPosts > 0) {
                                                        count.toFloat() / metrics.totalPosts
                                                    } else 0f
                                                },
                                                modifier = Modifier
                                                    .weight(1f)
                                                    .height(8.dp)
                                            )
                                            Spacer(modifier = Modifier.width(12.dp))
                                            Text(
                                                text = count.toString(),
                                                style = MaterialTheme.typography.labelMedium
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Theme score
                uiState.themeScore?.let { score ->
                    item {
                        Text(
                            text = "Theme Consistency",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    item {
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                // Overall score
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "Overall Score",
                                        style = MaterialTheme.typography.titleMedium
                                    )
                                    Spacer(modifier = Modifier.weight(1f))
                                    Text(
                                        text = "${(score.overallScore * 100).toInt()}%",
                                        style = MaterialTheme.typography.headlineMedium,
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }

                                Spacer(modifier = Modifier.height(16.dp))

                                // Sub-scores
                                ScoreRow(
                                    label = "Brand Voice",
                                    score = score.brandVoiceConsistency
                                )
                                ScoreRow(
                                    label = "Visual Consistency",
                                    score = score.visualConsistency
                                )

                                Spacer(modifier = Modifier.height(16.dp))

                                // Content pillar balance
                                if (score.contentPillarBalance.isNotEmpty()) {
                                    Text(
                                        text = "Content Pillar Balance",
                                        style = MaterialTheme.typography.titleSmall,
                                        fontWeight = FontWeight.SemiBold
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    score.contentPillarBalance.forEach { (pillar, value) ->
                                        ScoreRow(
                                            label = pillar.replaceFirstChar { it.uppercase() },
                                            score = value
                                        )
                                    }
                                }
                            }
                        }
                    }

                    // Recommendations
                    if (score.recommendations.isNotEmpty()) {
                        item {
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                                )
                            ) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Icon(
                                            Icons.Default.Lightbulb,
                                            contentDescription = null,
                                            tint = MaterialTheme.colorScheme.onSecondaryContainer
                                        )
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(
                                            text = "Recommendations",
                                            style = MaterialTheme.typography.titleMedium,
                                            fontWeight = FontWeight.SemiBold
                                        )
                                    }
                                    Spacer(modifier = Modifier.height(12.dp))
                                    score.recommendations.forEach { rec ->
                                        Row(
                                            modifier = Modifier.padding(vertical = 4.dp)
                                        ) {
                                            Text(
                                                text = "\u2022",
                                                style = MaterialTheme.typography.bodyMedium
                                            )
                                            Spacer(modifier = Modifier.width(8.dp))
                                            Text(
                                                text = rec,
                                                style = MaterialTheme.typography.bodyMedium
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Empty state
                if (uiState.performanceMetrics == null && !uiState.isLoading) {
                    item {
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(32.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    Icons.Default.Analytics,
                                    contentDescription = null,
                                    modifier = Modifier.size(48.dp),
                                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = "No analytics data yet",
                                    style = MaterialTheme.typography.titleMedium
                                )
                                Text(
                                    text = "Generate and publish some content to see analytics here.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MetricCard(
    title: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(28.dp)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = title,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun ScoreRow(label: String, score: Float) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.width(140.dp)
        )
        LinearProgressIndicator(
            progress = { score },
            modifier = Modifier
                .weight(1f)
                .height(8.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "${(score * 100).toInt()}%",
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold
        )
    }
}
