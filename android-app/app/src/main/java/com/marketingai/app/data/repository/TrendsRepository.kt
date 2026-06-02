package com.marketingai.app.data.repository

import com.marketingai.app.data.api.ApiService
import com.marketingai.app.data.models.CompetitorAnalysisResponse
import com.marketingai.app.data.models.TrendsResponse
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TrendsRepository @Inject constructor(
    private val apiService: ApiService
) {

    suspend fun getTrendingHashtags(
        platform: String = "instagram",
        industry: String = "general",
        limit: Int = 20
    ): ApiResult<TrendsResponse> {
        return try {
            val response = apiService.getTrendingHashtags(platform, industry, limit)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to load trends",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun getCompetitorAnalysis(
        industry: String = "technology",
        platform: String? = null
    ): ApiResult<List<CompetitorAnalysisResponse>> {
        return try {
            val response = apiService.getCompetitorAnalysis(industry, platform)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Analysis failed",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }
}
