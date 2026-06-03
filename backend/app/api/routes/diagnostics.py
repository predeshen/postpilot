"""Diagnostics API routes for testing AWS Bedrock connectivity."""

import base64
import json
import logging

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.get("/test-aws")
async def test_aws_connection():
    """Test AWS Bedrock connectivity and model access.

    Verifies:
    1. AWS credentials are configured
    2. Bedrock client can be initialized
    3. Text model (Claude) can generate a response
    4. Image model (Bria) can generate an image
    """
    result = {
        "aws_credentials_configured": False,
        "aws_region": settings.aws_region,
        "bedrock_text_model": {
            "model_id": settings.bedrock_model_id,
            "status": "error",
            "message": "Not tested",
            "response_preview": None,
        },
        "bedrock_image_model": {
            "model_id": settings.bedrock_image_model_id,
            "status": "error",
            "message": "Not tested",
            "image_size_bytes": None,
        },
    }

    # Step 1: Check if credentials are configured
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        result["bedrock_text_model"]["message"] = "AWS credentials not configured"
        result["bedrock_image_model"]["message"] = "AWS credentials not configured"
        return result

    result["aws_credentials_configured"] = True

    # Build session kwargs
    session_kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }

    # Step 2: Test Bedrock client initialization and list models
    try:
        session = boto3.Session(**session_kwargs)
        bedrock_client = session.client("bedrock")
        bedrock_client.list_foundation_models(maxResults=1)
    except NoCredentialsError as e:
        result["bedrock_text_model"]["message"] = f"Credentials error: {e}"
        result["bedrock_image_model"]["message"] = f"Credentials error: {e}"
        return result
    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        result["bedrock_text_model"]["message"] = f"Bedrock client error: {error_msg}"
        result["bedrock_image_model"]["message"] = f"Bedrock client error: {error_msg}"
        return result
    except Exception as e:
        result["bedrock_text_model"]["message"] = f"Unexpected error: {e}"
        result["bedrock_image_model"]["message"] = f"Unexpected error: {e}"
        return result

    # Step 3: Test text model (Claude) via bedrock-runtime
    try:
        runtime_client = session.client("bedrock-runtime")
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

        result["bedrock_text_model"]["status"] = "connected"
        result["bedrock_text_model"]["message"] = "Successfully generated response"
        result["bedrock_text_model"]["response_preview"] = content_text[:50]

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        result["bedrock_text_model"]["message"] = f"Text model error: {error_msg}"
    except Exception as e:
        result["bedrock_text_model"]["message"] = f"Text model error: {e}"

    # Step 4: Test image model (Bria) via bedrock-runtime
    try:
        runtime_client = session.client("bedrock-runtime")
        body = json.dumps({
            "prompt": "test",
            "num_results": 1,
            "width": 256,
            "height": 256,
        })

        response = runtime_client.invoke_model(
            modelId=settings.bedrock_image_model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())

        if "artifacts" in response_body and len(response_body["artifacts"]) > 0:
            image_base64 = response_body["artifacts"][0]["base64"]
            image_bytes = base64.b64decode(image_base64)
            result["bedrock_image_model"]["status"] = "connected"
            result["bedrock_image_model"]["message"] = "Successfully generated image"
            result["bedrock_image_model"]["image_size_bytes"] = len(image_bytes)
        else:
            result["bedrock_image_model"]["message"] = (
                f"Unexpected response format: {list(response_body.keys())}"
            )

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        result["bedrock_image_model"]["message"] = f"Image model error: {error_msg}"
    except Exception as e:
        result["bedrock_image_model"]["message"] = f"Image model error: {e}"

    return result
