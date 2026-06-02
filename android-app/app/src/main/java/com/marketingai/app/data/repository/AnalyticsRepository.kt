package com.marketingai.app.data.repository

import com.marketingai.app.data.api.ApiService
import com.marketingai.app.data.models.PerformanceMetrics
import com.marketingai.app.data.models.ThemeScoreResponse
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AnalyticsRepository @Inject constructor(
    private val apiService: ApiService
) {

    suspend fun getPerformanceMetrics(businessId: Int): ApiResult<PerformanceMetrics> {
        return try {
            val response = apiService.getPerformanceMetrics(businessId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to load metrics",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun getThemeScore(businessId: Int): ApiResult<ThemeScoreResponse> {
        return try {
            val response = apiService.getThemeScore(businessId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to load theme score",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }
}
