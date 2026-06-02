package com.marketingai.app.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.marketingai.app.ui.screens.analytics.AnalyticsScreen
import com.marketingai.app.ui.screens.campaigns.CampaignDetailScreen
import com.marketingai.app.ui.screens.campaigns.CampaignsScreen
import com.marketingai.app.ui.screens.content.ContentPreviewScreen
import com.marketingai.app.ui.screens.dashboard.DashboardScreen
import com.marketingai.app.ui.screens.onboarding.OnboardingScreen
import com.marketingai.app.ui.screens.schedule.ScheduleScreen
import com.marketingai.app.ui.screens.settings.SettingsScreen
import com.marketingai.app.ui.screens.trending.TrendingScreen

sealed class Screen(val route: String) {
    data object Onboarding : Screen("onboarding")
    data object Dashboard : Screen("dashboard")
    data object Schedule : Screen("schedule")
    data object ContentPreview : Screen("content_preview/{postId}") {
        fun createRoute(postId: Int) = "content_preview/$postId"
    }
    data object Trending : Screen("trending")
    data object Analytics : Screen("analytics")
    data object Settings : Screen("settings")
    data object Campaigns : Screen("campaigns")
    data object CampaignDetail : Screen("campaign_detail/{campaignId}") {
        fun createRoute(campaignId: Int) = "campaign_detail/$campaignId"
    }
}

@Composable
fun NavGraph(
    navController: NavHostController = rememberNavController(),
    startDestination: String = Screen.Onboarding.route
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Onboarding.route) {
            OnboardingScreen(
                onSetupComplete = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Onboarding.route) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Dashboard.route) {
            DashboardScreen(
                onNavigateToContent = { postId ->
                    navController.navigate(Screen.ContentPreview.createRoute(postId))
                },
                onNavigateToSchedule = {
                    navController.navigate(Screen.Schedule.route)
                },
                onNavigateToTrending = {
                    navController.navigate(Screen.Trending.route)
                },
                onNavigateToAnalytics = {
                    navController.navigate(Screen.Analytics.route)
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                onNavigateToCampaigns = {
                    navController.navigate(Screen.Campaigns.route)
                }
            )
        }

        composable(Screen.Schedule.route) {
            ScheduleScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(
            route = Screen.ContentPreview.route,
            arguments = listOf(navArgument("postId") { type = NavType.IntType })
        ) { backStackEntry ->
            val postId = backStackEntry.arguments?.getInt("postId") ?: 0
            ContentPreviewScreen(
                postId = postId,
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Trending.route) {
            TrendingScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Analytics.route) {
            AnalyticsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Campaigns.route) {
            CampaignsScreen(
                onNavigateBack = { navController.popBackStack() },
                onNavigateToCampaignDetail = { campaignId ->
                    navController.navigate(Screen.CampaignDetail.createRoute(campaignId))
                }
            )
        }

        composable(
            route = Screen.CampaignDetail.route,
            arguments = listOf(navArgument("campaignId") { type = NavType.IntType })
        ) { backStackEntry ->
            val campaignId = backStackEntry.arguments?.getInt("campaignId") ?: 0
            CampaignDetailScreen(
                campaignId = campaignId,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
