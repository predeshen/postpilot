package com.marketingai.app.ui.screens.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketingai.app.data.models.ContentCalendarResponse
import com.marketingai.app.data.models.GeneratedPostResponse
import com.marketingai.app.data.repository.ApiResult
import com.marketingai.app.data.repository.ContentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(
    val posts: List<GeneratedPostResponse> = emptyList(),
    val totalPosts: Int = 0,
    val upcomingPosts: Int = 0,
    val publishedPosts: Int = 0,
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val actionError: String? = null,
    val selectedFilter: PostFilter = PostFilter.ALL,
    val pillarDistribution: Map<String, Int> = emptyMap()
)

enum class PostFilter(val label: String) {
    ALL("All"),
    DRAFT("Drafts"),
    APPROVED("Approved"),
    PUBLISHED("Published")
}

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val contentRepository: ContentRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadCalendar()
    }

    fun loadCalendar() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            when (val result = contentRepository.getContentCalendar(1)) {
                is ApiResult.Success -> {
                    val data = result.data
                    val pillarDist = data.posts
                        .groupBy { it.pillarType ?: "other" }
                        .mapValues { it.value.size }

                    _uiState.update {
                        it.copy(
                            posts = data.posts,
                            totalPosts = data.total,
                            upcomingPosts = data.upcoming,
                            publishedPosts = data.published,
                            pillarDistribution = pillarDist,
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
        }
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(isRefreshing = true) }
            loadCalendar()
            _uiState.update { it.copy(isRefreshing = false) }
        }
    }

    fun setFilter(filter: PostFilter) {
        _uiState.update { it.copy(selectedFilter = filter) }
    }

    fun approvePost(postId: Int) {
        viewModelScope.launch {
            when (val result = contentRepository.approveContent(postId)) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(actionError = null) }
                    loadCalendar()
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(actionError = result.message)
                    }
                }
            }
        }
    }

    fun regeneratePost(postId: Int) {
        viewModelScope.launch {
            when (val result = contentRepository.regenerateContent(postId)) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(actionError = null) }
                    loadCalendar()
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(actionError = result.message)
                    }
                }
            }
        }
    }

    fun clearActionError() {
        _uiState.update { it.copy(actionError = null) }
    }

    val filteredPosts: List<GeneratedPostResponse>
        get() {
            val state = _uiState.value
            return when (state.selectedFilter) {
                PostFilter.ALL -> state.posts
                PostFilter.DRAFT -> state.posts.filter { it.status == "draft" }
                PostFilter.APPROVED -> state.posts.filter { it.status == "approved" }
                PostFilter.PUBLISHED -> state.posts.filter { it.status == "published" }
            }
        }
}
