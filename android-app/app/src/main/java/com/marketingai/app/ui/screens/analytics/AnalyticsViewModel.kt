package com.marketingai.app.ui.screens.analytics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketingai.app.data.models.PerformanceMetrics
import com.marketingai.app.data.models.ThemeScoreResponse
import com.marketingai.app.data.repository.AnalyticsRepository
import com.marketingai.app.data.repository.ApiResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AnalyticsUiState(
    val performanceMetrics: PerformanceMetrics? = null,
    val themeScore: ThemeScoreResponse? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AnalyticsViewModel @Inject constructor(
    private val analyticsRepository: AnalyticsRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AnalyticsUiState())
    val uiState: StateFlow<AnalyticsUiState> = _uiState.asStateFlow()

    init {
        loadAnalytics()
    }

    fun loadAnalytics() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            // Load performance metrics
            when (val result = analyticsRepository.getPerformanceMetrics(1)) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(performanceMetrics = result.data) }
                }
                is ApiResult.Error -> {
                    _uiState.update { it.copy(error = result.message) }
                }
            }

            // Load theme score
            when (val result = analyticsRepository.getThemeScore(1)) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(themeScore = result.data) }
                }
                is ApiResult.Error -> { /* Non-critical */ }
            }

            _uiState.update { it.copy(isLoading = false) }
        }
    }

    fun refresh() {
        loadAnalytics()
    }
}
