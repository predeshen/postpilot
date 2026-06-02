package com.marketingai.app.ui.screens.campaigns

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketingai.app.data.models.CampaignCreateRequest
import com.marketingai.app.data.models.CampaignResponse
import com.marketingai.app.data.repository.ApiResult
import com.marketingai.app.data.repository.CampaignRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CampaignsUiState(
    val campaigns: List<CampaignResponse> = emptyList(),
    val totalCampaigns: Int = 0,
    val isLoading: Boolean = false,
    val isCreating: Boolean = false,
    val error: String? = null,
    val showCreateDialog: Boolean = false
)

data class CampaignDetailUiState(
    val campaign: CampaignResponse? = null,
    val isLoading: Boolean = false,
    val isGeneratingCreatives: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class CampaignViewModel @Inject constructor(
    private val campaignRepository: CampaignRepository
) : ViewModel() {

    private val _listState = MutableStateFlow(CampaignsUiState())
    val listState: StateFlow<CampaignsUiState> = _listState.asStateFlow()

    private val _detailState = MutableStateFlow(CampaignDetailUiState())
    val detailState: StateFlow<CampaignDetailUiState> = _detailState.asStateFlow()

    init {
        loadCampaigns()
    }

    fun loadCampaigns(businessId: Int = 1) {
        viewModelScope.launch {
            _listState.update { it.copy(isLoading = true, error = null) }

            when (val result = campaignRepository.listCampaigns(businessId)) {
                is ApiResult.Success -> {
                    _listState.update {
                        it.copy(
                            campaigns = result.data.campaigns,
                            totalCampaigns = result.data.total,
                            isLoading = false
                        )
                    }
                }
                is ApiResult.Error -> {
                    _listState.update {
                        it.copy(isLoading = false, error = result.message)
                    }
                }
            }
        }
    }

    fun createCampaign(
        businessId: Int = 1,
        campaignName: String,
        campaignObjective: String,
        targetAudience: String?,
        productService: String,
        budgetRange: String?
    ) {
        viewModelScope.launch {
            _listState.update { it.copy(isCreating = true, error = null) }

            val request = CampaignCreateRequest(
                businessId = businessId,
                campaignName = campaignName,
                campaignObjective = campaignObjective,
                targetAudience = targetAudience,
                productService = productService,
                budgetRange = budgetRange
            )

            when (val result = campaignRepository.createCampaign(request)) {
                is ApiResult.Success -> {
                    _listState.update {
                        it.copy(
                            isCreating = false,
                            showCreateDialog = false
                        )
                    }
                    loadCampaigns(businessId)
                }
                is ApiResult.Error -> {
                    _listState.update {
                        it.copy(isCreating = false, error = result.message)
                    }
                }
            }
        }
    }

    fun loadCampaignDetail(campaignId: Int) {
        viewModelScope.launch {
            _detailState.update { it.copy(isLoading = true, error = null) }

            when (val result = campaignRepository.getCampaign(campaignId)) {
                is ApiResult.Success -> {
                    _detailState.update {
                        it.copy(campaign = result.data, isLoading = false)
                    }
                }
                is ApiResult.Error -> {
                    _detailState.update {
                        it.copy(isLoading = false, error = result.message)
                    }
                }
            }
        }
    }

    fun generateCreatives(campaignId: Int) {
        viewModelScope.launch {
            _detailState.update { it.copy(isGeneratingCreatives = true, error = null) }

            when (val result = campaignRepository.generateCreatives(campaignId)) {
                is ApiResult.Success -> {
                    _detailState.update {
                        it.copy(
                            campaign = result.data,
                            isGeneratingCreatives = false
                        )
                    }
                }
                is ApiResult.Error -> {
                    _detailState.update {
                        it.copy(isGeneratingCreatives = false, error = result.message)
                    }
                }
            }
        }
    }

    fun deleteCampaign(campaignId: Int, businessId: Int = 1) {
        viewModelScope.launch {
            when (campaignRepository.deleteCampaign(campaignId)) {
                is ApiResult.Success -> {
                    loadCampaigns(businessId)
                }
                is ApiResult.Error -> {
                    _listState.update {
                        it.copy(error = "Failed to delete campaign")
                    }
                }
            }
        }
    }

    fun showCreateDialog() {
        _listState.update { it.copy(showCreateDialog = true) }
    }

    fun hideCreateDialog() {
        _listState.update { it.copy(showCreateDialog = false) }
    }

    fun clearError() {
        _listState.update { it.copy(error = null) }
        _detailState.update { it.copy(error = null) }
    }
}
