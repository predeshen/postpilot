"""SQLAlchemy database models."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class PostStatus(str, enum.Enum):
    """Status of a generated post."""
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class Platform(str, enum.Enum):
    """Social media platforms."""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


class ContentPillarType(str, enum.Enum):
    """Types of content pillars."""
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"
    ENGAGEMENT = "engagement"
    BEHIND_THE_SCENES = "behind_the_scenes"
    TESTIMONIALS = "testimonials"


class CampaignStatus(str, enum.Enum):
    """Status of a meta ads campaign."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class HookType(str, enum.Enum):
    """Types of advertising angle hooks."""
    PAIN_POINT = "pain_point"
    ASPIRATIONAL = "aspirational"
    SOCIAL_PROOF = "social_proof"
    CURIOSITY = "curiosity"
    URGENCY = "urgency"
    CONTRARIAN = "contrarian"


class CreativeStatus(str, enum.Enum):
    """Status of an ad creative."""
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class AdFormat(str, enum.Enum):
    """Meta ad formats."""
    SINGLE_IMAGE = "single_image"
    CAROUSEL = "carousel"
    VIDEO = "video"
    COLLECTION = "collection"


class PlatformPlacement(str, enum.Enum):
    """Meta ad platform placements."""
    FEED = "feed"
    STORIES = "stories"
    REELS = "reels"
    AUDIENCE_NETWORK = "audience_network"


class BusinessProfile(Base):
    """Business profile with brand information."""

    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    brand_voice = Column(String(100), default="professional")
    brand_colors = Column(JSON, default=list)
    logo_path = Column(String(500), nullable=True)
    logo_url = Column(String(1000), nullable=True)
    target_audience = Column(Text, nullable=True)
    unique_selling_points = Column(JSON, default=list)
    languages = Column(JSON, default=lambda: ["en"])
    website = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("GeneratedPost", back_populates="business", cascade="all, delete-orphan")
    themes = relationship("ContentTheme", back_populates="business", cascade="all, delete-orphan")
    schedules = relationship("PostingSchedule", back_populates="business", cascade="all, delete-orphan")
    pillars = relationship("ContentPillar", back_populates="business", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="business", cascade="all, delete-orphan")


class GeneratedPost(Base):
    """Generated social media post."""

    __tablename__ = "generated_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    content = Column(Text, nullable=False)
    hashtags = Column(JSON, default=list)
    image_path = Column(String(500), nullable=True)
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    pillar_type = Column(Enum(ContentPillarType), nullable=True)
    engagement_hook = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    variant_group = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    theme_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="posts")


class HashtagCache(Base):
    """Cache for trending hashtags."""

    __tablename__ = "hashtag_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(Enum(Platform), nullable=False)
    hashtag = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True)
    relevance_score = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class ContentTheme(Base):
    """Brand content theme configuration."""

    __tablename__ = "content_themes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tone = Column(String(100), nullable=True)
    keywords = Column(JSON, default=list)
    color_palette = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    consistency_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="themes")


class PostingSchedule(Base):
    """Content posting schedule."""

    __tablename__ = "posting_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    time_slot = Column(String(5), nullable=False)  # HH:MM format
    timezone = Column(String(50), default="UTC")
    pillar_type = Column(Enum(ContentPillarType), nullable=True)
    is_active = Column(Boolean, default=True)
    series_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="schedules")


class PostHistory(Base):
    """Post publishing history for analytics."""

    __tablename__ = "post_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("generated_posts.id"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    published_at = Column(DateTime, nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class ContentPillar(Base):
    """Content pillar configuration for business."""

    __tablename__ = "content_pillars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False)
    pillar_type = Column(Enum(ContentPillarType), nullable=False)
    weight = Column(Float, default=0.2)  # Distribution weight
    description = Column(Text, nullable=True)
    sample_topics = Column(JSON, default=list)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="pillars")


class Campaign(Base):
    """Meta Ads campaign."""

    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False)
    name = Column(String(255), nullable=False)
    objective = Column(String(100), nullable=False)
    target_audience = Column(Text, nullable=True)
    product_service = Column(Text, nullable=True)
    budget_range = Column(String(100), nullable=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="campaigns")
    angles = relationship("CampaignAngle", back_populates="campaign", cascade="all, delete-orphan")


class CampaignAngle(Base):
    """Advertising angle for a campaign."""

    __tablename__ = "campaign_angles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    angle_number = Column(Integer, nullable=False)
    hook_type = Column(Enum(HookType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_emotion = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="angles")
    creatives = relationship("CampaignCreative", back_populates="angle", cascade="all, delete-orphan")


class CampaignCreative(Base):
    """Ad creative for a campaign angle."""

    __tablename__ = "campaign_creatives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    angle_id = Column(Integer, ForeignKey("campaign_angles.id"), nullable=False)
    creative_number = Column(Integer, nullable=False)
    headline = Column(String(255), nullable=False)
    primary_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    call_to_action = Column(String(50), nullable=False)
    image_concept = Column(Text, nullable=True)
    image_base64 = Column(Text, nullable=True)
    ad_format = Column(Enum(AdFormat), nullable=False)
    platform_placement = Column(Enum(PlatformPlacement), nullable=False)
    status = Column(Enum(CreativeStatus), default=CreativeStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)

    angle = relationship("CampaignAngle", back_populates="creatives")
