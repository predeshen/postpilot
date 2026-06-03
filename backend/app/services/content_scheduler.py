"""Content scheduler service - lightweight, on-demand content planning.

This scheduler is designed to work with serverless/scale-to-zero deployments
(like AWS Lambda). Instead of running 24/7 background workers, it:
- Calculates optimal posting times when the user opens the app
- Queues content generation requests on-demand
- Supports cron-triggered generation via AWS EventBridge scheduled rules
- Keeps costs minimal by only running when needed

For production, use AWS EventBridge Scheduler to trigger the /api/schedule/trigger
endpoint at desired intervals rather than running a persistent background worker.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from app.config import settings

logger = logging.getLogger(__name__)

# Best posting times by platform (based on general engagement data)
BEST_POSTING_TIMES = {
    "tiktok": {
        0: ["07:00", "12:00", "19:00"],  # Monday
        1: ["07:00", "12:00", "19:00"],  # Tuesday
        2: ["07:00", "12:00", "19:00"],  # Wednesday
        3: ["09:00", "12:00", "19:00"],  # Thursday
        4: ["09:00", "12:00", "17:00"],  # Friday
        5: ["10:00", "14:00", "19:00"],  # Saturday
        6: ["10:00", "14:00", "18:00"],  # Sunday
    },
    "instagram": {
        0: ["06:00", "11:00", "17:00"],
        1: ["06:00", "11:00", "17:00"],
        2: ["06:00", "11:00", "17:00"],
        3: ["06:00", "11:00", "17:00"],
        4: ["06:00", "11:00", "14:00"],
        5: ["09:00", "12:00", "17:00"],
        6: ["09:00", "12:00", "17:00"],
    },
    "facebook": {
        0: ["09:00", "13:00", "16:00"],
        1: ["09:00", "13:00", "16:00"],
        2: ["09:00", "13:00", "16:00"],
        3: ["09:00", "12:00", "15:00"],
        4: ["09:00", "11:00", "14:00"],
        5: ["10:00", "12:00"],
        6: ["10:00", "12:00"],
    },
}

# Content series templates
CONTENT_SERIES = {
    "monday_motivation": {
        "day": 0,
        "name": "Monday Motivation",
        "pillar": "engagement",
        "description": "Inspirational content to start the week",
    },
    "tip_tuesday": {
        "day": 1,
        "name": "Tip Tuesday",
        "pillar": "educational",
        "description": "Weekly tips and how-tos",
    },
    "wednesday_wisdom": {
        "day": 2,
        "name": "Wednesday Wisdom",
        "pillar": "educational",
        "description": "Industry insights and knowledge sharing",
    },
    "throwback_thursday": {
        "day": 3,
        "name": "Throwback Thursday",
        "pillar": "behind_the_scenes",
        "description": "Behind the scenes and brand story",
    },
    "feature_friday": {
        "day": 4,
        "name": "Feature Friday",
        "pillar": "promotional",
        "description": "Product/service highlights",
    },
    "spotlight_saturday": {
        "day": 5,
        "name": "Spotlight Saturday",
        "pillar": "testimonials",
        "description": "Customer stories and testimonials",
    },
    "sunday_funday": {
        "day": 6,
        "name": "Sunday Funday",
        "pillar": "engagement",
        "description": "Light, fun, interactive content",
    },
}

# Holiday/event calendar for auto-content suggestions
HOLIDAY_CALENDAR = {
    "01-01": "New Year's Day",
    "02-14": "Valentine's Day",
    "03-08": "International Women's Day",
    "04-22": "Earth Day",
    "05-01": "May Day",
    "06-21": "Summer Solstice",
    "07-04": "Independence Day (US)",
    "09-01": "Labor Day (approximate)",
    "10-31": "Halloween",
    "11-25": "Thanksgiving (approximate)",
    "12-25": "Christmas",
    "12-31": "New Year's Eve",
}


class ContentSchedulerService:
    """On-demand content scheduling and planning service.

    Designed for cost-effective serverless deployment. Content generation
    happens when triggered by user interaction or external cron (Cloud Scheduler).
    """

    def __init__(self):
        """Initialize the scheduler service."""
        self._timezone = ZoneInfo(settings.scheduler_timezone)

    def get_best_posting_times(
        self,
        platform: str,
        day_of_week: Optional[int] = None,
        timezone: str = "UTC",
    ) -> List[str]:
        """
        Get optimal posting times for a platform.

        Args:
            platform: Target platform
            day_of_week: Specific day (0=Monday), or None for today
            timezone: User's timezone

        Returns:
            List of optimal time strings (HH:MM format)
        """
        if day_of_week is None:
            tz = ZoneInfo(timezone)
            day_of_week = datetime.now(tz).weekday()

        platform_times = BEST_POSTING_TIMES.get(platform, BEST_POSTING_TIMES["instagram"])
        return platform_times.get(day_of_week, ["09:00", "12:00", "17:00"])

    def get_content_series_for_day(
        self,
        day_of_week: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get suggested content series for a specific day.

        Args:
            day_of_week: Day of week (0=Monday), or None for today

        Returns:
            List of content series suggestions
        """
        if day_of_week is None:
            day_of_week = datetime.now(timezone.utc).weekday()

        suggestions = []
        for series_id, series in CONTENT_SERIES.items():
            if series["day"] == day_of_week:
                suggestions.append({
                    "series_id": series_id,
                    "name": series["name"],
                    "pillar": series["pillar"],
                    "description": series["description"],
                })

        return suggestions

    def get_upcoming_holidays(self, days_ahead: int = 14) -> List[Dict]:
        """
        Get upcoming holidays/events for content planning.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming holidays/events
        """
        today = datetime.now(timezone.utc).date()
        upcoming = []

        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            date_key = check_date.strftime("%m-%d")

            if date_key in HOLIDAY_CALENDAR:
                upcoming.append({
                    "date": check_date.isoformat(),
                    "name": HOLIDAY_CALENDAR[date_key],
                    "days_until": i,
                })

        return upcoming

    def generate_content_calendar(
        self,
        business_id: int,
        platforms: List[str],
        days: int = 7,
        timezone: str = "UTC",
    ) -> List[Dict]:
        """
        Generate a content calendar plan for the upcoming week.

        This creates a plan of what to post and when - actual content
        generation happens on-demand when the user requests it.

        Args:
            business_id: Business profile ID
            platforms: List of target platforms
            days: Number of days to plan
            timezone: User's timezone

        Returns:
            List of planned content slots
        """
        calendar = []
        today = datetime.now(ZoneInfo(timezone))

        for day_offset in range(days):
            current_date = today + timedelta(days=day_offset)
            day_of_week = current_date.weekday()

            # Get series suggestion for this day
            series = self.get_content_series_for_day(day_of_week)

            for platform in platforms:
                best_times = self.get_best_posting_times(
                    platform, day_of_week, timezone
                )

                for i, time_slot in enumerate(best_times[:1]):  # One post per platform per day
                    pillar = series[0]["pillar"] if series else "engagement"
                    series_name = series[0]["name"] if series else None

                    calendar.append({
                        "business_id": business_id,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "time_slot": time_slot,
                        "platform": platform,
                        "day_of_week": day_of_week,
                        "pillar_type": pillar,
                        "series_name": series_name,
                        "status": "planned",
                    })

        return calendar

    def should_generate_content(
        self,
        last_generated_at: Optional[datetime],
        schedule_time: str,
        timezone: str = "UTC",
    ) -> bool:
        """
        Determine if content should be generated now based on schedule.

        Used by Cloud Scheduler trigger to decide if generation is needed.

        Args:
            last_generated_at: When content was last generated
            schedule_time: Scheduled time (HH:MM)
            timezone: Schedule timezone

        Returns:
            True if content generation should proceed
        """
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)

        # Parse schedule time
        hour, minute = map(int, schedule_time.split(":"))
        scheduled_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Check if we're within the generation window (30 minutes before scheduled time)
        window_start = scheduled_datetime - timedelta(minutes=30)

        if window_start <= now <= scheduled_datetime:
            if last_generated_at is None:
                return True
            # Don't regenerate if already done today
            if last_generated_at.date() < now.date():
                return True

        return False


# Singleton instance
content_scheduler_service = ContentSchedulerService()
