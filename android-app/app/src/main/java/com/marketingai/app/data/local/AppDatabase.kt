package com.marketingai.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverter
import androidx.room.TypeConverters
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

// Entities

@Entity(tableName = "cached_posts")
data class CachedPost(
    @PrimaryKey val id: Int,
    val businessId: Int,
    val platform: String,
    val content: String,
    val hashtags: String, // JSON array stored as string
    val imagePath: String? = null,
    val status: String,
    val pillarType: String? = null,
    val engagementHook: String? = null,
    val scheduledAt: String? = null,
    val publishedAt: String? = null,
    val variantGroup: String? = null,
    val language: String,
    val themeScore: Float? = null,
    val createdAt: String,
    val cachedAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "cached_business")
data class CachedBusiness(
    @PrimaryKey val id: Int,
    val name: String,
    val industry: String,
    val description: String? = null,
    val brandVoice: String,
    val brandColors: String, // JSON array stored as string
    val logoPath: String? = null,
    val targetAudience: String? = null,
    val uniqueSellingPoints: String, // JSON array stored as string
    val languages: String, // JSON array stored as string
    val website: String? = null,
    val cachedAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "cached_schedules")
data class CachedSchedule(
    @PrimaryKey val id: Int,
    val businessId: Int,
    val platform: String,
    val dayOfWeek: Int,
    val timeSlot: String,
    val timezone: String,
    val pillarType: String? = null,
    val isActive: Boolean,
    val seriesName: String? = null,
    val cachedAt: Long = System.currentTimeMillis()
)

// DAOs

@Dao
interface PostDao {
    @Query("SELECT * FROM cached_posts WHERE businessId = :businessId ORDER BY createdAt DESC")
    fun getPostsForBusiness(businessId: Int): Flow<List<CachedPost>>

    @Query("SELECT * FROM cached_posts WHERE id = :postId")
    suspend fun getPostById(postId: Int): CachedPost?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPosts(posts: List<CachedPost>)

    @Query("DELETE FROM cached_posts WHERE businessId = :businessId")
    suspend fun clearPostsForBusiness(businessId: Int)

    @Query("DELETE FROM cached_posts WHERE cachedAt < :timestamp")
    suspend fun clearStaleCache(timestamp: Long)
}

@Dao
interface BusinessDao {
    @Query("SELECT * FROM cached_business WHERE id = :businessId")
    suspend fun getBusiness(businessId: Int): CachedBusiness?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBusiness(business: CachedBusiness)

    @Query("DELETE FROM cached_business")
    suspend fun clearAll()
}

@Dao
interface ScheduleDao {
    @Query("SELECT * FROM cached_schedules WHERE businessId = :businessId")
    fun getSchedulesForBusiness(businessId: Int): Flow<List<CachedSchedule>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSchedules(schedules: List<CachedSchedule>)

    @Query("DELETE FROM cached_schedules WHERE businessId = :businessId")
    suspend fun clearSchedulesForBusiness(businessId: Int)
}

// Database

@Database(
    entities = [CachedPost::class, CachedBusiness::class, CachedSchedule::class],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun postDao(): PostDao
    abstract fun businessDao(): BusinessDao
    abstract fun scheduleDao(): ScheduleDao
}
