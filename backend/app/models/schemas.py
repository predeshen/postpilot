"""Pydantic request/response models for all API endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============== Business Schemas ==============

class BusinessSetupRequest(BaseModel):
    """Request model for business profile setup."""
    name: str = Field(..., min_length=1, max_length=255)
    industry: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    brand_voice: str = Field(default="professional", max_length=100)
    brand_colors: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    unique_selling_points: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=lambda: ["en"])
    website: Optional[str] = None
    logo_url: Optional[str] = Field(None, description="URL to your brand logo (alternative to file upload)")


class BusinessUpdateRequest(BaseModel):
    """Request model for updating business profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    brand_voice: Optional[str] = Field(None, max_length=100)
    brand_colors: Optional[List[str]] = None
    target_audience: Optional[str] = None
    unique_selling_points: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    website: Optional[str] = None
    logo_url: Optional[str] = Field(None, description="URL to your brand logo (alternative to file upload)")


class BusinessResponse(BaseModel):
    """Response model for business profile."""
    id: int
    name: str
    industry: str
    description: Optional[str] = None
    brand_voice: str
    brand_colors: List[str]
    logo_path: Optional[str] = None
    logo_url: Optional[str] = None
    target_audience: Optional[str] = None
    unique_selling_points: List[str]
    languages: List[str]
    website: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Content Schemas ==============

class ContentGenerateRequest(BaseModel):
    """Request model for content generation."""
    business_id: int
    platform: str = Field(..., pattern="^(tiktok|instagram|facebook)$")
    pillar_type: Optional[str] = None
    language: str = "en"
    num_variants: int = Field(default=2, ge=1, le=5)
    topic: Optional[str] = None
    include_hashtags: bool = True
    include_image: bool = False


class GeneratedPostResponse(BaseModel):
    """Response model for a generated post."""
    id: int
    business_id: int
    platform: str
    content: str
    hashtags: List[str]
    image_path: Optional[str] = None
    status: str
    pillar_type: Optional[str] = None
    engagement_hook: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    variant_group: Optional[str] = None
    language: str
    theme_score: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentCalendarResponse(BaseModel):
    """Response model for content calendar view."""
    posts: List[GeneratedPostResponse]
    total: int
    upcoming: int
    published: int


class ContentApproveResponse(BaseModel):
    """Response model for content approval."""
    id: int
    status: str
    message: str


# ============== Trends Schemas ==============

class TrendingHashtagResponse(BaseModel):
    """Response model for trending hashtags."""
    hashtag: str
    platform: str
    category: Optional[str] = None
    relevance_score: float
    trend_score: float
    usage_count: int


class TrendsResponse(BaseModel):
    """Response model for trends endpoint."""
    platform: str
    hashtags: List[TrendingHashtagResponse]
    updated_at: datetime


class TrendingTopicResponse(BaseModel):
    """Response model for a single trending topic."""
    title: str
    description: str
    relevance_score: float
    content_angles: List[str]


class TrendingTopicsResponse(BaseModel):
    """Response model for trending topics endpoint."""
    industry: str
    topics: List[TrendingTopicResponse]
    updated_at: datetime


class CompetitorAnalysisResponse(BaseModel):
    """Response model for competitor analysis."""
    competitor_name: str
    top_hashtags: List[str]
    posting_frequency: str
    engagement_rate: float
    content_themes: List[str]


# ============== Analytics Schemas ==============

class PerformanceMetrics(BaseModel):
    """Response model for performance analytics."""
    total_posts: int
    published_posts: int
    average_engagement_rate: float
    top_performing_platform: Optional[str] = None
    top_performing_pillar: Optional[str] = None
    posts_by_platform: dict
    posts_by_status: dict


class ThemeScoreResponse(BaseModel):
    """Response model for theme consistency scoring."""
    overall_score: float
    brand_voice_consistency: float
    visual_consistency: float
    content_pillar_balance: dict
    recommendations: List[str]


# ============== Schedule Schemas ==============

class ScheduleConfigureRequest(BaseModel):
    """Request model for schedule configuration."""
    business_id: int
    platform: str = Field(..., pattern="^(tiktok|instagram|facebook)$")
    day_of_week: int = Field(..., ge=0, le=6)
    time_slot: str = Field(..., pattern="^\\d{2}:\\d{2}$")
    timezone: str = "UTC"
    pillar_type: Optional[str] = None
    series_name: Optional[str] = None


class ScheduleUpdateRequest(BaseModel):
    """Request model for schedule update."""
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    time_slot: Optional[str] = Field(None, pattern="^\\d{2}:\\d{2}$")
    timezone: Optional[str] = None
    pillar_type: Optional[str] = None
    series_name: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    """Response model for schedule."""
    id: int
    business_id: int
    platform: str
    day_of_week: int
    time_slot: str
    timezone: str
    pillar_type: Optional[str] = None
    is_active: bool
    series_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleListResponse(BaseModel):
    """Response model for schedule list."""
    schedules: List[ScheduleResponse]
    total: int


class ContentSeriesSuggestionResponse(BaseModel):
    """Response model for a content series suggestion."""
    series_id: str
    name: str
    pillar: str
    description: str
    day_name: Optional[str] = None


class HolidayEventResponse(BaseModel):
    """Response model for an upcoming holiday/event."""
    date: str
    name: str
    days_until: int
    category: Optional[str] = None


class ScheduleSuggestionsResponse(BaseModel):
    """Response model for schedule suggestions."""
    platform: str
    best_posting_times: dict
    content_series: List[ContentSeriesSuggestionResponse]
    upcoming_holidays: List[HolidayEventResponse]


# ============== Common Schemas ==============

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    service: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    detail: str
    code: Optional[str] = None


# ============== Campaign Schemas ==============

class CampaignCreateRequest(BaseModel):
    """Request model for creating a Meta Ads campaign."""
    business_id: int
    campaign_name: str = Field(..., min_length=1, max_length=255)
    campaign_objective: str = Field(..., pattern="^(conversions|awareness|traffic|engagement|leads|app_installs)$")
    target_audience: Optional[str] = None
    product_service: str = Field(..., min_length=1)
    budget_range: Optional[str] = None


class CampaignCreativeResponse(BaseModel):
    """Response model for a single ad creative."""
    id: int
    angle_id: int
    creative_number: int
    headline: str
    primary_text: str
    description: Optional[str] = None
    call_to_action: str
    image_concept: Optional[str] = None
    image_base64: Optional[str] = None
    ad_format: str
    platform_placement: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignAngleResponse(BaseModel):
    """Response model for a campaign angle."""
    id: int
    campaign_id: int
    angle_number: int
    hook_type: str
    title: str
    description: Optional[str] = None
    target_emotion: Optional[str] = None
    creatives: List[CampaignCreativeResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignResponse(BaseModel):
    """Response model for a campaign."""
    id: int
    business_id: int
    name: str
    objective: str
    target_audience: Optional[str] = None
    product_service: Optional[str] = None
    budget_range: Optional[str] = None
    status: str
    angles: List[CampaignAngleResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignListResponse(BaseModel):
    """Response model for campaign list."""
    campaigns: List[CampaignResponse]
    total: int


# ============== Image Generation Schemas ==============

class ImageGenerateRequest(BaseModel):
    """Request model for on-demand image generation via Stability AI."""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt for image generation")
    width: int = Field(default=1080, ge=256, le=2048, description="Image width in pixels")
    height: int = Field(default=1080, ge=256, le=2048, description="Image height in pixels")
    model_id: Optional[str] = Field(
        default=None,
        description="Stability AI model ID. Options: sd3.5-large-turbo, sd3.5-large, sd3.5-medium"
    )


class ImageGenerateResponse(BaseModel):
    """Response model for image generation."""
    success: bool
    image_base64: Optional[str] = None
    width: int
    height: int
    model_id: str
    prompt: str
    file_path: Optional[str] = None


class PostImageGenerateResponse(BaseModel):
    """Response model for generating an image for a specific post."""
    post_id: int
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    platform: str
    success: bool
