# PostPilot

**AI-Powered Content That Converts**

PostPilot is an AI-powered social media content generator built for South African businesses. Create scroll-stopping posts for TikTok, Instagram, and Facebook - all tailored to your brand voice, industry, and target audience.

Designed for cost-effective, on-demand operation - content is generated only when you request it through the mobile app. No 24/7 server required. You only pay for actual AI calls.

## Key Features

- **AI Content Generation** - Creates platform-optimized posts using AWS Bedrock (Claude) with brand voice consistency
- **Multi-Platform Support** - Generates content tailored for TikTok, Instagram, and Facebook with platform-specific formatting
- **Brand Voice Engine** - Maintains consistent brand personality across all content (professional, casual, bold, inspirational, playful, luxurious)
- **Content Pillars System** - Balances content across educational, promotional, engagement, behind-the-scenes, and testimonial categories
- **Trending Hashtags** - Provides industry-relevant hashtag suggestions with trend scoring
- **Image Generation** - Creates platform-sized social media images with brand colors and text overlays using Pillow
- **Content Calendar** - Plans and schedules posts with optimal posting time suggestions
- **Analytics Dashboard** - Tracks performance metrics and theme consistency scores
- **Competitor Analysis** - Analyzes competitor hashtag strategies and content themes
- **On-Demand Architecture** - Scales to zero when idle, only incurs costs during active use

## Architecture Overview

```
+-------------------+         +-------------------------+         +------------------+
|                   |         |                         |         |                  |
|   PostPilot       |  HTTP   |   FastAPI Backend        |  API    |  AWS Bedrock     |
|   Android App     | ------> |   (AWS Lambda +         | ------> |  (Claude AI)     |
|   (Kotlin/        |         |    API Gateway)         |         |                  |
|    Compose)       |         |                         |         +------------------+
|                   |         |                         |
+-------------------+         |   - Content Generation  |
                              |   - Image Generation    |
                              |   - Scheduling          |
                              |   - Analytics           |
                              |   - Trending Hashtags   |
                              |                         |
                              |   SQLite (ephemeral)    |
                              +-------------------------+
```

The architecture is intentionally simple and cost-effective:

1. The **PostPilot Android app** is the primary interface. When the user opens the app, it sends requests to the backend.
2. The **FastAPI backend** runs on AWS Lambda with API Gateway. It only executes when requests arrive, so you pay nothing when idle.
3. **AWS Bedrock** handles AI content generation. You only pay per API call when content is actually generated.

There is no always-on server, no background workers, and no persistent infrastructure costs beyond storage.

## Technology Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| Python 3.11 | Runtime |
| FastAPI | Web framework |
| SQLAlchemy 2.0 (async) | ORM / database |
| aiosqlite | Async SQLite driver |
| boto3 | AWS Bedrock client |
| Pillow | Image generation |
| Pydantic Settings | Configuration management |
| uvicorn | ASGI server |
| Docker | Containerization |

### Android App
| Technology | Purpose |
|-----------|---------|
| Kotlin | Language |
| Jetpack Compose | UI framework |
| Material 3 | Design system |
| Hilt | Dependency injection |
| Retrofit + Moshi | HTTP client + JSON |
| Room | Local database |
| Navigation Compose | Screen navigation |
| Coil | Image loading |
| DataStore | Preferences storage |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| AWS Lambda | Backend hosting (scale-to-zero, on-demand) |
| API Gateway HTTP API | HTTP routing to Lambda |
| AWS Lambda Web Adapter | Runs FastAPI unchanged on Lambda |
| AWS Bedrock | AI content generation (Claude) |
| AWS SAM | Infrastructure as Code / deployment |
| Docker | Container packaging |

## Prerequisites

- **Python 3.11+** (backend development)
- **Docker** (required for Lambda container builds and local development)
- **Android Studio Hedgehog+** (Android app development)
- **AWS Account** with Bedrock access enabled in your region
- **AWS CLI** configured with valid credentials (`aws configure`)
- **SAM CLI** (for Lambda deployment - https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

## Quick Start

### Backend (Local Development)

```bash
cd backend/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (create .env file)
cat > .env << EOF
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./social_media.db
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
CORS_ORIGINS=*
EOF

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Android App (Local Development)

1. Open `android-app/` in Android Studio
2. Sync Gradle files
3. The app defaults to `http://10.0.2.2:8000` (Android emulator localhost)
4. Run the backend first, then launch the app on an emulator or device

To point the app at your deployed AWS Lambda backend, modify `BASE_URL` in `app/build.gradle.kts`:

```kotlin
buildConfigField("String", "BASE_URL", "\"https://{api-id}.execute-api.{region}.amazonaws.com\"")
```

## API Endpoint Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API info and links |
| `GET` | `/health` | Health check for load balancers |
| `POST` | `/api/business/setup` | Create a new business profile |
| `PUT` | `/api/business/update` | Update business profile |
| `POST` | `/api/business/logo` | Upload business logo |
| `GET` | `/api/business/{id}` | Get business profile by ID |
| `POST` | `/api/content/generate` | Generate AI content for a platform |
| `GET` | `/api/content/calendar` | Get content calendar with all posts |
| `POST` | `/api/content/approve/{id}` | Approve a draft post |
| `POST` | `/api/content/publish/{id}` | Publish an approved post |
| `POST` | `/api/content/regenerate/{id}` | Regenerate content for a post |
| `GET` | `/api/trends/hashtags` | Get trending hashtags by platform/industry |
| `GET` | `/api/trends/competitors` | Get competitor analysis |
| `GET` | `/api/analytics/performance` | Get performance metrics |
| `GET` | `/api/analytics/theme-score` | Get brand theme consistency score |
| `POST` | `/api/schedule/configure` | Create a posting schedule slot |
| `GET` | `/api/schedule/current` | Get current posting schedule |
| `PUT` | `/api/schedule/update/{id}` | Update a schedule slot |
| `GET` | `/api/schedule/suggestions` | Get optimal posting time suggestions |

## AWS Bedrock Configuration

### 1. Enable Bedrock Access

1. Sign in to the AWS Console
2. Navigate to **Amazon Bedrock**
3. Go to **Model access** in the left sidebar
4. Request access to **Anthropic Claude 3 Sonnet** (or your preferred Claude model)
5. Wait for access approval (usually immediate for Claude models)

### 2. Create IAM Credentials

Create an IAM user or role with the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.*"
    }
  ]
}
```

### 3. Configure Credentials

Set the following environment variables:

```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

For Lambda deployment, the SAM template automatically configures the IAM role with `bedrock:InvokeModel` permission. No additional credential management needed - the Lambda execution role handles authentication with Bedrock.

**Note:** If AWS credentials are not configured, the backend automatically falls back to mock content generation. This allows local development and testing without incurring AWS costs.

## AWS Lambda Deployment

### 1. Install Prerequisites

```bash
# Install AWS CLI (if not installed)
# See: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

# Install SAM CLI
# See: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# Configure AWS credentials
aws configure
```

### 2. Deploy with SAM

```bash
cd backend/

# First time: guided deployment (prompts for stack name, region, etc.)
./deploy-aws.sh --guided

# Subsequent deployments
./deploy-aws.sh
```

The guided deployment will ask for:
- Stack name (default: `social-media-generator`)
- AWS region (default: `us-east-1`)
- Confirmation before deploying

### 3. Get Your API URL

```bash
aws cloudformation describe-stacks \
  --stack-name social-media-generator \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
```

### 4. Verify Deployment

```bash
# Test the health endpoint
curl https://{api-id}.execute-api.{region}.amazonaws.com/health
```

### 5. Update the Android App

Update `BASE_URL` in `app/build.gradle.kts` with your API Gateway URL:

```kotlin
buildConfigField("String", "BASE_URL", "\"https://{api-id}.execute-api.us-east-1.amazonaws.com\"")
```

### 6. View Logs and Monitor

```bash
# Tail logs in real time
sam logs --stack-name social-media-generator --tail

# View CloudWatch metrics in AWS Console
# Lambda > Functions > social-media-generator > Monitor
```

### 7. Delete the Stack (if needed)

```bash
sam delete --stack-name social-media-generator
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `PostPilot` | Application display name |
| `APP_VERSION` | `1.0.0` | Application version |
| `DEBUG` | `false` | Enable debug mode and verbose logging |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |
| `DATABASE_URL` | `sqlite+aiosqlite:///./social_media.db` | Database connection string |
| `AWS_ACCESS_KEY_ID` | `None` | AWS access key for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | `None` | AWS secret key for Bedrock |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-sonnet-20240229-v1:0` | Bedrock model identifier |
| `SCHEDULER_ENABLED` | `true` | Enable scheduling features |
| `SCHEDULER_TIMEZONE` | `UTC` | Default scheduler timezone |
| `DEFAULT_LANGUAGE` | `en` | Default content language |
| `MAX_HASHTAGS_PER_POST` | `30` | Maximum hashtags per post |
| `CONTENT_CACHE_TTL` | `3600` | Hashtag cache TTL in seconds |
| `IMAGE_QUALITY` | `95` | PNG/JPEG output quality (1-100) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |

## Content Pillars System

The platform uses a content pillar framework to ensure balanced, strategic content across five categories:

| Pillar | Target Weight | Purpose |
|--------|--------------|---------|
| **Educational** | 25% | Tips, how-tos, industry insights - positions brand as authority |
| **Promotional** | 20% | Product/service highlights with natural CTAs |
| **Engagement** | 25% | Questions, polls, conversations - maximizes interaction |
| **Behind the Scenes** | 15% | Team stories, process reveals - builds trust and authenticity |
| **Testimonials** | 15% | Customer success stories - social proof |

The theme engine automatically tracks pillar distribution and recommends which type of content to create next based on what is underrepresented in your recent history.

### Content Series (Daily Themes)

| Day | Series Name | Pillar |
|-----|------------|--------|
| Monday | Monday Motivation | Engagement |
| Tuesday | Tip Tuesday | Educational |
| Wednesday | Wednesday Wisdom | Educational |
| Thursday | Throwback Thursday | Behind the Scenes |
| Friday | Feature Friday | Promotional |
| Saturday | Spotlight Saturday | Testimonials |
| Sunday | Sunday Funday | Engagement |

## Scheduling System (On-Demand Approach)

This project takes an on-demand approach to content scheduling rather than running persistent background workers:

1. **No background workers** - The server does not run 24/7 cron jobs or APScheduler tasks.
2. **Content generates on request** - When you open the app, it calls the API to generate fresh content.
3. **Optimal times are suggestions** - The scheduler service calculates best posting times per platform, but the user decides when to generate and post.
4. **EventBridge integration (optional)** - For automated posting, configure AWS EventBridge to invoke the Lambda function at desired intervals. This triggers generation only when needed.

This design means:
- The backend scales to zero between requests (Lambda shuts down automatically)
- You only pay for actual compute time and AI API calls
- No idle costs from running a persistent server
- The mobile app acts as the trigger for all operations

## Cost Optimization

This architecture is designed to minimize hosting costs. The backend only runs when the user opens the app and makes a request - there is no 24/7 server.

| Component | Cost Model | Idle Cost |
|-----------|-----------|-----------|
| **AWS Lambda** | Pay per request + compute time | $0 (scales to zero) |
| **API Gateway** | Pay per request | $0 (no requests = no cost) |
| **AWS Bedrock (Claude)** | Pay per input/output tokens | $0 (no calls when idle) |
| **SQLite** | Bundled with Lambda | $0 |
| **ECR (container storage)** | Storage only | ~$0.10/month |

**Estimated costs for a small business (~100 posts/month):**
- AWS Lambda: $0 (well within free tier: 1M requests/month + 400,000 GB-seconds free)
- API Gateway: $0 (free tier: 1M HTTP API calls/month)
- AWS Bedrock: ~$2-5/month (depends on content length and variants)
- **Total: ~$2-5/month** (potentially $0 if within Lambda/API Gateway free tier)

**Why this is so cheap:**
- Lambda free tier covers 1 million requests/month and 400,000 GB-seconds of compute
- For ~100 posts/month, you are using maybe 100-300 requests (generation + calendar + approvals)
- That is less than 0.03% of the free tier
- You only pay for the AI calls (Bedrock) since everything else fits in free tier

**Tips to reduce costs further:**
- Use `num_variants=1` instead of 2 to halve AI generation costs
- Cache trending hashtag results (configured via `CONTENT_CACHE_TTL`)
- The mock fallback generates content without calling Bedrock (useful for testing)

## Troubleshooting

### Backend won't start

```
ModuleNotFoundError: No module named 'app'
```
Make sure you are running `uvicorn` from the `backend/` directory.

### AWS Bedrock returns no content

- Verify your IAM user has `bedrock:InvokeModel` permissions
- Check that model access is enabled in the Bedrock console for your region
- The backend falls back to mock content if credentials are missing - check logs for "No Bedrock client available"

### Android app cannot connect to backend

- **Emulator:** The app uses `10.0.2.2:8000` which maps to host machine localhost
- **Physical device:** Update `BASE_URL` in `build.gradle.kts` to your machine's LAN IP
- **Production:** Update `BASE_URL` to your API Gateway URL (https://{api-id}.execute-api.{region}.amazonaws.com)
- Verify CORS is configured to allow your client origin

### Docker build fails

```bash
# Ensure you're in the backend/ directory
cd backend/
docker build -t social-media-generator .

# If Pillow fails, it likely needs system libraries (handled in the Dockerfile)
```

### Database errors

The app uses SQLite by default. The database file is created automatically on first run. If you encounter schema issues:

```bash
# Delete the database to start fresh
rm social_media.db

# Restart the server - tables are recreated on startup
uvicorn app.main:app --reload
```

### Content generation returns mock data

This is expected when AWS credentials are not configured. Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your `.env` file or environment to use real AI generation.

### Lambda cold starts are slow

Cold starts typically take 3-8 seconds for container-based Lambda functions. To reduce this:
- Use Lambda SnapStart (currently Java only, Python support coming)
- Use Provisioned Concurrency (costs ~$5-10/month but eliminates cold starts)
- Reduce container image size by removing unnecessary dependencies
- The current Dockerfile uses multi-stage builds to minimize image size
- Consider using Lambda ARM64 architecture (faster cold starts, lower cost)
