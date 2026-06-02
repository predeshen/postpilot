package com.marketingai.app.ui.screens.trending

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import com.marketingai.app.data.models.CompetitorAnalysisResponse
import com.marketingai.app.data.models.TrendingHashtagResponse
import com.marketingai.app.ui.components.HashtagChip
import com.marketingai.app.ui.theme.FacebookColor
import com.marketingai.app.ui.theme.InstagramColor
import com.marketingai.app.ui.theme.TikTokColor

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TrendingScreen(
    onNavigateBack: () -> Unit,
    viewModel: TrendingViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Trending") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::loadTrends) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Platform filter
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf("instagram" to InstagramColor, "tiktok" to TikTokColor, "facebook" to FacebookColor)
                    .forEach { (platform, color) ->
                        FilterChip(
                            selected = uiState.selectedPlatform == platform,
                            onClick = { viewModel.selectPlatform(platform) },
                            label = { Text(platform.replaceFirstChar { it.uppercase() }) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = color.copy(alpha = 0.2f)
                            )
                        )
                    }
            }

            // Tab selector
            TabRow(
                selectedTabIndex = TrendingTab.entries.indexOf(uiState.selectedTab)
            ) {
                TrendingTab.entries.forEach { tab ->
                    Tab(
                        selected = uiState.selectedTab == tab,
                        onClick = { viewModel.selectTab(tab) },
                        text = { Text(tab.label) }
                    )
                }
            }

            if (uiState.isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                when (uiState.selectedTab) {
                    TrendingTab.HASHTAGS -> HashtagsList(hashtags = uiState.hashtags)
                    TrendingTab.COMPETITORS -> CompetitorsList(competitors = uiState.competitors)
                }
            }
        }
    }
}

@Composable
private fun HashtagsList(hashtags: List<TrendingHashtagResponse>) {
    if (hashtags.isEmpty()) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(
                    Icons.Default.Tag,
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "No trending hashtags found",
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }
    } else {
        LazyColumn(
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(hashtags) { hashtag ->
                HashtagCard(hashtag = hashtag)
            }
        }
    }
}

@Composable
private fun HashtagCard(hashtag: TrendingHashtagResponse) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "#${hashtag.hashtag}",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                hashtag.category?.let { category ->
                    Text(
                        text = category,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Text(
                    text = "${hashtag.usageCount} uses",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Column(horizontalAlignment = Alignment.End) {
                // Relevance score
                Text(
                    text = "Relevance",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                LinearProgressIndicator(
                    progress = { hashtag.relevanceScore },
                    modifier = Modifier
                        .width(80.dp)
                        .height(6.dp)
                )
                Spacer(modifier = Modifier.height(4.dp))

                // Trend score
                Text(
                    text = "Trend",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                LinearProgressIndicator(
                    progress = { hashtag.trendScore / 100f },
                    modifier = Modifier
                        .width(80.dp)
                        .height(6.dp),
                    color = MaterialTheme.colorScheme.tertiary
                )
            }
        }
    }
}

@Composable
private fun CompetitorsList(competitors: List<CompetitorAnalysisResponse>) {
    if (competitors.isEmpty()) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(
                    Icons.Default.People,
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "No competitor data available",
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }
    } else {
        LazyColumn(
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(competitors) { competitor ->
                CompetitorCard(competitor = competitor)
            }
        }
    }
}

@Composable
private fun CompetitorCard(competitor: CompetitorAnalysisResponse) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Business,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = competitor.competitorName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = "Posts ${competitor.postingFrequency}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Text(
                    text = "${(competitor.engagementRate * 100).toInt()}%",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "Top Hashtags",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                competitor.topHashtags.take(4).forEach { tag ->
                    HashtagChip(hashtag = tag)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Content Themes",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                competitor.contentThemes.take(3).forEach { theme ->
                    SuggestionChip(
                        onClick = { },
                        label = { Text(theme) }
                    )
                }
            }
        }
    }
}
