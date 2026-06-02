package com.marketingai.app.ui.screens.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketingai.app.data.api.ApiClient
import com.marketingai.app.data.models.BusinessResponse
import com.marketingai.app.data.models.BusinessUpdateRequest
import com.marketingai.app.data.repository.ApiResult
import com.marketingai.app.data.repository.BusinessRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val backendUrl: String = ApiClient.getBaseUrl(),
    val business: BusinessResponse? = null,
    val notificationsEnabled: Boolean = true,
    val darkModeEnabled: Boolean = false,
    val brandVoice: String = "professional",
    val isLoading: Boolean = false,
    val isSaving: Boolean = false,
    val error: String? = null,
    val successMessage: String? = null,
    val isConnected: Boolean = false
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val businessRepository: BusinessRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadSettings()
    }

    private fun loadSettings() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }

            when (val result = businessRepository.getBusiness(1)) {
                is ApiResult.Success -> {
                    _uiState.update {
                        it.copy(
                            business = result.data,
                            brandVoice = result.data.brandVoice,
                            isLoading = false,
                            isConnected = true
                        )
                    }
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(isLoading = false, isConnected = false)
                    }
                }
            }
        }
    }

    fun updateBackendUrl(url: String) {
        _uiState.update { it.copy(backendUrl = url) }
    }

    fun saveBackendUrl() {
        val url = _uiState.value.backendUrl
        ApiClient.updateBaseUrl(url)
        _uiState.update { it.copy(successMessage = "Backend URL updated") }
        loadSettings()
    }

    fun testConnection() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            when (businessRepository.getBusiness(1)) {
                is ApiResult.Success -> {
                    _uiState.update {
                        it.copy(isLoading = false, isConnected = true, successMessage = "Connected successfully")
                    }
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(isLoading = false, isConnected = false, error = "Connection failed")
                    }
                }
            }
        }
    }

    fun toggleNotifications(enabled: Boolean) {
        _uiState.update { it.copy(notificationsEnabled = enabled) }
    }

    fun toggleDarkMode(enabled: Boolean) {
        _uiState.update { it.copy(darkModeEnabled = enabled) }
    }

    fun updateBrandVoice(voice: String) {
        _uiState.update { it.copy(brandVoice = voice) }
    }

    fun saveBrandVoice() {
        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true) }

            val request = BusinessUpdateRequest(brandVoice = _uiState.value.brandVoice)
            when (businessRepository.updateBusiness(1, request)) {
                is ApiResult.Success -> {
                    _uiState.update {
                        it.copy(isSaving = false, successMessage = "Brand voice updated")
                    }
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(isSaving = false, error = "Failed to update brand voice")
                    }
                }
            }
        }
    }

    fun dismissMessage() {
        _uiState.update { it.copy(successMessage = null, error = null) }
    }
}
