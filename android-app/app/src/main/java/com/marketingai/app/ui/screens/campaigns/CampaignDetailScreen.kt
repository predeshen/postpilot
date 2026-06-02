package com.marketingai.app.ui.screens.campaigns

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketingai.app.data.models.CampaignAngleResponse
import com.marketingai.app.data.models.CampaignCreativeResponse

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CampaignDetailScreen(
    campaignId: Int,
    onNavigateBack: () -> Unit,
    viewModel: CampaignViewModel = hiltViewModel()
) {
    val uiState by viewModel.detailState.collectAsStateWithLifecycle()
    val clipboardManager = LocalClipboardManager.current

    LaunchedEffect(campaignId) {
        viewModel.loadCampaignDetail(campaignId)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = uiState.campaign?.name ?: "Campaign Detail",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        uiState.campaign?.let { campaign ->
                            Text(
                                text = campaign.objective.replaceFirstChar { it.uppercase() },
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    // Export approved creatives
                    uiState.campaign?.let { campaign ->
                        val approvedCreatives = campaign.angles
                            .flatMap { it.creatives }
                            .filter { it.status == "approved" }
                        if (approvedCreatives.isNotEmpty()) {
                            IconButton(onClick = {
                                val exportText = buildExportText(campaign.name, campaign.angles)
                                clipboardManager.setText(AnnotatedString(exportText))
                            }) {
                                Icon(Icons.Default.ContentCopy, contentDescription = "Export Approved")
                            }
                        }
                    }
                }
            )
        }
    ) { paddingValues ->
        when {
            uiState.isLoading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            uiState.campaign == null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = uiState.error ?: "Campaign not found",
                        style = MaterialTheme.typography.bodyLarge
                    )
                }
            }
            else -> {
                val campaign = uiState.campaign!!
                val hasCreatives = campaign.angles.any { it.creatives.isNotEmpty() }

                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Campaign info header
                    item {
                        CampaignInfoCard(campaign)
                    }

                    // Generate creatives button if no creatives yet
                    if (!hasCreatives) {
                        item {
                            Button(
                                onClick = { viewModel.generateCreatives(campaignId) },
                                modifier = Modifier.fillMaxWidth(),
                                enabled = !uiState.isGeneratingCreatives
                            ) {
                                if (uiState.isGeneratingCreatives) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(20.dp),
                                        strokeWidth = 2.dp,
                                        color = MaterialTheme.colorScheme.onPrimary
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Generating 15 Creatives...")
                                } else {
                                    Icon(Icons.Default.AutoAwesome, contentDescription = null)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Generate 5 Creatives Per Angle")
                                }
                            }
                        }
                    }

                    // Angles with creatives
                    items(campaign.angles, key = { it.id }) { angle ->
                        AngleCard(angle = angle)
                    }
                }
            }
        }
    }
}

@Composable
private fun CampaignInfoCard(campaign: com.marketingai.app.data.models.CampaignResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            campaign.productService?.let { product ->
                Text(
                    text = "Promoting: $product",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium
                )
                Spacer(modifier = Modifier.height(4.dp))
            }
            campaign.targetAudience?.let { audience ->
                Text(
                    text = "Target: $audience",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
                Spacer(modifier = Modifier.height(4.dp))
            }
            campaign.budgetRange?.let { budget ->
                Text(
                    text = "Budget: $budget",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }

            Spacer(modifier = Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                val totalCreatives = campaign.angles.sumOf { it.creatives.size }
                val approvedCreatives = campaign.angles
                    .flatMap { it.creatives }
                    .count { it.status == "approved" }

                SuggestionChip(
                    onClick = {},
                    label = { Text("${campaign.angles.size} Angles") }
                )
                SuggestionChip(
                    onClick = {},
                    label = { Text("$totalCreatives Creatives") }
                )
                if (approvedCreatives > 0) {
                    SuggestionChip(
                        onClick = {},
                        label = { Text("$approvedCreatives Approved") }
                    )
                }
            }
        }
    }
}

@Composable
private fun AngleCard(angle: CampaignAngleResponse) {
    var expanded by remember { mutableStateOf(true) }

    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Angle header (clickable to expand/collapse)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "Angle ${angle.angleNumber}: ${angle.title}",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = angle.hookType.replace("_", " ").replaceFirstChar { it.uppercase() },
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                    angle.targetEmotion?.let { emotion ->
                        Text(
                            text = "Target emotion: $emotion",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                IconButton(onClick = { expanded = !expanded }) {
                    Icon(
                        if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                        contentDescription = if (expanded) "Collapse" else "Expand"
                    )
                }
            }

            angle.description?.let { desc ->
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = desc,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // Creatives list (collapsible)
            AnimatedVisibility(visible = expanded) {
                Column(
                    modifier = Modifier.padding(top = 12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    angle.creatives.forEach { creative ->
                        CreativeCard(creative = creative)
                    }

                    if (angle.creatives.isEmpty()) {
                        Text(
                            text = "No creatives generated yet. Tap 'Generate Creatives' above.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(vertical = 8.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CreativeCard(creative: CampaignCreativeResponse) {
    OutlinedCard(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            // Header row with creative number and status
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = creative.headline,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f)
                )
                StatusBadge(status = creative.status)
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Primary text preview
            Text(
                text = creative.primaryText,
                style = MaterialTheme.typography.bodySmall,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Meta info row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                AssistChip(
                    onClick = {},
                    label = {
                        Text(
                            creative.adFormat.replace("_", " "),
                            style = MaterialTheme.typography.labelSmall
                        )
                    },
                    modifier = Modifier.height(24.dp)
                )
                AssistChip(
                    onClick = {},
                    label = {
                        Text(
                            creative.platformPlacement,
                            style = MaterialTheme.typography.labelSmall
                        )
                    },
                    modifier = Modifier.height(24.dp)
                )
                AssistChip(
                    onClick = {},
                    label = {
                        Text(
                            creative.callToAction.replace("_", " "),
                            style = MaterialTheme.typography.labelSmall
                        )
                    },
                    modifier = Modifier.height(24.dp)
                )
            }
        }
    }
}

@Composable
private fun StatusBadge(status: String) {
    val (color, text) = when (status) {
        "approved" -> MaterialTheme.colorScheme.primary to "Approved"
        "rejected" -> MaterialTheme.colorScheme.error to "Rejected"
        else -> MaterialTheme.colorScheme.outline to "Draft"
    }

    Surface(
        color = color.copy(alpha = 0.1f),
        shape = MaterialTheme.shapes.small
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = color,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
        )
    }
}

private fun buildExportText(
    campaignName: String,
    angles: List<CampaignAngleResponse>
): String {
    val sb = StringBuilder()
    sb.appendLine("=== $campaignName - Approved Creatives ===")
    sb.appendLine()

    angles.forEach { angle ->
        val approvedCreatives = angle.creatives.filter { it.status == "approved" }
        if (approvedCreatives.isNotEmpty()) {
            sb.appendLine("--- Angle ${angle.angleNumber}: ${angle.title} (${angle.hookType}) ---")
            sb.appendLine()

            approvedCreatives.forEach { creative ->
                sb.appendLine("Creative #${creative.creativeNumber}")
                sb.appendLine("Headline: ${creative.headline}")
                sb.appendLine("Primary Text: ${creative.primaryText}")
                creative.description?.let { sb.appendLine("Description: $it") }
                sb.appendLine("CTA: ${creative.callToAction}")
                creative.imageConcept?.let { sb.appendLine("Image Concept: $it") }
                sb.appendLine("Format: ${creative.adFormat} | Placement: ${creative.platformPlacement}")
                sb.appendLine()
            }
        }
    }

    return sb.toString()
}
