"""Diagnostics API routes for testing service connectivity.

Provides separate endpoints for testing:
- Claude text model via AWS Bedrock
- Stability AI image generation
- Combined test for convenience
"""

import json
import logging

import boto3
import httpx
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.get("/test-claude")
async def test_claude_connection():
    """Test Claude text model connectivity via AWS Bedrock.

    Verifies:
    1. AWS credentials are configured
    2. Bedrock Runtime client can be initialized
    3. Claude model can generate a response
    """
    result = {
        "status": "error",
        "model_id": settings.bedrock_model_id,
        "region": settings.aws_region,
        "message": "Not tested",
        "response_preview": None,
    }

    # Check if credentials are configured
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        result["message"] = "AWS credentials not configured"
        return result

    # Initialize session and runtime client
    try:
        session = boto3.Session(
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        runtime_client = session.client("bedrock-runtime")
    except NoCredentialsError as e:
        result["message"] = f"Credentials error: {e}"
        return result
    except Exception as e:
        result["message"] = f"Session error: {e}"
        return result

    # Test text model (Claude) via bedrock-runtime
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "messages": [
                {"role": "user", "content": "Say hello in one word"}
            ],
            "temperature": 0.1,
        })

        response = runtime_client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        content_text = response_body["content"][0]["text"]

        result["status"] = "connected"
        result["message"] = "Success"
        result["response_preview"] = content_text[:50]

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        result["message"] = f"Text model error: {error_msg}"
    except Exception as e:
        result["message"] = f"Text model error: {e}"

    return result


@router.get("/test-stability")
async def test_stability_connection():
    """Test Stability AI image generation connectivity.

    Verifies:
    1. Stability API key is configured
    2. API endpoint is reachable
    3. Image generation works
    """
    result = {
        "status": "error",
        "api_configured": bool(settings.stability_api_key),
        "model": settings.stability_model,
        "message": "Not tested",
        "image_size_bytes": None,
    }

    if not settings.stability_api_key:
        result["message"] = "STABILITY_API_KEY not configured"
        return result

    # Try generating a small test image
    headers = {
        "Authorization": f"Bearer {settings.stability_api_key}",
        "Accept": "image/*",
    }
    data = {
        "prompt": "test",
        "model": settings.stability_model,
        "aspect_ratio": "1:1",
        "output_format": "png",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.stability.ai/v2beta/stable-image/generate/sd3",
                headers=headers,
                data=data,
            )

            if response.status_code == 200:
                result["status"] = "connected"
                result["message"] = "Success"
                result["image_size_bytes"] = len(response.content)
            else:
                result["message"] = f"API error {response.status_code}: {response.text[:200]}"
    except httpx.TimeoutException:
        result["message"] = "Request timed out"
    except Exception as e:
        result["message"] = f"Request failed: {e}"

    return result


@router.get("/test-aws")
async def test_aws_connection():
    """Test all service connectivity (Claude via Bedrock + Stability AI).

    Runs both tests and returns combined results for convenience.
    """
    claude_result = await test_claude_connection()
    stability_result = await test_stability_connection()

    return {
        "aws_credentials_configured": bool(
            settings.aws_access_key_id and settings.aws_secret_access_key
        ),
        "aws_region": settings.aws_region,
        "bedrock_text_model": claude_result,
        "stability_image_model": stability_result,
    }
