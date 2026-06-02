package com.marketingai.app.data.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class BusinessSetupRequest(
    val name: String,
    val industry: String,
    val description: String? = null,
    @Json(name = "brand_voice") val brandVoice: String = "professional",
    @Json(name = "brand_colors") val brandColors: List<String> = emptyList(),
    @Json(name = "target_audience") val targetAudience: String? = null,
    @Json(name = "unique_selling_points") val uniqueSellingPoints: List<String> = emptyList(),
    val languages: List<String> = listOf("en"),
    val website: String? = null
)

@JsonClass(generateAdapter = true)
data class BusinessUpdateRequest(
    val name: String? = null,
    val industry: String? = null,
    val description: String? = null,
    @Json(name = "brand_voice") val brandVoice: String? = null,
    @Json(name = "brand_colors") val brandColors: List<String>? = null,
    @Json(name = "target_audience") val targetAudience: String? = null,
    @Json(name = "unique_selling_points") val uniqueSellingPoints: List<String>? = null,
    val languages: List<String>? = null,
    val website: String? = null
)

@JsonClass(generateAdapter = true)
data class BusinessResponse(
    val id: Int,
    val name: String,
    val industry: String,
    val description: String? = null,
    @Json(name = "brand_voice") val brandVoice: String,
    @Json(name = "brand_colors") val brandColors: List<String>,
    @Json(name = "logo_path") val logoPath: String? = null,
    @Json(name = "target_audience") val targetAudience: String? = null,
    @Json(name = "unique_selling_points") val uniqueSellingPoints: List<String>,
    val languages: List<String>,
    val website: String? = null,
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "updated_at") val updatedAt: String
)

@JsonClass(generateAdapter = true)
data class ContentGenerateRequest(
    @Json(name = "business_id") val businessId: Int,
    val platform: String,
    @Json(name = "pillar_type") val pillarType: String? = null,
    val language: String = "en",
    @Json(name = "num_variants") val numVariants: Int = 2,
    val topic: String? = null,
    @Json(name = "include_hashtags") val includeHashtags: Boolean = true,
    @Json(name = "include_image") val includeImage: Boolean = false
)

@JsonClass(generateAdapter = true)
data class GeneratedPostResponse(
    val id: Int,
    @Json(name = "business_id") val businessId: Int,
    val platform: String,
    val content: String,
    val hashtags: List<String>,
    @Json(name = "image_path") val imagePath: String? = null,
    val status: String,
    @Json(name = "pillar_type") val pillarType: String? = null,
    @Json(name = "engagement_hook") val engagementHook: String? = null,
    @Json(name = "scheduled_at") val scheduledAt: String? = null,
    @Json(name = "published_at") val publishedAt: String? = null,
    @Json(name = "variant_group") val variantGroup: String? = null,
    val language: String,
    @Json(name = "theme_score") val themeScore: Float? = null,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class ContentCalendarResponse(
    val posts: List<GeneratedPostResponse>,
    val total: Int,
    val upcoming: Int,
    val published: Int
)

@JsonClass(generateAdapter = true)
data class ContentApproveResponse(
    val id: Int,
    val status: String,
    val message: String
)

@JsonClass(generateAdapter = true)
data class TrendingHashtagResponse(
    val hashtag: String,
    val platform: String,
    val category: String? = null,
    @Json(name = "relevance_score") val relevanceScore: Float,
    @Json(name = "trend_score") val trendScore: Float,
    @Json(name = "usage_count") val usageCount: Int
)

@JsonClass(generateAdapter = true)
data class TrendsResponse(
    val platform: String,
    val hashtags: List<TrendingHashtagResponse>,
    @Json(name = "updated_at") val updatedAt: String
)

@JsonClass(generateAdapter = true)
data class CompetitorAnalysisResponse(
    @Json(name = "competitor_name") val competitorName: String,
    @Json(name = "top_hashtags") val topHashtags: List<String>,
    @Json(name = "posting_frequency") val postingFrequency: String,
    @Json(name = "engagement_rate") val engagementRate: Float,
    @Json(name = "content_themes") val contentThemes: List<String>
)

@JsonClass(generateAdapter = true)
data class PerformanceMetrics(
    @Json(name = "total_posts") val totalPosts: Int,
    @Json(name = "published_posts") val publishedPosts: Int,
    @Json(name = "average_engagement_rate") val averageEngagementRate: Float,
    @Json(name = "top_performing_platform") val topPerformingPlatform: String? = null,
    @Json(name = "top_performing_pillar") val topPerformingPillar: String? = null,
    @Json(name = "posts_by_platform") val postsByPlatform: Map<String, Int>,
    @Json(name = "posts_by_status") val postsByStatus: Map<String, Int>
)

@JsonClass(generateAdapter = true)
data class ThemeScoreResponse(
    @Json(name = "overall_score") val overallScore: Float,
    @Json(name = "brand_voice_consistency") val brandVoiceConsistency: Float,
    @Json(name = "visual_consistency") val visualConsistency: Float,
    @Json(name = "content_pillar_balance") val contentPillarBalance: Map<String, Float>,
    val recommendations: List<String>
)

@JsonClass(generateAdapter = true)
data class ScheduleConfigureRequest(
    @Json(name = "business_id") val businessId: Int,
    val platform: String,
    @Json(name = "day_of_week") val dayOfWeek: Int,
    @Json(name = "time_slot") val timeSlot: String,
    val timezone: String = "UTC",
    @Json(name = "pillar_type") val pillarType: String? = null,
    @Json(name = "series_name") val seriesName: String? = null
)

@JsonClass(generateAdapter = true)
data class ScheduleUpdateRequest(
    @Json(name = "day_of_week") val dayOfWeek: Int? = null,
    @Json(name = "time_slot") val timeSlot: String? = null,
    val timezone: String? = null,
    @Json(name = "pillar_type") val pillarType: String? = null,
    @Json(name = "series_name") val seriesName: String? = null,
    @Json(name = "is_active") val isActive: Boolean? = null
)

@JsonClass(generateAdapter = true)
data class ScheduleResponse(
    val id: Int,
    @Json(name = "business_id") val businessId: Int,
    val platform: String,
    @Json(name = "day_of_week") val dayOfWeek: Int,
    @Json(name = "time_slot") val timeSlot: String,
    val timezone: String,
    @Json(name = "pillar_type") val pillarType: String? = null,
    @Json(name = "is_active") val isActive: Boolean,
    @Json(name = "series_name") val seriesName: String? = null,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class ScheduleListResponse(
    val schedules: List<ScheduleResponse>,
    val total: Int
)

@JsonClass(generateAdapter = true)
data class ScheduleSuggestionsResponse(
    val platform: String,
    @Json(name = "best_posting_times") val bestPostingTimes: Map<String, List<String>>,
    @Json(name = "content_series") val contentSeries: List<ContentSeriesSuggestion>,
    @Json(name = "upcoming_holidays") val upcomingHolidays: List<HolidayEvent>
)

@JsonClass(generateAdapter = true)
data class ContentSeriesSuggestion(
    @Json(name = "series_id") val seriesId: String? = null,
    val name: String,
    val pillar: String? = null,
    val description: String,
    @Json(name = "day_name") val dayName: String? = null
)

@JsonClass(generateAdapter = true)
data class HolidayEvent(
    val name: String,
    val date: String,
    @Json(name = "days_until") val daysUntil: Int? = null,
    val category: String? = null
)

@JsonClass(generateAdapter = true)
data class HealthResponse(
    val status: String,
    val version: String,
    val service: String
)

@JsonClass(generateAdapter = true)
data class ErrorResponse(
    val detail: String,
    val code: String? = null
)

// ============== Campaign Models ==============

@JsonClass(generateAdapter = true)
data class CampaignCreateRequest(
    @Json(name = "business_id") val businessId: Int,
    @Json(name = "campaign_name") val campaignName: String,
    @Json(name = "campaign_objective") val campaignObjective: String,
    @Json(name = "target_audience") val targetAudience: String? = null,
    @Json(name = "product_service") val productService: String,
    @Json(name = "budget_range") val budgetRange: String? = null
)

@JsonClass(generateAdapter = true)
data class CampaignCreativeResponse(
    val id: Int,
    @Json(name = "angle_id") val angleId: Int,
    @Json(name = "creative_number") val creativeNumber: Int,
    val headline: String,
    @Json(name = "primary_text") val primaryText: String,
    val description: String? = null,
    @Json(name = "call_to_action") val callToAction: String,
    @Json(name = "image_concept") val imageConcept: String? = null,
    @Json(name = "image_base64") val imageBase64: String? = null,
    @Json(name = "ad_format") val adFormat: String,
    @Json(name = "platform_placement") val platformPlacement: String,
    val status: String,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class CampaignAngleResponse(
    val id: Int,
    @Json(name = "campaign_id") val campaignId: Int,
    @Json(name = "angle_number") val angleNumber: Int,
    @Json(name = "hook_type") val hookType: String,
    val title: String,
    val description: String? = null,
    @Json(name = "target_emotion") val targetEmotion: String? = null,
    val creatives: List<CampaignCreativeResponse> = emptyList(),
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class CampaignResponse(
    val id: Int,
    @Json(name = "business_id") val businessId: Int,
    val name: String,
    val objective: String,
    @Json(name = "target_audience") val targetAudience: String? = null,
    @Json(name = "product_service") val productService: String? = null,
    @Json(name = "budget_range") val budgetRange: String? = null,
    val status: String,
    val angles: List<CampaignAngleResponse> = emptyList(),
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "updated_at") val updatedAt: String
)

@JsonClass(generateAdapter = true)
data class CampaignListResponse(
    val campaigns: List<CampaignResponse>,
    val total: Int
)

@JsonClass(generateAdapter = true)
data class DeleteResponse(
    val detail: String,
    val id: Int
)

// ============== Image Generation Models (Bria AI) ==============

@JsonClass(generateAdapter = true)
data class ImageGenerateRequest(
    val prompt: String,
    val width: Int = 1080,
    val height: Int = 1080,
    @Json(name = "model_id") val modelId: String? = null
)

@JsonClass(generateAdapter = true)
data class ImageGenerateResponse(
    val success: Boolean,
    @Json(name = "image_base64") val imageBase64: String? = null,
    val width: Int,
    val height: Int,
    @Json(name = "model_id") val modelId: String,
    val prompt: String,
    @Json(name = "file_path") val filePath: String? = null
)

@JsonClass(generateAdapter = true)
data class PostImageGenerateResponse(
    @Json(name = "post_id") val postId: Int,
    @Json(name = "image_path") val imagePath: String? = null,
    @Json(name = "image_base64") val imageBase64: String? = null,
    val platform: String,
    val success: Boolean
)

@JsonClass(generateAdapter = true)
data class ImageModelInfo(
    val id: String,
    val name: String,
    val description: String
)

@JsonClass(generateAdapter = true)
data class ImageModelsResponse(
    val models: List<ImageModelInfo>,
    @Json(name = "default_model") val defaultModel: String
)

@JsonClass(generateAdapter = true)
data class PlatformDimension(
    val width: Int,
    val height: Int,
    val label: String
)

@JsonClass(generateAdapter = true)
data class ImagePlatformsResponse(
    val platforms: Map<String, PlatformDimension>
)
