"""Diagnostics API routes for testing AWS connectivity.

Provides separate endpoints for testing:
- Claude text model via Bedrock
- Bria image model via SageMaker
- Combined test for convenience
"""

import base64
import json
import logging

import boto3
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


@router.get("/test-bria")
async def test_bria_connection():
    """Test Bria image model connectivity via AWS SageMaker.

    Verifies:
    1. SageMaker endpoint name is configured
    2. AWS credentials are configured
    3. SageMaker endpoint can generate an image
    """
    result = {
        "status": "error",
        "endpoint_name": settings.sagemaker_endpoint_name,
        "region": settings.aws_region,
        "message": "Not tested",
        "image_size_bytes": None,
    }

    # Check if endpoint is configured
    if not settings.sagemaker_endpoint_name:
        result["status"] = "not_deployed"
        result["message"] = (
            "Endpoint not configured - deploy Bria first. "
            "Set SAGEMAKER_ENDPOINT_NAME in your .env file."
        )
        return result

    # Check if credentials are configured
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        result["message"] = "AWS credentials not configured"
        return result

    # Initialize SageMaker Runtime client
    try:
        session = boto3.Session(
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        sagemaker_client = session.client("sagemaker-runtime")
    except NoCredentialsError as e:
        result["message"] = f"Credentials error: {e}"
        return result
    except Exception as e:
        result["message"] = f"Session error: {e}"
        return result

    # Test Bria via SageMaker endpoint
    try:
        payload = json.dumps({
            "prompt": "test image",
            "steps": 8,
            "eula_license_agreement": True,
            "seed": 42,
            "aspect_ratio": "1:1",
            "negative_prompt": "text, watermark",
        })

        response = sagemaker_client.invoke_endpoint(
            EndpointName=settings.sagemaker_endpoint_name,
            ContentType="application/json",
            Accept="application/json",
            Body=payload,
        )

        response_body = json.loads(response["Body"].read())

        if response_body.get("result") == "success" and "artifacts" in response_body:
            if len(response_body["artifacts"]) > 0:
                image_base64 = response_body["artifacts"][0]["image_base64"]
                image_bytes = base64.b64decode(image_base64)
                result["status"] = "connected"
                result["message"] = "Success"
                result["image_size_bytes"] = len(image_bytes)
            else:
                result["message"] = "No artifacts in response"
        else:
            result["message"] = (
                f"Unexpected response format: {list(response_body.keys())}"
            )

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        result["message"] = f"SageMaker error: {error_msg}"
    except Exception as e:
        result["message"] = f"SageMaker error: {e}"

    return result


@router.get("/test-aws")
async def test_aws_connection():
    """Test all AWS connectivity (Claude via Bedrock + Bria via SageMaker).

    Runs both tests and returns combined results for convenience.
    """
    claude_result = await test_claude_connection()
    bria_result = await test_bria_connection()

    return {
        "aws_credentials_configured": bool(
            settings.aws_access_key_id and settings.aws_secret_access_key
        ),
        "aws_region": settings.aws_region,
        "bedrock_text_model": claude_result,
        "sagemaker_image_model": bria_result,
    }
