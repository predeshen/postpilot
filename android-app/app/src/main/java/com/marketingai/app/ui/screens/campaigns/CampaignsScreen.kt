package com.marketingai.app.ui.screens.campaigns

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
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketingai.app.data.models.CampaignResponse

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CampaignsScreen(
    onNavigateBack: () -> Unit,
    onNavigateToCampaignDetail: (Int) -> Unit,
    viewModel: CampaignViewModel = hiltViewModel()
) {
    val uiState by viewModel.listState.collectAsStateWithLifecycle()

    // Create campaign dialog state
    var campaignName by remember { mutableStateOf("") }
    var campaignObjective by remember { mutableStateOf("conversions") }
    var targetAudience by remember { mutableStateOf("") }
    var productService by remember { mutableStateOf("") }
    var budgetRange by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "Meta Ads Campaigns",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            "Create and manage ad campaigns",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { viewModel.showCreateDialog() },
                icon = { Icon(Icons.Default.Add, contentDescription = null) },
                text = { Text("Create Campaign") }
            )
        }
    ) { paddingValues ->
        if (uiState.isLoading && uiState.campaigns.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (uiState.campaigns.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Icon(
                        Icons.Default.Campaign,
                        contentDescription = null,
                        modifier = Modifier.size(64.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "No campaigns yet",
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = "Create your first Meta Ads campaign to generate\n3 angles with 5 creatives each.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
                    Text(
                        text = "${uiState.totalCampaigns} campaign${if (uiState.totalCampaigns != 1) "s" else ""}",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                items(uiState.campaigns, key = { it.id }) { campaign ->
                    CampaignCard(
                        campaign = campaign,
                        onClick = { onNavigateToCampaignDetail(campaign.id) },
                        onDelete = { viewModel.deleteCampaign(campaign.id) }
                    )
                }
            }
        }

        // Error snackbar
        uiState.error?.let { error ->
            Snackbar(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(error)
            }
        }
    }

    // Create campaign dialog
    if (uiState.showCreateDialog) {
        AlertDialog(
            onDismissRequest = { viewModel.hideCreateDialog() },
            title = { Text("Create Campaign") },
            text = {
                Column(
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedTextField(
                        value = campaignName,
                        onValueChange = { campaignName = it },
                        label = { Text("Campaign Name") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = productService,
                        onValueChange = { productService = it },
                        label = { Text("Product/Service to Promote") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = targetAudience,
                        onValueChange = { targetAudience = it },
                        label = { Text("Target Audience (optional)") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = budgetRange,
                        onValueChange = { budgetRange = it },
                        label = { Text("Budget Range (optional)") },
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = { Text("e.g. R5000-R15000/month") },
                        singleLine = true
                    )

                    // Objective selector
                    Text(
                        text = "Campaign Objective",
                        style = MaterialTheme.typography.labelMedium
                    )
                    val objectives = listOf(
                        "conversions" to "Conversions",
                        "awareness" to "Awareness",
                        "traffic" to "Traffic",
                        "engagement" to "Engagement",
                        "leads" to "Leads",
                        "app_installs" to "App Installs"
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        objectives.take(3).forEach { (value, label) ->
                            FilterChip(
                                selected = campaignObjective == value,
                                onClick = { campaignObjective = value },
                                label = { Text(label, style = MaterialTheme.typography.labelSmall) }
                            )
                        }
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        objectives.drop(3).forEach { (value, label) ->
                            FilterChip(
                                selected = campaignObjective == value,
                                onClick = { campaignObjective = value },
                                label = { Text(label, style = MaterialTheme.typography.labelSmall) }
                            )
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.createCampaign(
                            campaignName = campaignName,
                            campaignObjective = campaignObjective,
                            targetAudience = targetAudience.ifBlank { null },
                            productService = productService,
                            budgetRange = budgetRange.ifBlank { null }
                        )
                        // Reset form
                        campaignName = ""
                        productService = ""
                        targetAudience = ""
                        budgetRange = ""
                        campaignObjective = "conversions"
                    },
                    enabled = campaignName.isNotBlank() && productService.isNotBlank() && !uiState.isCreating
                ) {
                    if (uiState.isCreating) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Text("Create")
                    }
                }
            },
            dismissButton = {
                TextButton(onClick = { viewModel.hideCreateDialog() }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun CampaignCard(
    campaign: CampaignResponse,
    onClick: () -> Unit,
    onDelete: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = campaign.name,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = campaign.objective.replaceFirstChar { it.uppercase() },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
                IconButton(onClick = onDelete) {
                    Icon(
                        Icons.Default.Delete,
                        contentDescription = "Delete",
                        tint = MaterialTheme.colorScheme.error
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                val angleCount = campaign.angles.size
                val creativeCount = campaign.angles.sumOf { it.creatives.size }

                AssistChip(
                    onClick = {},
                    label = { Text("$angleCount angles") },
                    leadingIcon = {
                        Icon(
                            Icons.Default.Layers,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                )
                AssistChip(
                    onClick = {},
                    label = { Text("$creativeCount creatives") },
                    leadingIcon = {
                        Icon(
                            Icons.Default.AutoAwesome,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                )
            }

            campaign.productService?.let { product ->
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = product,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}
