package com.marketingai.app.ui.screens.content

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
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

data class ContentPreviewUiState(
    val posts: List<GeneratedPostResponse> = emptyList(),
    val selectedVariantIndex: Int = 0,
    val isLoading: Boolean = false,
    val isRegenerating: Boolean = false,
    val error: String? = null,
    val actionMessage: String? = null
)

@HiltViewModel
class ContentPreviewViewModel @Inject constructor(
    private val contentRepository: ContentRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val postId: Int = savedStateHandle["postId"] ?: 0

    private val _uiState = MutableStateFlow(ContentPreviewUiState())
    val uiState: StateFlow<ContentPreviewUiState> = _uiState.asStateFlow()

    init {
        loadPost()
    }

    private fun loadPost() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            when (val result = contentRepository.getContentCalendar(1)) {
                is ApiResult.Success -> {
                    val allPosts = result.data.posts
                    // Find the post and its variants
                    val targetPost = allPosts.find { it.id == postId }
                    val variantGroup = targetPost?.variantGroup

                    val variants = if (variantGroup != null) {
                        allPosts.filter { it.variantGroup == variantGroup }
                    } else if (targetPost != null) {
                        listOf(targetPost)
                    } else {
                        emptyList()
                    }

                    _uiState.update {
                        it.copy(
                            posts = variants,
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

    fun selectVariant(index: Int) {
        _uiState.update { it.copy(selectedVariantIndex = index) }
    }

    fun approvePost() {
        val post = getCurrentPost() ?: return
        viewModelScope.launch {
            when (val result = contentRepository.approveContent(post.id)) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(actionMessage = "Post approved") }
                    loadPost()
                }
                is ApiResult.Error -> {
                    _uiState.update { it.copy(error = result.message) }
                }
            }
        }
    }

    fun publishPost() {
        val post = getCurrentPost() ?: return
        viewModelScope.launch {
            when (val result = contentRepository.publishContent(post.id)) {
                is ApiResult.Success -> {
                    _uiState.update { it.copy(actionMessage = "Post published") }
                    loadPost()
                }
                is ApiResult.Error -> {
                    _uiState.update { it.copy(error = result.message) }
                }
            }
        }
    }

    fun regeneratePost() {
        val post = getCurrentPost() ?: return
        viewModelScope.launch {
            _uiState.update { it.copy(isRegenerating = true) }
            when (val result = contentRepository.regenerateContent(post.id)) {
                is ApiResult.Success -> {
                    _uiState.update {
                        it.copy(isRegenerating = false, actionMessage = "Content regenerated")
                    }
                    loadPost()
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(isRegenerating = false, error = result.message)
                    }
                }
            }
        }
    }

    fun dismissMessage() {
        _uiState.update { it.copy(actionMessage = null, error = null) }
    }

    private fun getCurrentPost(): GeneratedPostResponse? {
        val state = _uiState.value
        return state.posts.getOrNull(state.selectedVariantIndex)
    }
}
