package com.marketingai.app.ui.screens.onboarding

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketingai.app.ui.components.BrandVoiceSelector
import com.marketingai.app.ui.components.ColorPicker
import com.marketingai.app.ui.theme.FacebookColor
import com.marketingai.app.ui.theme.InstagramColor
import com.marketingai.app.ui.theme.TikTokColor

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OnboardingScreen(
    onSetupComplete: () -> Unit,
    viewModel: OnboardingViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(uiState.isSetupComplete) {
        if (uiState.isSetupComplete) {
            onSetupComplete()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        "PostPilot",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 24.dp)
        ) {
            // Progress indicator
            LinearProgressIndicator(
                progress = { (uiState.currentStep + 1).toFloat() / (uiState.totalSteps + 1) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 16.dp)
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp))
            )

            Text(
                text = "Step ${uiState.currentStep + 1} of ${uiState.totalSteps + 1}",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Step content
            AnimatedContent(
                targetState = uiState.currentStep,
                transitionSpec = {
                    slideInHorizontally { it } togetherWith slideOutHorizontally { -it }
                },
                modifier = Modifier.weight(1f),
                label = "step_animation"
            ) { step ->
                when (step) {
                    0 -> WelcomeStep()
                    1 -> BusinessInfoStep(
                        businessName = uiState.businessName,
                        industry = uiState.industry,
                        description = uiState.description,
                        website = uiState.website,
                        onBusinessNameChange = viewModel::updateBusinessName,
                        onIndustryChange = viewModel::updateIndustry,
                        onDescriptionChange = viewModel::updateDescription,
                        onWebsiteChange = viewModel::updateWebsite
                    )
                    2 -> AudienceStep(
                        targetAudience = uiState.targetAudience,
                        uniqueSellingPoints = uiState.uniqueSellingPoints,
                        onAudienceChange = viewModel::updateTargetAudience,
                        onAddSellingPoint = viewModel::addSellingPoint,
                        onRemoveSellingPoint = viewModel::removeSellingPoint
                    )
                    3 -> BrandVoiceStep(
                        selectedVoice = uiState.brandVoice,
                        onVoiceSelected = viewModel::updateBrandVoice
                    )
                    4 -> BrandColorsStep(
                        selectedColors = uiState.brandColors,
                        onAddColor = viewModel::addBrandColor,
                        onRemoveColor = viewModel::removeBrandColor
                    )
                    5 -> PlatformSelectionStep(
                        selectedPlatforms = uiState.selectedPlatforms,
                        onTogglePlatform = viewModel::togglePlatform
                    )
                }
            }

            // Error message
            uiState.error?.let { error ->
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Warning,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.error
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = error,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.weight(1f)
                        )
                        IconButton(onClick = viewModel::dismissError) {
                            Icon(Icons.Default.Close, contentDescription = "Dismiss")
                        }
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
            }

            // Navigation buttons
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                if (uiState.currentStep > 0) {
                    OutlinedButton(
                        onClick = viewModel::previousStep
                    ) {
                        Icon(Icons.Default.ArrowBack, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Back")
                    }
                } else {
                    Spacer(modifier = Modifier.width(1.dp))
                }

                if (uiState.currentStep < uiState.totalSteps - 1) {
                    Button(
                        onClick = viewModel::nextStep,
                        enabled = viewModel.canProceed()
                    ) {
                        Text("Next")
                        Spacer(modifier = Modifier.width(8.dp))
                        Icon(Icons.Default.ArrowForward, contentDescription = null)
                    }
                } else {
                    Button(
                        onClick = viewModel::submitSetup,
                        enabled = viewModel.canProceed() && !uiState.isLoading
                    ) {
                        if (uiState.isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(20.dp),
                                color = MaterialTheme.colorScheme.onPrimary,
                                strokeWidth = 2.dp
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                        }
                        Text("Complete Setup")
                        Spacer(modifier = Modifier.width(8.dp))
                        Icon(Icons.Default.Check, contentDescription = null)
                    }
                }
            }
        }
    }
}

@Composable
private fun WelcomeStep() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Brand icon representation
        Box(
            modifier = Modifier
                .size(120.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primary),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                Icons.Default.Rocket,
                contentDescription = "PostPilot",
                tint = Color.White,
                modifier = Modifier.size(64.dp)
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        Text(
            text = "PostPilot",
            style = MaterialTheme.typography.displaySmall,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = "AI-Powered Content That Converts",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.secondary,
            textAlign = TextAlign.Center,
            fontWeight = FontWeight.Medium
        )

        Spacer(modifier = Modifier.height(32.dp))

        Text(
            text = "Your AI co-pilot for creating scroll-stopping social media content. Built for South African businesses ready to grow on TikTok, Instagram, and Facebook.",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 16.dp)
        )

        Spacer(modifier = Modifier.height(48.dp))

        // Feature highlights
        FeatureHighlight(
            icon = Icons.Default.AutoAwesome,
            title = "AI Content Generation",
            description = "Claude AI creates posts tailored to your brand voice"
        )
        Spacer(modifier = Modifier.height(16.dp))
        FeatureHighlight(
            icon = Icons.Default.TrendingUp,
            title = "Trending Hashtags",
            description = "Stay on top of what is trending in your industry"
        )
        Spacer(modifier = Modifier.height(16.dp))
        FeatureHighlight(
            icon = Icons.Default.Schedule,
            title = "Smart Scheduling",
            description = "Post at the best times for maximum engagement"
        )
    }
}

@Composable
private fun FeatureHighlight(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    description: String
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.primaryContainer),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(22.dp)
            )
        }
        Spacer(modifier = Modifier.width(16.dp))
        Column {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun BusinessInfoStep(
    businessName: String,
    industry: String,
    description: String,
    website: String,
    onBusinessNameChange: (String) -> Unit,
    onIndustryChange: (String) -> Unit,
    onDescriptionChange: (String) -> Unit,
    onWebsiteChange: (String) -> Unit
) {
    Column(
        modifier = Modifier.verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "Tell us about your business",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "This helps us create content that matches your brand identity.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(24.dp))

        OutlinedTextField(
            value = businessName,
            onValueChange = onBusinessNameChange,
            label = { Text("Business Name") },
            placeholder = { Text("e.g., Acme Coffee Co.") },
            leadingIcon = { Icon(Icons.Default.Business, contentDescription = null) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = industry,
            onValueChange = onIndustryChange,
            label = { Text("Industry") },
            placeholder = { Text("e.g., Food & Beverage") },
            leadingIcon = { Icon(Icons.Default.Category, contentDescription = null) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = description,
            onValueChange = onDescriptionChange,
            label = { Text("Description (Optional)") },
            placeholder = { Text("A brief description of what you do...") },
            leadingIcon = { Icon(Icons.Default.Description, contentDescription = null) },
            maxLines = 3,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = website,
            onValueChange = onWebsiteChange,
            label = { Text("Website (Optional)") },
            placeholder = { Text("https://yoursite.com") },
            leadingIcon = { Icon(Icons.Default.Language, contentDescription = null) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
    }
}

@Composable
private fun AudienceStep(
    targetAudience: String,
    uniqueSellingPoints: List<String>,
    onAudienceChange: (String) -> Unit,
    onAddSellingPoint: (String) -> Unit,
    onRemoveSellingPoint: (String) -> Unit
) {
    var newSellingPoint by remember { mutableStateOf("") }

    Column(
        modifier = Modifier.verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "Who is your audience?",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Understanding your audience helps us tailor messaging and tone.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(24.dp))

        OutlinedTextField(
            value = targetAudience,
            onValueChange = onAudienceChange,
            label = { Text("Target Audience") },
            placeholder = { Text("e.g., Health-conscious millennials aged 25-40") },
            leadingIcon = { Icon(Icons.Default.People, contentDescription = null) },
            maxLines = 3,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = "Unique Selling Points",
            style = MaterialTheme.typography.titleMedium
        )
        Spacer(modifier = Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = newSellingPoint,
                onValueChange = { newSellingPoint = it },
                placeholder = { Text("Add a selling point") },
                singleLine = true,
                modifier = Modifier.weight(1f)
            )
            Spacer(modifier = Modifier.width(8.dp))
            FilledIconButton(
                onClick = {
                    onAddSellingPoint(newSellingPoint)
                    newSellingPoint = ""
                },
                enabled = newSellingPoint.isNotBlank()
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add")
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        uniqueSellingPoints.forEach { point ->
            InputChip(
                selected = true,
                onClick = { onRemoveSellingPoint(point) },
                label = { Text(point) },
                trailingIcon = {
                    Icon(Icons.Default.Close, contentDescription = "Remove", modifier = Modifier.size(16.dp))
                },
                modifier = Modifier.padding(end = 8.dp, bottom = 8.dp)
            )
        }
    }
}

@Composable
private fun BrandVoiceStep(
    selectedVoice: String,
    onVoiceSelected: (String) -> Unit
) {
    Column(
        modifier = Modifier.verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "Choose your brand voice",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "This sets the tone for all generated content.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(24.dp))

        BrandVoiceSelector(
            selectedVoice = selectedVoice,
            onVoiceSelected = onVoiceSelected
        )
    }
}

@Composable
private fun BrandColorsStep(
    selectedColors: List<String>,
    onAddColor: (String) -> Unit,
    onRemoveColor: (String) -> Unit
) {
    Column(
        modifier = Modifier.verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "Brand Colors",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Pick colors that represent your brand for generated images.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(24.dp))

        // Selected colors display
        Text(
            text = "Selected Colors (${selectedColors.size})",
            style = MaterialTheme.typography.titleSmall
        )
        Spacer(modifier = Modifier.height(8.dp))

        LazyRow(
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(selectedColors) { colorHex ->
                val color = try {
                    Color(android.graphics.Color.parseColor(colorHex))
                } catch (e: Exception) {
                    MaterialTheme.colorScheme.primary
                }
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(CircleShape)
                        .background(color)
                        .border(2.dp, MaterialTheme.colorScheme.outline, CircleShape)
                        .clickable { onRemoveColor(colorHex) },
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        Icons.Default.Close,
                        contentDescription = "Remove color",
                        tint = Color.White,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        ColorPicker(
            onColorSelected = onAddColor
        )
    }
}

@Composable
private fun PlatformSelectionStep(
    selectedPlatforms: Set<String>,
    onTogglePlatform: (String) -> Unit
) {
    Column(
        modifier = Modifier.verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "Select your platforms",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Choose which social media platforms you want content for.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(24.dp))

        PlatformCard(
            name = "TikTok",
            description = "Short-form video content with trending sounds and effects",
            color = TikTokColor,
            isSelected = "tiktok" in selectedPlatforms,
            onClick = { onTogglePlatform("tiktok") }
        )
        Spacer(modifier = Modifier.height(12.dp))

        PlatformCard(
            name = "Instagram",
            description = "Visual storytelling with reels, stories, and feed posts",
            color = InstagramColor,
            isSelected = "instagram" in selectedPlatforms,
            onClick = { onTogglePlatform("instagram") }
        )
        Spacer(modifier = Modifier.height(12.dp))

        PlatformCard(
            name = "Facebook",
            description = "Community engagement with longer-form posts and groups",
            color = FacebookColor,
            isSelected = "facebook" in selectedPlatforms,
            onClick = { onTogglePlatform("facebook") }
        )
    }
}

@Composable
private fun PlatformCard(
    name: String,
    description: String,
    color: Color,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected)
                color.copy(alpha = 0.1f)
            else
                MaterialTheme.colorScheme.surfaceVariant
        ),
        border = if (isSelected) {
            CardDefaults.outlinedCardBorder().copy(
                width = 2.dp
            )
        } else null
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(color),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = name.first().toString(),
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            if (isSelected) {
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = "Selected",
                    tint = color
                )
            }
        }
    }
}
