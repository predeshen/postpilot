package com.marketingai.app.di

import android.content.Context
import androidx.room.Room
import com.marketingai.app.data.api.ApiClient
import com.marketingai.app.data.api.ApiService
import com.marketingai.app.data.local.AppDatabase
import com.marketingai.app.data.local.BusinessDao
import com.marketingai.app.data.local.PostDao
import com.marketingai.app.data.local.ScheduleDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideApiService(): ApiService {
        return ApiClient.getApiService()
    }

    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "marketing_ai_db"
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    fun providePostDao(database: AppDatabase): PostDao {
        return database.postDao()
    }

    @Provides
    fun provideBusinessDao(database: AppDatabase): BusinessDao {
        return database.businessDao()
    }

    @Provides
    fun provideScheduleDao(database: AppDatabase): ScheduleDao {
        return database.scheduleDao()
    }
}
