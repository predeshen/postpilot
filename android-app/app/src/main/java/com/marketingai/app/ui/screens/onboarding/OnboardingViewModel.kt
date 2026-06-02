package com.marketingai.app.ui.screens.onboarding

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketingai.app.data.models.BusinessSetupRequest
import com.marketingai.app.data.repository.ApiResult
import com.marketingai.app.data.repository.BusinessRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class OnboardingUiState(
    val currentStep: Int = 0,
    val totalSteps: Int = 5,
    val businessName: String = "",
    val industry: String = "",
    val description: String = "",
    val targetAudience: String = "",
    val brandVoice: String = "professional",
    val brandColors: List<String> = listOf("#6750A4", "#006B5E"),
    val selectedPlatforms: Set<String> = emptySet(),
    val uniqueSellingPoints: List<String> = emptyList(),
    val website: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
    val isSetupComplete: Boolean = false
)

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val businessRepository: BusinessRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(OnboardingUiState())
    val uiState: StateFlow<OnboardingUiState> = _uiState.asStateFlow()

    fun updateBusinessName(name: String) {
        _uiState.update { it.copy(businessName = name) }
    }

    fun updateIndustry(industry: String) {
        _uiState.update { it.copy(industry = industry) }
    }

    fun updateDescription(description: String) {
        _uiState.update { it.copy(description = description) }
    }

    fun updateTargetAudience(audience: String) {
        _uiState.update { it.copy(targetAudience = audience) }
    }

    fun updateBrandVoice(voice: String) {
        _uiState.update { it.copy(brandVoice = voice) }
    }

    fun addBrandColor(color: String) {
        _uiState.update { it.copy(brandColors = it.brandColors + color) }
    }

    fun removeBrandColor(color: String) {
        _uiState.update { it.copy(brandColors = it.brandColors - color) }
    }

    fun togglePlatform(platform: String) {
        _uiState.update { state ->
            val updated = if (platform in state.selectedPlatforms) {
                state.selectedPlatforms - platform
            } else {
                state.selectedPlatforms + platform
            }
            state.copy(selectedPlatforms = updated)
        }
    }

    fun addSellingPoint(point: String) {
        if (point.isNotBlank()) {
            _uiState.update { it.copy(uniqueSellingPoints = it.uniqueSellingPoints + point) }
        }
    }

    fun removeSellingPoint(point: String) {
        _uiState.update { it.copy(uniqueSellingPoints = it.uniqueSellingPoints - point) }
    }

    fun updateWebsite(website: String) {
        _uiState.update { it.copy(website = website) }
    }

    fun nextStep() {
        _uiState.update { state ->
            if (state.currentStep < state.totalSteps - 1) {
                state.copy(currentStep = state.currentStep + 1, error = null)
            } else {
                state
            }
        }
    }

    fun previousStep() {
        _uiState.update { state ->
            if (state.currentStep > 0) {
                state.copy(currentStep = state.currentStep - 1, error = null)
            } else {
                state
            }
        }
    }

    fun submitSetup() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            val state = _uiState.value
            val request = BusinessSetupRequest(
                name = state.businessName,
                industry = state.industry,
                description = state.description.ifBlank { null },
                brandVoice = state.brandVoice,
                brandColors = state.brandColors,
                targetAudience = state.targetAudience.ifBlank { null },
                uniqueSellingPoints = state.uniqueSellingPoints,
                website = state.website.ifBlank { null }
            )

            when (val result = businessRepository.setupBusiness(request)) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(isLoading = false, isSetupComplete = true) }
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(isLoading = false, error = result.message)
                    }
                }
            }
        }
    }

    fun dismissError() {
        _uiState.update { it.copy(error = null) }
    }

    fun canProceed(): Boolean {
        val state = _uiState.value
        return when (state.currentStep) {
            0 -> state.businessName.isNotBlank() && state.industry.isNotBlank()
            1 -> state.targetAudience.isNotBlank()
            2 -> state.brandVoice.isNotBlank()
            3 -> state.brandColors.isNotEmpty()
            4 -> state.selectedPlatforms.isNotEmpty()
            else -> true
        }
    }
}
