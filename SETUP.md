# PostPilot - Setup Guide

## Prerequisites
- Python 3.9+
- AWS Account (for Claude text generation via Bedrock)
- Stability AI account (for image generation)
- Android Studio (for the mobile app)

## Step 1: Get a Stability AI API Key (Image Generation)
1. Go to https://platform.stability.ai/account/keys
2. Create an account or sign in
3. Generate an API key
4. Copy the key (starts with `sk-`)

That is it for image generation. No cloud deployment, no endpoints to manage, no hourly costs.

## Step 2: Enable AWS Bedrock Model Access (Claude - Text Generation)
1. Sign in to AWS Console: https://console.aws.amazon.com
2. Go to Amazon Bedrock service (search "Bedrock" in the search bar)
3. Make sure you are in the **eu-central-1** region (Europe - Frankfurt)
4. In the left sidebar, click "Model access"
5. Click "Manage model access" button
6. Check the box for:
   - **Anthropic > Claude 3.5 Sonnet v2** (for text/content generation)
7. Click "Request model access"
8. Wait for approval (usually instant for Claude)

## Step 3: Create AWS Access Keys
1. Go to IAM in AWS Console: https://console.aws.amazon.com/iam
2. Click "Users" > "Create user"
3. Name it "postpilot-dev"
4. Click "Next" > "Attach policies directly"
5. Click "Create policy" and use this JSON:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["bedrock:InvokeModel"],
         "Resource": "*"
       }
     ]
   }
   ```
6. Name the policy "PostPilotAccess" and create it
7. Go back to the user creation, attach "PostPilotAccess"
8. Create the user
9. Go to the user > "Security credentials" tab > "Create access key"
10. Choose "Application running outside AWS"
11. Copy the Access Key ID and Secret Access Key (save them!)

## Step 4: Configure and Run the Backend
1. Clone the repo:
   ```bash
   git clone https://github.com/predeshen/postpilot.git
   cd postpilot/backend
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend/` folder:
   ```
   # AWS Bedrock (Claude - text generation)
   AWS_ACCESS_KEY_ID=AKIA...your_key...
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_REGION=eu-central-1
   BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

   # Stability AI (image generation)
   STABILITY_API_KEY=sk-your-stability-key-here
   STABILITY_MODEL=sd3.5-large-turbo

   DEBUG=true
   ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Test it: Open http://localhost:8000/docs in your browser
7. Try the health check: http://localhost:8000/health

Done! No cloud deployment needed. Everything runs from your PC.

## Step 5: Test Connectivity
Once the backend is running, test service connectivity:

```bash
# Test Claude (text generation via AWS Bedrock)
curl http://localhost:8000/api/diagnostics/test-claude

# Test Stability AI (image generation)
curl http://localhost:8000/api/diagnostics/test-stability

# Test everything at once
curl http://localhost:8000/api/diagnostics/test-aws
```

## Step 6: Set Up the Android App
1. Download and install Android Studio: https://developer.android.com/studio
2. Open Android Studio > File > Open > select the `android-app/` folder
3. Wait for Gradle sync to complete (may take a few minutes first time)
4. Connect your phone via USB with Developer Mode enabled, OR use the emulator
5. In `app/build.gradle.kts`, the BASE_URL is set to:
   - For emulator: `http://10.0.2.2:8000` (this maps to your PC's localhost)
   - For physical device on same WiFi: change to `http://YOUR_PC_IP:8000`
6. Click the green "Run" button in Android Studio
7. The app will install on your device/emulator

## Step 7: Build the APK (for sharing/installing)
1. In Android Studio: Build > Build Bundle(s) / APK(s) > Build APK(s)
2. The APK will be at: `android-app/app/build/outputs/apk/debug/app-debug.apk`
3. Transfer this APK to any Android phone to install

## Architecture

PostPilot uses two AI services:

| Feature | Service | Model | How |
|---------|---------|-------|-----|
| Text/Content Generation | AWS Bedrock | Claude 3.5 Sonnet v2 | API call (pay per use) |
| Image Generation | Stability AI | SD 3.5 Large Turbo | API call (pay per use) |

Both are simple API calls. No servers to manage, no endpoints to deploy, no hourly costs.

### Stability AI Request Format
```
POST https://api.stability.ai/v2beta/stable-image/generate/sd3
Content-Type: multipart/form-data
Authorization: Bearer sk-...

prompt=A professional social media visual
model=sd3.5-large-turbo
aspect_ratio=1:1
output_format=png
```

### Stability AI Response
Returns raw image bytes directly (Content-Type: image/png).

### Supported Aspect Ratios
- `1:1` - Instagram Feed
- `9:16` - TikTok, Instagram/Facebook Stories
- `16:9` - Facebook Feed
- `4:5`, `5:4`, `3:2`, `2:3` - Additional options

## API Endpoints for Image Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/images/generate` | Generate an image from a custom prompt |
| POST | `/api/content/{post_id}/generate-image` | Generate an image for a specific post |
| GET | `/api/images/models` | List available Stability AI models |
| GET | `/api/images/platforms` | List platform dimensions |

### Example: Generate a custom image
```json
POST /api/images/generate
{
  "prompt": "Modern fitness brand social media visual, electric blue tones, energetic athlete, clean composition",
  "width": 1080,
  "height": 1080
}
```

## How It Works

1. **Content Generation**: Claude 3.5 Sonnet v2 (via AWS Bedrock) generates text content, hashtags, and ad copy
2. **Trending Analysis**: Claude analyzes current trends and generates relevant hashtag suggestions
3. **Image Generation**: Stability AI generates professional images based on:
   - The post content/concept
   - Your brand colors and industry
   - The target platform aspect ratio
4. **Fallback**: If the Stability AI key is not set, the system falls back to Pillow-based template images with your brand colors and text overlay
5. **Cost**: You only pay per API call. No running servers, no hourly costs.

## Cost Estimation (South African Rand)

Based on current pricing:
- **Claude 3.5 Sonnet v2** (Bedrock): ~R0.50 per content generation request
- **Stability AI** (SD 3.5 Large Turbo): ~R1.00 per image (based on credit pricing)
- **Backend hosting**: Free when running locally. Lambda scales to zero if deployed.
- **Total for 100 posts/month with images**: ~R150

No monthly server costs. No SageMaker endpoints running 24/7.

## Troubleshooting

- **"STABILITY_API_KEY not configured"** - Add your Stability AI key to the `.env` file.
- **"API error 403"** - Your Stability AI key may be invalid or expired. Check at https://platform.stability.ai/account/keys
- **"API error 402"** - Insufficient credits on your Stability AI account. Top up at https://platform.stability.ai
- **"AccessDeniedException" for Bedrock** - Model access not enabled. Go to Bedrock > Model access and enable Claude.
- **"No credentials"** - Check your `.env` file has the correct AWS keys.
- **App cannot connect** - Make sure the backend is running and the URL is correct for your device type.
- **Fallback images showing** - This means the Stability AI key is not set or API returned an error.
