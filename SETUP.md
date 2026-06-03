# PostPilot - Complete Setup Guide

## Prerequisites
- AWS Account (even a free tier/demo account works)
- Python 3.9+
- Android Studio (for the mobile app)

## Step 1: Enable AWS Bedrock Model Access (Claude)
1. Sign in to AWS Console: https://console.aws.amazon.com
2. Go to Amazon Bedrock service (search "Bedrock" in the search bar)
3. Make sure you are in the **ca-central-1** region (Canada - Central)
4. In the left sidebar, click "Model access"
5. Click "Manage model access" button
6. Check the box for:
   - **Anthropic > Claude 3.5 Sonnet v2** (for text/content generation)
7. Click "Request model access"
8. Wait for approval (usually instant for Claude)

## Step 2: Subscribe to Bria AI (SageMaker Marketplace)
1. Go to AWS Marketplace: https://aws.amazon.com/marketplace
2. Search for "Bria 2.3 Fast Commercial"
3. Subscribe to the model (free to subscribe, you pay per endpoint usage)
4. Note: You need to DEPLOY an endpoint before it can be used (see Step below)

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
         "Action": [
           "bedrock:InvokeModel",
           "sagemaker:InvokeEndpoint"
         ],
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

## Step 4: Deploy Bria Image Model (SageMaker)

The Bria AI model is a Marketplace model that requires a SageMaker endpoint deployment.

### Option A: Deploy via AWS Console
1. Go to SageMaker > Marketplace models in ca-central-1
2. Find "Bria 2.3 Fast Commercial" (you should already be subscribed)
3. Click "Deploy"
4. Choose instance type: `ml.g5.xlarge` (GPU required for image generation)
5. Set endpoint name: `postpilot-bria` (or any name you prefer)
6. Deploy and wait for status to show "InService" (5-10 minutes)
7. Update your `.env` file: `SAGEMAKER_ENDPOINT_NAME=postpilot-bria`

### Option B: Deploy via AWS CLI
```bash
# Create the model
aws sagemaker create-model \
  --model-name postpilot-bria \
  --primary-container ModelPackageName=arn:aws:sagemaker:ca-central-1:aws:hub-content/SageMakerPublicHub/Model/bria-ai-2-3-fast-commercial/4.1.4 \
  --execution-role-name your-sagemaker-role \
  --region ca-central-1

# Create endpoint config
aws sagemaker create-endpoint-config \
  --endpoint-config-name postpilot-bria-config \
  --production-variants VariantName=default,ModelName=postpilot-bria,InstanceType=ml.g5.xlarge,InitialInstanceCount=1 \
  --region ca-central-1

# Create endpoint
aws sagemaker create-endpoint \
  --endpoint-name postpilot-bria \
  --endpoint-config-name postpilot-bria-config \
  --region ca-central-1
```

### Important Cost Note
SageMaker endpoints run 24/7 while active. The `ml.g5.xlarge` costs approximately $1.50/hour.
To save costs during development:
- Delete the endpoint when not testing: `aws sagemaker delete-endpoint --endpoint-name postpilot-bria --region ca-central-1`
- Re-create it when needed (takes 5-10 min to spin up)
- For production, consider using SageMaker Serverless Inference if available for this model

## Step 5: Configure the Backend
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
   AWS_ACCESS_KEY_ID=AKIA...your_key...
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_REGION=ca-central-1
   BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
   BEDROCK_IMAGE_MODEL_ID=bria-ai-2-3-fast-commercial
   SAGEMAKER_ENDPOINT_NAME=postpilot-bria
   DEBUG=true
   ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Test it: Open http://localhost:8000/docs in your browser
7. Try the health check: http://localhost:8000/health

## Step 6: Test Connectivity
Once the backend is running, test AWS connectivity:

```bash
# Test Claude (text generation)
curl http://localhost:8000/api/diagnostics/test-claude

# Test Bria (image generation via SageMaker)
curl http://localhost:8000/api/diagnostics/test-bria

# Test both at once
curl http://localhost:8000/api/diagnostics/test-aws
```

If Bria returns `"status": "not_deployed"`, you need to deploy the SageMaker endpoint first (Step 4).

## Step 7: Set Up the Android App
1. Download and install Android Studio: https://developer.android.com/studio
2. Open Android Studio > File > Open > select the `android-app/` folder
3. Wait for Gradle sync to complete (may take a few minutes first time)
4. Connect your phone via USB with Developer Mode enabled, OR use the emulator
5. In `app/build.gradle.kts`, the BASE_URL is set to:
   - For emulator: `http://10.0.2.2:8000` (this maps to your PC's localhost)
   - For physical device on same WiFi: change to `http://YOUR_PC_IP:8000`
6. Click the green "Run" button in Android Studio
7. The app will install on your device/emulator

## Step 8: Build the APK (for sharing/installing)
1. In Android Studio: Build > Build Bundle(s) / APK(s) > Build APK(s)
2. The APK will be at: `android-app/app/build/outputs/apk/debug/app-debug.apk`
3. Transfer this APK to any Android phone to install

## Step 9: Deploy Backend to AWS (Production)
1. Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
2. Install SAM CLI: https://docs.aws.amazon.com/sam/latest/userguide/install-sam-cli.html
3. Configure AWS CLI:
   ```bash
   aws configure
   # Enter your Access Key ID
   # Enter your Secret Access Key
   # Region: ca-central-1
   # Output format: json
   ```
4. Deploy:
   ```bash
   cd backend
   chmod +x deploy-aws.sh
   ./deploy-aws.sh
   ```
5. After deployment, you will get an API Gateway URL like:
   `https://abc123.execute-api.ca-central-1.amazonaws.com`
6. Update the Android app's BASE_URL in `app/build.gradle.kts` with this URL
7. Rebuild the APK

## Image Generation Architecture

PostPilot uses **two separate AWS services** for AI:

| Feature | AWS Service | Model | Region |
|---------|-------------|-------|--------|
| Text/Content Generation | Bedrock | Claude 3.5 Sonnet v2 | ca-central-1 |
| Image Generation | SageMaker | Bria 2.3 Fast Commercial | ca-central-1 |

**Why SageMaker for Bria?**
Bria 2.3 Fast Commercial is a Marketplace model. Unlike Claude which is directly available via Bedrock, Bria requires you to deploy a SageMaker endpoint. The model runs on a GPU instance that you control.

### Bria Input Format (SageMaker)
```json
{
    "prompt": "A professional photo of a product",
    "steps": 20,
    "eula_license_agreement": true,
    "seed": 42,
    "aspect_ratio": "1:1",
    "negative_prompt": "text, watermark, blurry"
}
```

### Bria Output Format (SageMaker)
```json
{
    "result": "success",
    "artifacts": [
        {
            "seed": 1525972691,
            "image_base64": "...base64 encoded image...",
            "embeddings_base64": ["..."]
        }
    ]
}
```

### Supported Aspect Ratios
- `1:1` - Instagram Feed (1080x1080)
- `9:16` - TikTok, Instagram/Facebook Stories (1080x1920)
- `16:9` - Facebook Feed (1200x630)

## API Endpoints for Image Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/images/generate` | Generate an image from a custom prompt |
| POST | `/api/content/{post_id}/generate-image` | Generate an image for a specific post |
| GET | `/api/images/models` | List available Bria AI models |
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

1. **Content Generation**: Claude 3.5 Sonnet v2 (via Bedrock) generates text content, hashtags, and ad copy
2. **Image Generation**: Bria AI (via SageMaker) generates professional images based on:
   - The post content/concept
   - Your brand colors and industry
   - The target platform aspect ratio
3. **Fallback**: If the SageMaker endpoint is not deployed or unavailable, the system falls back to Pillow-based template images with your brand colors and text overlay
4. **Cost**: You only pay per API call for Claude. For Bria, you pay for the SageMaker endpoint while it runs (~$1.50/hr for ml.g5.xlarge). The Lambda backend scales to zero when idle.

## Troubleshooting

- **"Endpoint not configured"** - Set `SAGEMAKER_ENDPOINT_NAME` in your `.env` file after deploying the Bria endpoint.
- **"ModelError" from SageMaker** - The endpoint may still be spinning up. Wait for status "InService" in the SageMaker console.
- **"AccessDeniedException" for Bedrock** - Model access not enabled. Go to Bedrock > Model access and enable Claude.
- **"AccessDeniedException" for SageMaker** - Add `sagemaker:InvokeEndpoint` to your IAM policy.
- **"No credentials"** - Check your `.env` file has the correct AWS keys.
- **App cannot connect** - Make sure the backend is running and the URL is correct for your device type.
- **Fallback images showing** - This means the SageMaker endpoint is not reachable or not configured. Check your endpoint status.

## Cost Estimation (South African Rand)

Based on current AWS pricing:
- **Claude 3.5 Sonnet v2**: ~R0.50 per content generation request
- **Bria via SageMaker**: ~R27/hour while endpoint is running (ml.g5.xlarge)
- **Lambda hosting**: Free tier covers ~1 million requests/month
- **Total for 100 posts/month**: Claude cost + endpoint time during generation

**Cost-saving tip**: Only run the SageMaker endpoint when generating images. Delete it when done. A batch of 100 images takes about 10-15 minutes, costing roughly R5-R7.

No monthly server costs for the API itself - Lambda scales to zero and only costs when the app makes requests.
