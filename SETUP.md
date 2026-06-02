# PostPilot - Complete Setup Guide

## Prerequisites
- AWS Account (even a free tier/demo account works)
- Python 3.9+
- Android Studio (for the mobile app)

## Step 1: Enable AWS Bedrock Model Access
1. Sign in to AWS Console: https://console.aws.amazon.com
2. Go to Amazon Bedrock service (search "Bedrock" in the search bar)
3. Make sure you are in the **us-east-1** region (N. Virginia)
4. In the left sidebar, click "Model access"
5. Click "Manage model access" button
6. Check the boxes for:
   - **Anthropic > Claude 3 Sonnet** (for text/content generation)
   - **Bria > Bria 2.3 Fast** (for image generation - primary)
   - **Bria > Bria 2.3** (optional - higher quality images)
   - **Bria > Bria 2.2 HD** (optional - highest quality images)
7. Click "Request model access"
8. Wait for approval (usually instant for these models)

## Step 2: Create AWS Access Keys
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
6. Name the policy "BedrockInvokeAccess" and create it
7. Go back to the user creation, attach "BedrockInvokeAccess"
8. Create the user
9. Go to the user > "Security credentials" tab > "Create access key"
10. Choose "Application running outside AWS"
11. Copy the Access Key ID and Secret Access Key (save them!)

## Step 3: Configure the Backend
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
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   BEDROCK_IMAGE_MODEL_ID=bria.bria-2.3-fast-v1:0
   DEBUG=true
   ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Test it: Open http://localhost:8000/docs in your browser
7. Try the health check: http://localhost:8000/health

## Step 4: Test Image Generation
Once the backend is running, test Bria AI image generation:

```bash
curl -X POST http://localhost:8000/api/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A professional social media post for a fitness brand, modern design, bold typography, electric blue and coral colors",
    "width": 1080,
    "height": 1080
  }'
```

Or use the Swagger docs at http://localhost:8000/docs and find the `/api/images/generate` endpoint.

## Step 5: Set Up the Android App
1. Download and install Android Studio: https://developer.android.com/studio
2. Open Android Studio > File > Open > select the `android-app/` folder
3. Wait for Gradle sync to complete (may take a few minutes first time)
4. Connect your phone via USB with Developer Mode enabled, OR use the emulator
5. In `app/build.gradle.kts`, the BASE_URL is set to:
   - For emulator: `http://10.0.2.2:8000` (this maps to your PC's localhost)
   - For physical device on same WiFi: change to `http://YOUR_PC_IP:8000`
6. Click the green "Run" button in Android Studio
7. The app will install on your device/emulator

## Step 6: Build the APK (for sharing/installing)
1. In Android Studio: Build > Build Bundle(s) / APK(s) > Build APK(s)
2. The APK will be at: `android-app/app/build/outputs/apk/debug/app-debug.apk`
3. Transfer this APK to any Android phone to install

## Step 7: Deploy Backend to AWS (Production)
1. Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
2. Install SAM CLI: https://docs.aws.amazon.com/sam/latest/userguide/install-sam-cli.html
3. Configure AWS CLI:
   ```bash
   aws configure
   # Enter your Access Key ID
   # Enter your Secret Access Key
   # Region: us-east-1
   # Output format: json
   ```
4. Deploy:
   ```bash
   cd backend
   chmod +x deploy-aws.sh
   ./deploy-aws.sh
   ```
5. After deployment, you will get an API Gateway URL like:
   `https://abc123.execute-api.us-east-1.amazonaws.com`
6. Update the Android app's BASE_URL in `app/build.gradle.kts` with this URL
7. Rebuild the APK

## Image Generation Models Available

| Model | ID | Best For |
|-------|-----|----------|
| Bria 2.3 Fast | `bria.bria-2.3-fast-v1:0` | Quick generation, real-time use (DEFAULT) |
| Bria 2.3 | `bria.bria-2.3-v1:0` | Higher quality, slightly slower |
| Bria 2.2 HD | `bria.bria-2.2-hd-v1:0` | Highest quality, best for final ad creatives |

To change the model, update `BEDROCK_IMAGE_MODEL_ID` in your `.env` file.

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
  "height": 1080,
  "model_id": "bria.bria-2.3-fast-v1:0"
}
```

### Example: Generate image for a post
```json
POST /api/content/1/generate-image
// No body needed - uses the post content and business brand identity
```

## How It Works

1. **Content Generation**: Claude 3 Sonnet (via Bedrock) generates text content, hashtags, and ad copy
2. **Image Generation**: Bria AI (via Bedrock) generates professional images based on:
   - The post content/concept
   - Your brand colors
   - Your industry
   - The target platform dimensions
3. **Fallback**: If Bedrock is unavailable (no credentials, quota exceeded), the system falls back to Pillow-based template images with your brand colors and text overlay
4. **Cost**: You only pay per API call - no monthly fees. The Lambda backend scales to zero when idle.

## Troubleshooting

- **"AccessDeniedException"** - Model access not enabled. Go to Bedrock > Model access and enable the Bria models.
- **"No credentials"** - Check your `.env` file has the correct AWS keys.
- **App cannot connect** - Make sure the backend is running and the URL is correct for your device type.
- **Images not generating** - Bria models may not be available in all regions. Use us-east-1.
- **"ValidationException"** - Check that width/height are within 256-2048 range.
- **Fallback images showing** - This means Bedrock is not reachable. Check your AWS credentials and model access.

## Cost Estimation (South African Rand)

Based on current AWS Bedrock pricing:
- **Claude 3 Sonnet**: ~R0.50 per content generation request
- **Bria 2.3 Fast**: ~R0.30 per image generated
- **Lambda hosting**: Free tier covers ~1 million requests/month
- **Total for 100 posts/month with images**: approximately R80-R120

No monthly server costs - you only pay when the app generates content.
