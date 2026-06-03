"""Tests for the diagnostics API routes."""

import json
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    """Create a test HTTP client (no DB needed for diagnostics)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============== Test Claude Endpoint ==============


@pytest.mark.asyncio
async def test_claude_no_credentials(client):
    """Test Claude endpoint when AWS credentials are not configured."""
    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = None
        mock_settings.aws_secret_access_key = None
        mock_settings.aws_region = "ca-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        response = await client.get("/api/diagnostics/test-claude")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["region"] == "ca-central-1"
    assert "not configured" in data["message"].lower()


@pytest.mark.asyncio
async def test_claude_success(client):
    """Test Claude endpoint with successful response."""
    mock_runtime = MagicMock()

    text_response_body = json.dumps({
        "content": [{"text": "Hello"}],
    }).encode()
    mock_text_stream = MagicMock()
    mock_text_stream.read.return_value = text_response_body
    mock_runtime.invoke_model.return_value = {"body": mock_text_stream}

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "ca-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.return_value = mock_runtime
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-claude")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["message"] == "Success"
    assert data["response_preview"] == "Hello"
    assert data["model_id"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"


@pytest.mark.asyncio
async def test_claude_client_error(client):
    """Test Claude endpoint when Bedrock returns an error."""
    from botocore.exceptions import ClientError

    mock_runtime = MagicMock()
    mock_runtime.invoke_model.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
        "InvokeModel",
    )

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "ca-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.return_value = mock_runtime
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-claude")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Access denied" in data["message"]


# ============== Test Bria Endpoint ==============


@pytest.mark.asyncio
async def test_bria_no_endpoint_configured(client):
    """Test Bria endpoint when SageMaker endpoint is not configured."""
    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.sagemaker_endpoint_name = None
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "ca-central-1"

        response = await client.get("/api/diagnostics/test-bria")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_deployed"
    assert data["endpoint_name"] is None
    assert "deploy bria first" in data["message"].lower()


@pytest.mark.asyncio
async def test_bria_no_credentials(client):
    """Test Bria endpoint when credentials are missing."""
    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.sagemaker_endpoint_name = "postpilot-bria"
        mock_settings.aws_access_key_id = None
        mock_settings.aws_secret_access_key = None
        mock_settings.aws_region = "ca-central-1"

        response = await client.get("/api/diagnostics/test-bria")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "not configured" in data["message"].lower()


@pytest.mark.asyncio
async def test_bria_success(client):
    """Test Bria endpoint with successful SageMaker response."""
    import base64

    fake_image = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50).decode()
    response_body = json.dumps({
        "result": "success",
        "artifacts": [
            {
                "seed": 42,
                "image_base64": fake_image,
                "embeddings_base64": [],
            }
        ],
    }).encode()

    mock_sagemaker = MagicMock()
    mock_body_stream = MagicMock()
    mock_body_stream.read.return_value = response_body
    mock_sagemaker.invoke_endpoint.return_value = {"Body": mock_body_stream}

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.sagemaker_endpoint_name = "postpilot-bria"
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "ca-central-1"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.return_value = mock_sagemaker
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-bria")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["message"] == "Success"
    assert data["image_size_bytes"] > 0
    assert data["endpoint_name"] == "postpilot-bria"


@pytest.mark.asyncio
async def test_bria_sagemaker_error(client):
    """Test Bria endpoint when SageMaker returns an error."""
    from botocore.exceptions import ClientError

    mock_sagemaker = MagicMock()
    mock_sagemaker.invoke_endpoint.side_effect = ClientError(
        {"Error": {"Code": "ModelError", "Message": "Endpoint not in service"}},
        "InvokeEndpoint",
    )

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.sagemaker_endpoint_name = "postpilot-bria"
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "ca-central-1"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.return_value = mock_sagemaker
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-bria")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Endpoint not in service" in data["message"]


# ============== Test Combined AWS Endpoint ==============


@pytest.mark.asyncio
async def test_aws_combined_no_credentials(client):
    """Test combined AWS endpoint when credentials are not configured."""
    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = None
        mock_settings.aws_secret_access_key = None
        mock_settings.aws_region = "ca-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        mock_settings.sagemaker_endpoint_name = None

        response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["aws_credentials_configured"] is False
    assert data["aws_region"] == "ca-central-1"
    assert data["bedrock_text_model"]["status"] == "error"
    assert data["sagemaker_image_model"]["status"] == "not_deployed"


@pytest.mark.asyncio
async def test_aws_combined_success(client):
    """Test combined AWS endpoint when both services work."""
    import base64

    # Mock Claude response
    text_response_body = json.dumps({
        "content": [{"text": "Hello"}],
    }).encode()
    mock_text_stream = MagicMock()
    mock_text_stream.read.return_value = text_response_body

    # Mock Bria response
    fake_image = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50).decode()
    image_response_body = json.dumps({
        "result": "success",
        "artifacts": [{"seed": 42, "image_base64": fake_image, "embeddings_base64": []}],
    }).encode()
    mock_image_stream = MagicMock()
    mock_image_stream.read.return_value = image_response_body

    # Track which client is being created
    call_count = {"n": 0}

    def mock_client_factory(service_name, **kwargs):
        call_count["n"] += 1
        if service_name == "bedrock-runtime":
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.return_value = {"body": mock_text_stream}
            return mock_bedrock
        elif service_name == "sagemaker-runtime":
            mock_sm = MagicMock()
            mock_sm.invoke_endpoint.return_value = {"Body": mock_image_stream}
            return mock_sm
        return MagicMock()

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "ca-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        mock_settings.sagemaker_endpoint_name = "postpilot-bria"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.side_effect = mock_client_factory
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["aws_credentials_configured"] is True
    assert data["bedrock_text_model"]["status"] == "connected"
    assert data["sagemaker_image_model"]["status"] == "connected"
