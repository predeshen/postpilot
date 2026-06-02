"""Content scheduling API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_scheduler_service
from app.database.models import PostingSchedule, Platform, ContentPillarType
from app.models.schemas import (
    ScheduleConfigureRequest,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleSuggestionsResponse,
    ScheduleUpdateRequest,
)
from app.services.content_scheduler import ContentSchedulerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("/configure", response_model=ScheduleResponse, status_code=201)
async def configure_schedule(
    request: ScheduleConfigureRequest,
    db: AsyncSession = Depends(get_db),
):
    """Configure a new posting schedule slot."""
    schedule = PostingSchedule(
        business_id=request.business_id,
        platform=Platform(request.platform),
        day_of_week=request.day_of_week,
        time_slot=request.time_slot,
        timezone=request.timezone,
        pillar_type=ContentPillarType(request.pillar_type) if request.pillar_type else None,
        series_name=request.series_name,
        is_active=True,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    logger.info(f"Created schedule: {request.platform} at {request.time_slot} on day {request.day_of_week}")
    return schedule


@router.get("/current", response_model=ScheduleListResponse)
async def get_current_schedule(
    business_id: int = Query(default=1),
    platform: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get current posting schedule for a business."""
    query = select(PostingSchedule).where(
        PostingSchedule.business_id == business_id
    )

    if platform:
        query = query.where(PostingSchedule.platform == Platform(platform))

    query = query.order_by(PostingSchedule.day_of_week, PostingSchedule.time_slot)
    result = await db.execute(query)
    schedules = result.scalars().all()

    return ScheduleListResponse(
        schedules=schedules,
        total=len(schedules),
    )


@router.put("/update/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing schedule slot."""
    result = await db.execute(
        select(PostingSchedule).where(PostingSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "pillar_type":
                setattr(schedule, field, ContentPillarType(value) if value else None)
            else:
                setattr(schedule, field, value)

    await db.commit()
    await db.refresh(schedule)

    logger.info(f"Updated schedule ID: {schedule_id}")
    return schedule


@router.get("/suggestions", response_model=ScheduleSuggestionsResponse)
async def get_schedule_suggestions(
    platform: str = Query(default="instagram", pattern="^(tiktok|instagram|facebook)$"),
    timezone: str = Query(default="UTC"),
    scheduler_service: ContentSchedulerService = Depends(get_scheduler_service),
):
    """Get optimal posting time suggestions for a platform."""
    best_times = {}
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day in range(7):
        times = scheduler_service.get_best_posting_times(platform, day, timezone)
        best_times[day_names[day]] = times

    series_suggestions = []
    for day in range(7):
        day_series = scheduler_service.get_content_series_for_day(day)
        for s in day_series:
            s["day_name"] = day_names[day]
            series_suggestions.append(s)

    upcoming_holidays = scheduler_service.get_upcoming_holidays()

    return ScheduleSuggestionsResponse(
        platform=platform,
        best_posting_times=best_times,
        content_series=series_suggestions,
        upcoming_holidays=upcoming_holidays,
    )
