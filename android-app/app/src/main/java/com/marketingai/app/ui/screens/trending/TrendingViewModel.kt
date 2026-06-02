package com.marketingai.app.ui.screens.trending

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketingai.app.data.models.CompetitorAnalysisResponse
import com.marketingai.app.data.models.TrendingHashtagResponse
import com.marketingai.app.data.repository.ApiResult
import com.marketingai.app.data.repository.TrendsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class TrendingUiState(
    val hashtags: List<TrendingHashtagResponse> = emptyList(),
    val competitors: List<CompetitorAnalysisResponse> = emptyList(),
    val selectedPlatform: String = "instagram",
    val selectedTab: TrendingTab = TrendingTab.HASHTAGS,
    val isLoading: Boolean = false,
    val error: String? = null,
    val lastUpdated: String? = null
)

enum class TrendingTab(val label: String) {
    HASHTAGS("Trending Hashtags"),
    COMPETITORS("Competitor Analysis")
}

@HiltViewModel
class TrendingViewModel @Inject constructor(
    private val trendsRepository: TrendsRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(TrendingUiState())
    val uiState: StateFlow<TrendingUiState> = _uiState.asStateFlow()

    init {
        loadTrends()
    }

    fun loadTrends() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            val platform = _uiState.value.selectedPlatform

            // Load hashtags
            when (val result = trendsRepository.getTrendingHashtags(platform)) {
                is ApiResult.Success -> {
                    _uiState.update {
                        it.copy(
                            hashtags = result.data.hashtags,
                            lastUpdated = result.data.updatedAt,
                            isLoading = false
                        )
                    }
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(isLoading = false, error = result.message)
                    }
                }
            }

            // Load competitors
            when (val result = trendsRepository.getCompetitorAnalysis()) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(competitors = result.data) }
                }
                is ApiResult.Error -> { /* Non-critical */ }
            }
        }
    }

    fun selectPlatform(platform: String) {
        _uiState.update { it.copy(selectedPlatform = platform) }
        loadTrends()
    }

    fun selectTab(tab: TrendingTab) {
        _uiState.update { it.copy(selectedTab = tab) }
    }
}
