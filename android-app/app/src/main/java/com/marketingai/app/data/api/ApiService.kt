package com.marketingai.app.data.api

import com.marketingai.app.data.models.*
import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // Health
    @GET("/health")
    suspend fun healthCheck(): Response<HealthResponse>

    // Business endpoints
    @POST("/api/business/setup")
    suspend fun setupBusiness(@Body request: BusinessSetupRequest): Response<BusinessResponse>

    @PUT("/api/business/update")
    suspend fun updateBusiness(
        @Query("business_id") businessId: Int = 1,
        @Body request: BusinessUpdateRequest
    ): Response<BusinessResponse>

    @Multipart
    @POST("/api/business/logo")
    suspend fun uploadLogo(
        @Query("business_id") businessId: Int = 1,
        @Part file: MultipartBody.Part
    ): Response<BusinessResponse>

    @GET("/api/business/{business_id}")
    suspend fun getBusiness(@Path("business_id") businessId: Int): Response<BusinessResponse>

    // Content endpoints
    @POST("/api/content/generate")
    suspend fun generateContent(@Body request: ContentGenerateRequest): Response<List<GeneratedPostResponse>>

    @GET("/api/content/calendar")
    suspend fun getContentCalendar(
        @Query("business_id") businessId: Int = 1
    ): Response<ContentCalendarResponse>

    @POST("/api/content/approve/{post_id}")
    suspend fun approveContent(@Path("post_id") postId: Int): Response<ContentApproveResponse>

    @POST("/api/content/publish/{post_id}")
    suspend fun publishContent(@Path("post_id") postId: Int): Response<ContentApproveResponse>

    @POST("/api/content/regenerate/{post_id}")
    suspend fun regenerateContent(@Path("post_id") postId: Int): Response<GeneratedPostResponse>

    // Trends endpoints
    @GET("/api/trends/hashtags")
    suspend fun getTrendingHashtags(
        @Query("platform") platform: String = "instagram",
        @Query("industry") industry: String = "general",
        @Query("limit") limit: Int = 20
    ): Response<TrendsResponse>

    @GET("/api/trends/competitors")
    suspend fun getCompetitorAnalysis(
        @Query("industry") industry: String = "technology",
        @Query("platform") platform: String? = null
    ): Response<List<CompetitorAnalysisResponse>>

    // Analytics endpoints
    @GET("/api/analytics/performance")
    suspend fun getPerformanceMetrics(
        @Query("business_id") businessId: Int = 1
    ): Response<PerformanceMetrics>

    @GET("/api/analytics/theme-score")
    suspend fun getThemeScore(
        @Query("business_id") businessId: Int = 1
    ): Response<ThemeScoreResponse>

    // Schedule endpoints
    @POST("/api/schedule/configure")
    suspend fun configureSchedule(@Body request: ScheduleConfigureRequest): Response<ScheduleResponse>

    @GET("/api/schedule/current")
    suspend fun getCurrentSchedule(
        @Query("business_id") businessId: Int = 1,
        @Query("platform") platform: String? = null
    ): Response<ScheduleListResponse>

    @PUT("/api/schedule/update/{schedule_id}")
    suspend fun updateSchedule(
        @Path("schedule_id") scheduleId: Int,
        @Body request: ScheduleUpdateRequest
    ): Response<ScheduleResponse>

    @GET("/api/schedule/suggestions")
    suspend fun getScheduleSuggestions(
        @Query("platform") platform: String = "instagram",
        @Query("timezone") timezone: String = "UTC"
    ): Response<ScheduleSuggestionsResponse>

    // Campaign endpoints
    @POST("/api/campaigns/create")
    suspend fun createCampaign(@Body request: CampaignCreateRequest): Response<CampaignResponse>

    @GET("/api/campaigns/{campaign_id}")
    suspend fun getCampaign(@Path("campaign_id") campaignId: Int): Response<CampaignResponse>

    @POST("/api/campaigns/{campaign_id}/generate-creatives")
    suspend fun generateCreatives(@Path("campaign_id") campaignId: Int): Response<CampaignResponse>

    @GET("/api/campaigns/list")
    suspend fun listCampaigns(
        @Query("business_id") businessId: Int = 1
    ): Response<CampaignListResponse>

    @DELETE("/api/campaigns/{campaign_id}")
    suspend fun deleteCampaign(@Path("campaign_id") campaignId: Int): Response<DeleteResponse>

    // Image Generation endpoints (Bria AI on AWS Bedrock)
    @POST("/api/images/generate")
    suspend fun generateImage(@Body request: ImageGenerateRequest): Response<ImageGenerateResponse>

    @POST("/api/content/{post_id}/generate-image")
    suspend fun generatePostImage(@Path("post_id") postId: Int): Response<PostImageGenerateResponse>

    @GET("/api/images/models")
    suspend fun getImageModels(): Response<ImageModelsResponse>

    @GET("/api/images/platforms")
    suspend fun getImagePlatforms(): Response<ImagePlatformsResponse>
}
