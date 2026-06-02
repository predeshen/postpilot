package com.marketingai.app.data.repository

import com.marketingai.app.data.api.ApiService
import com.marketingai.app.data.local.CachedPost
import com.marketingai.app.data.local.PostDao
import com.marketingai.app.data.models.ContentApproveResponse
import com.marketingai.app.data.models.ContentCalendarResponse
import com.marketingai.app.data.models.ContentGenerateRequest
import com.marketingai.app.data.models.GeneratedPostResponse
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ContentRepository @Inject constructor(
    private val apiService: ApiService,
    private val postDao: PostDao
) {

    suspend fun generateContent(request: ContentGenerateRequest): ApiResult<List<GeneratedPostResponse>> {
        return try {
            val response = apiService.generateContent(request)
            if (response.isSuccessful) {
                response.body()?.let { posts ->
                    // Cache generated posts locally
                    cachePosts(posts, request.businessId)
                    ApiResult.Success(posts)
                } ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Generation failed",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun getContentCalendar(businessId: Int): ApiResult<ContentCalendarResponse> {
        return try {
            val response = apiService.getContentCalendar(businessId)
            if (response.isSuccessful) {
                response.body()?.let { calendar ->
                    // Cache posts locally for offline access
                    cachePosts(calendar.posts, businessId)
                    ApiResult.Success(calendar)
                } ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Failed to load calendar",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            // On network failure, try to serve from cache
            val cachedPosts = getCachedPosts(businessId)
            if (cachedPosts.isNotEmpty()) {
                val calendar = ContentCalendarResponse(
                    posts = cachedPosts,
                    total = cachedPosts.size,
                    upcoming = cachedPosts.count { it.status == "approved" || it.status == "draft" },
                    published = cachedPosts.count { it.status == "published" }
                )
                ApiResult.Success(calendar)
            } else {
                ApiResult.Error(message = e.message ?: "Network error")
            }
        }
    }

    suspend fun approveContent(postId: Int): ApiResult<ContentApproveResponse> {
        return try {
            val response = apiService.approveContent(postId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Approval failed",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun publishContent(postId: Int): ApiResult<ContentApproveResponse> {
        return try {
            val response = apiService.publishContent(postId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Publishing failed",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    suspend fun regenerateContent(postId: Int): ApiResult<GeneratedPostResponse> {
        return try {
            val response = apiService.regenerateContent(postId)
            if (response.isSuccessful) {
                response.body()?.let { ApiResult.Success(it) }
                    ?: ApiResult.Error("Empty response body")
            } else {
                ApiResult.Error(
                    message = response.errorBody()?.string() ?: "Regeneration failed",
                    code = response.code()
                )
            }
        } catch (e: Exception) {
            ApiResult.Error(message = e.message ?: "Network error")
        }
    }

    private suspend fun cachePosts(posts: List<GeneratedPostResponse>, businessId: Int) {
        try {
            val cachedPosts = posts.map { post ->
                CachedPost(
                    id = post.id,
                    businessId = post.businessId,
                    platform = post.platform,
                    content = post.content,
                    hashtags = post.hashtags.joinToString(","),
                    imagePath = post.imagePath,
                    status = post.status,
                    pillarType = post.pillarType,
                    engagementHook = post.engagementHook,
                    scheduledAt = post.scheduledAt,
                    publishedAt = post.publishedAt,
                    variantGroup = post.variantGroup,
                    language = post.language,
                    themeScore = post.themeScore,
                    createdAt = post.createdAt
                )
            }
            postDao.insertPosts(cachedPosts)
        } catch (_: Exception) {
            // Cache write failure is non-critical
        }
    }

    private suspend fun getCachedPosts(businessId: Int): List<GeneratedPostResponse> {
        return try {
            val flow = postDao.getPostsForBusiness(businessId)
            val cachedPosts = kotlinx.coroutines.flow.first(flow)
            cachedPosts.map { cached ->
                GeneratedPostResponse(
                    id = cached.id,
                    businessId = cached.businessId,
                    platform = cached.platform,
                    content = cached.content,
                    hashtags = cached.hashtags.split(",").filter { it.isNotEmpty() },
                    imagePath = cached.imagePath,
                    status = cached.status,
                    pillarType = cached.pillarType,
                    engagementHook = cached.engagementHook,
                    scheduledAt = cached.scheduledAt,
                    publishedAt = cached.publishedAt,
                    variantGroup = cached.variantGroup,
                    language = cached.language,
                    themeScore = cached.themeScore,
                    createdAt = cached.createdAt
                )
            }
        } catch (_: Exception) {
            emptyList()
        }
    }
}
