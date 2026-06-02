package com.marketingai.app.ui.screens.dashboard

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
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
import com.marketingai.app.ui.components.CalendarView
import com.marketingai.app.ui.components.PlatformPostCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    onNavigateToContent: (Int) -> Unit,
    onNavigateToSchedule: () -> Unit,
    onNavigateToTrending: () -> Unit,
    onNavigateToAnalytics: () -> Unit,
    onNavigateToSettings: () -> Unit,
    onNavigateToCampaigns: () -> Unit,
    viewModel: DashboardViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "PostPilot",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Text(
                            "AI-Powered Content That Converts",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                }
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = true,
                    onClick = { },
                    icon = { Icon(Icons.Default.Dashboard, contentDescription = null) },
                    label = { Text("Dashboard") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = onNavigateToSchedule,
                    icon = { Icon(Icons.Default.Schedule, contentDescription = null) },
                    label = { Text("Schedule") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = onNavigateToTrending,
                    icon = { Icon(Icons.Default.TrendingUp, contentDescription = null) },
                    label = { Text("Trending") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = onNavigateToAnalytics,
                    icon = { Icon(Icons.Default.Analytics, contentDescription = null) },
                    label = { Text("Analytics") }
                )
            }
        }
    ) { paddingValues ->
        if (uiState.isLoading && uiState.posts.isEmpty()) {
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
                // Stats overview cards
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        StatCard(
                            title = "Total",
                            value = uiState.totalPosts.toString(),
                            icon = Icons.Default.Article,
                            modifier = Modifier.weight(1f)
                        )
                        StatCard(
                            title = "Upcoming",
                            value = uiState.upcomingPosts.toString(),
                            icon = Icons.Default.Upcoming,
                            modifier = Modifier.weight(1f)
                        )
                        StatCard(
                            title = "Published",
                            value = uiState.publishedPosts.toString(),
                            icon = Icons.Default.Publish,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }

                // Meta Ads Campaigns quick action
                item {
                    Card(
                        onClick = onNavigateToCampaigns,
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.secondaryContainer
                        )
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Icon(
                                Icons.Default.Campaign,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onSecondaryContainer,
                                modifier = Modifier.size(32.dp)
                            )
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "Meta Ads Campaigns",
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.SemiBold
                                )
                                Text(
                                    text = "Generate 3 angles with 5 creatives each",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                            Icon(
                                Icons.Default.ArrowForward,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onSecondaryContainer
                            )
                        }
                    }
                }

                // Content pillar balance
                if (uiState.pillarDistribution.isNotEmpty()) {
                    item {
                        Card(
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text(
                                    text = "Content Pillar Balance",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.SemiBold
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                uiState.pillarDistribution.forEach { (pillar, count) ->
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(vertical = 4.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = pillar.replaceFirstChar { it.uppercase() },
                                            style = MaterialTheme.typography.bodyMedium,
                                            modifier = Modifier.width(120.dp)
                                        )
                                        LinearProgressIndicator(
                                            progress = {
                                                if (uiState.totalPosts > 0) {
                                                    count.toFloat() / uiState.totalPosts
                                                } else 0f
                                            },
                                            modifier = Modifier
                                                .weight(1f)
                                                .height(8.dp)
                                        )
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(
                                            text = count.toString(),
                                            style = MaterialTheme.typography.labelSmall
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                // Calendar section
                item {
                    CalendarView(
                        posts = uiState.posts,
                        onPostClick = { post -> onNavigateToContent(post.id) }
                    )
                }

                // Filter chips
                item {
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(PostFilter.entries) { filter ->
                            FilterChip(
                                selected = uiState.selectedFilter == filter,
                                onClick = { viewModel.setFilter(filter) },
                                label = { Text(filter.label) }
                            )
                        }
                    }
                }

                // Posts list
                val posts = when (uiState.selectedFilter) {
                    PostFilter.ALL -> uiState.posts
                    PostFilter.DRAFT -> uiState.posts.filter { it.status == "draft" }
                    PostFilter.APPROVED -> uiState.posts.filter { it.status == "approved" }
                    PostFilter.PUBLISHED -> uiState.posts.filter { it.status == "published" }
                }

                items(posts, key = { it.id }) { post ->
                    PlatformPostCard(
                        post = post,
                        onApprove = { viewModel.approvePost(post.id) },
                        onRegenerate = { viewModel.regeneratePost(post.id) },
                        onClick = { onNavigateToContent(post.id) }
                    )
                }

                // Empty state
                if (posts.isEmpty() && !uiState.isLoading) {
                    item {
                        Card(
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(32.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    Icons.Default.Article,
                                    contentDescription = null,
                                    modifier = Modifier.size(48.dp),
                                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = "No posts yet",
                                    style = MaterialTheme.typography.titleMedium
                                )
                                Text(
                                    text = "Generate your first content from the schedule screen.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            }
        }

        // Error handling
        uiState.error?.let { error ->
            Snackbar(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(error)
            }
        }
    }
}

@Composable
private fun StatCard(
    title: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = title,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
