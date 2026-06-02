package com.marketingai.app.data.repository

import com.marketingai.app.data.api.ApiService
import com.marketingai.app.data.models.ScheduleConfigureRequest
import com.marketingai.app.data.models.ScheduleListResponse
import com.marketingai.app.data.models.ScheduleResponse
import com.marketingai.app.data.models.ScheduleSuggestionsResponse
import com.marketingai.app.data.models.ScheduleUpdateRequest
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ScheduleRepository @Inject constructor(
    private val apiService: ApiService
) {

    suspend fun configureSchedule(request: ScheduleConfigureRequest): ApiResult<ScheduleResponse> {
        return try {
            val response = apiService.configureSchedule(request)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Configuration failed",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun getCurrentSchedule(
        businessId: Int,
        platform: String? = null
    ): ApiResult<ScheduleListResponse> {
        return try {
            val response = apiService.getCurrentSchedule(businessId, platform)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to load schedule",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun updateSchedule(
        scheduleId: Int,
        request: ScheduleUpdateRequest
    ): ApiResult<ScheduleResponse> {
        return try {
            val response = apiService.updateSchedule(scheduleId, request)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Update failed",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun getScheduleSuggestions(
        platform: String,
        timezone: String = "UTC"
    ): ApiResult<ScheduleSuggestionsResponse> {
        return try {
            val response = apiService.getScheduleSuggestions(platform, timezone)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to load suggestions",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }
}
