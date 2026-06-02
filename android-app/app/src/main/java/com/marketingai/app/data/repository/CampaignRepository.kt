package com.marketingai.app.data.repository

import com.marketingai.app.data.api.ApiService
import com.marketingai.app.data.models.CampaignCreateRequest
import com.marketingai.app.data.models.CampaignListResponse
import com.marketingai.app.data.models.CampaignResponse
import com.marketingai.app.data.models.DeleteResponse
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CampaignRepository @Inject constructor(
    private val apiService: ApiService
) {

    suspend fun createCampaign(request: CampaignCreateRequest): ApiResult<CampaignResponse> {
        return try {
            val response = apiService.createCampaign(request)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to create campaign",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun getCampaign(campaignId: Int): ApiResult<CampaignResponse> {
        return try {
            val response = apiService.getCampaign(campaignId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to load campaign",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun generateCreatives(campaignId: Int): ApiResult<CampaignResponse> {
        return try {
            val response = apiService.generateCreatives(campaignId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to generate creatives",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun listCampaigns(businessId: Int): ApiResult<CampaignListResponse> {
        return try {
            val response = apiService.listCampaigns(businessId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to list campaigns",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun deleteCampaign(campaignId: Int): ApiResult<DeleteResponse> {
        return try {
            val response = apiService.deleteCampaign(campaignId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to delete campaign",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }
}
