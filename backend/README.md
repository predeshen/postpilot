# PostPilot Backend

FastAPI backend service for PostPilot - AI-powered social media content generation for South African businesses. Designed for on-demand, serverless deployment on AWS Lambda with API Gateway.

## Service Architecture

```
app/
├── main.py                    # FastAPI app entry point, lifespan, middleware
├── config.py                  # Pydantic Settings (env vars)
├── api/
│   ├── dependencies.py        # Dependency injection (DB session, services)
│   └── routes/
│       ├── business.py        # Business profile CRUD
│       ├── content.py         # Content generation and management
│       ├── trends.py          # Trending hashtags and competitor analysis
│       ├── analytics.py       # Performance metrics and theme scoring
│       └── schedule.py        # Posting schedule configuration
├── database/
│   ├── base.py                # SQLAlchemy async engine and session setup
│   └── models.py             # ORM models (BusinessProfile, GeneratedPost, etc.)
├── models/
│   └── schemas.py             # Pydantic request/response schemas
└── services/
    ├── ai_generator.py        # AWS Bedrock (Claude) content generation
    ├── content_scheduler.py   # On-demand scheduling and calendar planning
    ├── image_generator.py     # Pillow-based image template engine
    ├── theme_engine.py        # Brand voice consistency scoring
    └── trending_hashtags.py   # Hashtag trends and competitor data
```

### Service Descriptions

| Service | File | Responsibility |
|---------|------|---------------|
| **AI Generator** | `ai_generator.py` | Calls AWS Bedrock Claude to generate social media posts. Builds brand-aware prompts with platform guidelines. Falls back to mock generation when credentials are missing. |
| **Content Scheduler** | `content_scheduler.py` | Calculates optimal posting times per platform/day. Generates content calendar plans. Provides content series suggestions (Monday Motivation, Tip Tuesday, etc.). |
| **Image Generator** | `image_generator.py` | Creates platform-sized images (1080x1920, 1080x1080, 1200x630) with gradient backgrounds, text overlays, and brand watermarks using Pillow. |
| **Theme Engine** | `theme_engine.py` | Scores content for brand voice consistency. Tracks content pillar distribution. Detects content repetition. Suggests next pillar type for balanced output. |
| **Trending Hashtags** | `trending_hashtags.py` | Provides industry-specific trending hashtags with relevance scoring. Includes competitor analysis data. Uses in-memory caching with configurable TTL. |

## Database Schema

The application uses SQLAlchemy 2.0 with async support. Default database is SQLite (via aiosqlite), but PostgreSQL is supported for production.

### Tables

#### `business_profiles`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| name | String(255) | Business name |
| industry | String(100) | Industry category |
| description | Text | Business description |
| brand_voice | String(100) | Voice archetype (professional, casual, bold, etc.) |
| brand_colors | JSON | List of hex color codes |
| logo_path | String(500) | Path to uploaded logo file |
| target_audience | Text | Target audience description |
| unique_selling_points | JSON | List of USP strings |
| languages | JSON | Supported languages (default: ["en"]) |
| website | String(500) | Business website URL |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

#### `generated_posts`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| business_id | Integer (FK) | Reference to business_profiles |
| platform | Enum | tiktok, instagram, facebook |
| content | Text | Generated post text |
| hashtags | JSON | List of hashtag strings |
| image_path | String(500) | Path to generated image |
| status | Enum | draft, approved, published, rejected |
| pillar_type | Enum | educational, promotional, engagement, behind_the_scenes, testimonials |
| engagement_hook | Text | The hook/CTA text |
| scheduled_at | DateTime | Scheduled posting time |
| published_at | DateTime | Actual publish time |
| variant_group | String(100) | Groups variants from same generation |
| language | String(10) | Content language code |
| theme_score | Float | Brand consistency score (0.0-1.0) |
| created_at | DateTime | Creation timestamp |

#### `posting_schedules`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| business_id | Integer (FK) | Reference to business_profiles |
| platform | Enum | Target platform |
| day_of_week | Integer | 0=Monday through 6=Sunday |
| time_slot | String(5) | Posting time in HH:MM format |
| timezone | String(50) | Schedule timezone |
| pillar_type | Enum | Content pillar for this slot |
| is_active | Boolean | Whether schedule slot is active |
| series_name | String(200) | Content series name |

#### `post_history`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| post_id | Integer (FK) | Reference to generated_posts |
| platform | Enum | Platform where posted |
| published_at | DateTime | When published |
| likes | Integer | Like count |
| comments | Integer | Comment count |
| shares | Integer | Share count |
| impressions | Integer | Impression count |
| engagement_rate | Float | Calculated engagement rate |

#### `content_themes`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| business_id | Integer (FK) | Reference to business_profiles |
| name | String(200) | Theme name |
| description | Text | Theme description |
| tone | String(100) | Theme tone |
| keywords | JSON | Related keywords |
| color_palette | JSON | Theme-specific colors |
| is_active | Boolean | Whether theme is active |
| consistency_score | Float | Theme consistency score |

#### `content_pillars`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| business_id | Integer (FK) | Reference to business_profiles |
| pillar_type | Enum | Pillar category |
| weight | Float | Distribution weight (default 0.2) |
| description | Text | Pillar description |
| sample_topics | JSON | Example topics list |
| usage_count | Integer | Times this pillar was used |
| is_active | Boolean | Whether pillar is active |

#### `hashtag_cache`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| platform | Enum | Platform |
| hashtag | String(200) | Hashtag text |
| category | String(100) | Hashtag category |
| relevance_score | Float | Relevance score |
| trend_score | Float | Trend score |
| usage_count | Integer | Usage count |
| cached_at | DateTime | Cache timestamp |
| expires_at | DateTime | Cache expiration |

## API Details

### Business Profile

#### Create Business Profile

```bash
curl -X POST http://localhost:8000/api/business/setup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechStart Co",
    "industry": "technology",
    "description": "A SaaS platform helping small businesses automate marketing",
    "brand_voice": "professional",
    "brand_colors": ["#2980b9", "#2c3e50"],
    "target_audience": "Small business owners aged 25-45",
    "unique_selling_points": ["AI-powered", "Save 10 hours/week", "No design skills needed"],
    "languages": ["en"],
    "website": "https://techstart.example.com"
  }'
```

Response:
```json
{
  "id": 1,
  "name": "TechStart Co",
  "industry": "technology",
  "description": "A SaaS platform helping small businesses automate marketing",
  "brand_voice": "professional",
  "brand_colors": ["#2980b9", "#2c3e50"],
  "logo_path": null,
  "target_audience": "Small business owners aged 25-45",
  "unique_selling_points": ["AI-powered", "Save 10 hours/week", "No design skills needed"],
  "languages": ["en"],
  "website": "https://techstart.example.com",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Content Generation

#### Generate Content

```bash
curl -X POST http://localhost:8000/api/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": 1,
    "platform": "instagram",
    "pillar_type": "educational",
    "language": "en",
    "num_variants": 2,
    "topic": "productivity tips for entrepreneurs",
    "include_hashtags": true,
    "include_image": false
  }'
```

Response:
```json
[
  {
    "id": 1,
    "business_id": 1,
    "platform": "instagram",
    "content": "Did you know? Here's a game-changing technology tip...",
    "hashtags": ["#technology", "#techstartco", "#instagrammarketing", "#socialmedia"],
    "image_path": null,
    "status": "draft",
    "pillar_type": "educational",
    "engagement_hook": "Engaging educational hook for instagram",
    "scheduled_at": null,
    "published_at": null,
    "variant_group": "a1b2c3d4",
    "language": "en",
    "theme_score": 0.72,
    "created_at": "2024-01-15T10:35:00"
  }
]
```

#### Get Content Calendar

```bash
curl http://localhost:8000/api/content/calendar?business_id=1
```

Response:
```json
{
  "posts": [...],
  "total": 12,
  "upcoming": 8,
  "published": 4
}
```

#### Approve and Publish

```bash
# Approve a draft
curl -X POST http://localhost:8000/api/content/approve/1

# Publish an approved post
curl -X POST http://localhost:8000/api/content/publish/1
```

### Trending Hashtags

#### Get Trending Hashtags

```bash
curl "http://localhost:8000/api/trends/hashtags?platform=tiktok&industry=technology&limit=10"
```

Response:
```json
{
  "platform": "tiktok",
  "hashtags": [
    {
      "hashtag": "#ai",
      "platform": "tiktok",
      "category": "technology",
      "relevance_score": 0.95,
      "trend_score": 95.0,
      "usage_count": 95000
    },
    {
      "hashtag": "#techtok",
      "platform": "tiktok",
      "category": "technology",
      "relevance_score": 0.92,
      "trend_score": 92.0,
      "usage_count": 92000
    }
  ],
  "updated_at": "2024-01-15T10:40:00"
}
```

#### Get Competitor Analysis

```bash
curl "http://localhost:8000/api/trends/competitors?industry=technology"
```

Response:
```json
[
  {
    "competitor_name": "TechBrand Competitor",
    "top_hashtags": ["#innovation", "#techlife", "#startup", "#ai", "#futuretech"],
    "posting_frequency": "2x daily",
    "engagement_rate": 3.5,
    "content_themes": ["product demos", "industry news", "team culture"]
  }
]
```

### Analytics

#### Get Performance Metrics

```bash
curl "http://localhost:8000/api/analytics/performance?business_id=1"
```

Response:
```json
{
  "total_posts": 25,
  "published_posts": 12,
  "average_engagement_rate": 3.45,
  "top_performing_platform": "instagram",
  "top_performing_pillar": "engagement",
  "posts_by_platform": {"instagram": 12, "tiktok": 8, "facebook": 5},
  "posts_by_status": {"draft": 8, "approved": 5, "published": 12}
}
```

#### Get Theme Consistency Score

```bash
curl "http://localhost:8000/api/analytics/theme-score?business_id=1"
```

Response:
```json
{
  "overall_score": 0.78,
  "brand_voice_consistency": 0.82,
  "visual_consistency": 0.80,
  "content_pillar_balance": {
    "educational": {"target": 0.25, "actual": 0.30, "deviation": 0.05},
    "promotional": {"target": 0.20, "actual": 0.15, "deviation": 0.05}
  },
  "recommendations": ["Increase 'promotional' content (currently 15%, target 20%)"]
}
```

### Schedule

#### Configure Schedule

```bash
curl -X POST http://localhost:8000/api/schedule/configure \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": 1,
    "platform": "instagram",
    "day_of_week": 1,
    "time_slot": "11:00",
    "timezone": "America/New_York",
    "pillar_type": "educational",
    "series_name": "Tip Tuesday"
  }'
```

#### Get Posting Suggestions

```bash
curl "http://localhost:8000/api/schedule/suggestions?platform=instagram&timezone=UTC"
```

Response:
```json
{
  "platform": "instagram",
  "best_posting_times": {
    "Monday": ["06:00", "11:00", "17:00"],
    "Tuesday": ["06:00", "11:00", "17:00"],
    "Wednesday": ["06:00", "11:00", "17:00"]
  },
  "content_series": [
    {"name": "Monday Motivation", "description": "Inspirational content to start the week", "day_name": "Monday"}
  ],
  "upcoming_holidays": [
    {"date": "2024-02-14", "name": "Valentine's Day", "days_until": 5}
  ]
}
```

## Running Tests

```bash
cd backend/

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run a specific test file
python -m pytest tests/test_content.py -v
```

## Docker Usage

### Build and Run (Local Development)

```bash
cd backend/

# Build the image
docker build -t social-media-generator .

# Run the container
docker run -p 8000:8000 \
  -e DEBUG=true \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  social-media-generator
```

### Docker Compose (Development)

```bash
cd backend/

# Start all services
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f backend

# Stop
docker compose down
```

The Docker Compose configuration mounts `uploads/` and `generated_images/` as volumes for persistence. Production deployment uses AWS Lambda via SAM CLI (see deploy-aws.sh).

### Multi-Stage Build

The Dockerfile uses a multi-stage build:
1. **Builder stage** - Installs Python dependencies to a prefix directory
2. **Runtime stage** - Copies only the installed packages and application code, plus the AWS Lambda Web Adapter

This produces a smaller final image. The runtime stage also:
- Includes the AWS Lambda Web Adapter (`/opt/extensions/lambda-adapter`) for seamless Lambda integration
- Runs as non-root user (`appuser`) for local development
- Installs system libraries for Pillow (libpng, libjpeg, freetype, DejaVu fonts)
- Sets `PYTHONUNBUFFERED=1` for proper log output
- Includes a health check for local Docker usage

The same Dockerfile works for both local development (via docker-compose) and AWS Lambda deployment (via SAM).

## AWS Lambda Deployment

### Prerequisites

- AWS CLI configured (`aws configure`)
- SAM CLI installed
- Docker running (for building the container image)

### Deploy

```bash
cd backend/

# First deployment (interactive guided setup)
./deploy-aws.sh --guided

# Subsequent deployments
./deploy-aws.sh

# Deploy to staging
./deploy-aws.sh --config-env staging
```

### Architecture

The deployment uses:
- **AWS Lambda** (container image) - Runs the FastAPI app via AWS Lambda Web Adapter
- **API Gateway HTTP API** - Routes all HTTP requests to the Lambda function
- **IAM Role** - Grants the Lambda function `bedrock:InvokeModel` permission

Lambda configuration:
- Memory: 512 MB
- Timeout: 30 seconds
- Scales to zero when idle (no cost when unused)

### Get Your API URL

```bash
aws cloudformation describe-stacks \
  --stack-name social-media-generator \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
```

### View Logs

```bash
sam logs --stack-name social-media-generator --tail
```

### Delete the Stack

```bash
sam delete --stack-name social-media-generator
```

## Configuration Reference

All configuration is managed through environment variables (loaded from `.env` in development). See the `app/config.py` file which uses Pydantic Settings.

Key configuration groups:

**Application:** `APP_NAME`, `APP_VERSION`, `DEBUG`, `HOST`, `PORT`

**Database:** `DATABASE_URL` (SQLite or PostgreSQL connection string)

**AWS:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `BEDROCK_MODEL_ID`

**Content:** `DEFAULT_LANGUAGE`, `MAX_HASHTAGS_PER_POST`, `CONTENT_CACHE_TTL`

**Image:** `IMAGE_QUALITY` (1-100, controls PNG output quality)

**CORS:** `CORS_ORIGINS` (comma-separated list of allowed origins, `*` for development)
