"""Tests for the diagnostics API routes."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

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
        mock_settings.aws_region = "eu-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        response = await client.get("/api/diagnostics/test-claude")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["region"] == "eu-central-1"
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
        mock_settings.aws_region = "eu-central-1"
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
        mock_settings.aws_region = "eu-central-1"
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


# ============== Test Stability AI Endpoint ==============


@pytest.mark.asyncio
async def test_stability_no_api_key(client):
    """Test Stability endpoint when API key is not configured."""
    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.stability_api_key = None
        mock_settings.stability_model = "sd3.5-large-turbo"

        response = await client.get("/api/diagnostics/test-stability")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["api_configured"] is False
    assert "not configured" in data["message"].lower()


@pytest.mark.asyncio
async def test_stability_success(client):
    """Test Stability endpoint with successful response."""
    fake_image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = fake_image_bytes

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.stability_api_key = "sk-test-key"
        mock_settings.stability_model = "sd3.5-large-turbo"

        with patch("app.api.routes.diagnostics.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            response = await client.get("/api/diagnostics/test-stability")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["message"] == "Success"
    assert data["image_size_bytes"] == len(fake_image_bytes)
    assert data["api_configured"] is True


@pytest.mark.asyncio
async def test_stability_api_error(client):
    """Test Stability endpoint when API returns an error."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Invalid API key"

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.stability_api_key = "sk-invalid-key"
        mock_settings.stability_model = "sd3.5-large-turbo"

        with patch("app.api.routes.diagnostics.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            response = await client.get("/api/diagnostics/test-stability")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "403" in data["message"]


# ============== Test Combined AWS Endpoint ==============


@pytest.mark.asyncio
async def test_aws_combined_no_credentials(client):
    """Test combined endpoint when credentials are not configured."""
    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = None
        mock_settings.aws_secret_access_key = None
        mock_settings.aws_region = "eu-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        mock_settings.stability_api_key = None
        mock_settings.stability_model = "sd3.5-large-turbo"

        response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["aws_credentials_configured"] is False
    assert data["aws_region"] == "eu-central-1"
    assert data["bedrock_text_model"]["status"] == "error"
    assert data["stability_image_model"]["status"] == "error"


@pytest.mark.asyncio
async def test_aws_combined_success(client):
    """Test combined endpoint when both services work."""
    # Mock Claude response
    text_response_body = json.dumps({
        "content": [{"text": "Hello"}],
    }).encode()
    mock_text_stream = MagicMock()
    mock_text_stream.read.return_value = text_response_body

    mock_bedrock = MagicMock()
    mock_bedrock.invoke_model.return_value = {"body": mock_text_stream}

    # Mock Stability AI response
    fake_image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    mock_stability_response = MagicMock()
    mock_stability_response.status_code = 200
    mock_stability_response.content = fake_image_bytes

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "eu-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        mock_settings.stability_api_key = "sk-test-key"
        mock_settings.stability_model = "sd3.5-large-turbo"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.return_value = mock_bedrock
            mock_session_cls.return_value = mock_session

            with patch("app.api.routes.diagnostics.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_stability_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["aws_credentials_configured"] is True
    assert data["bedrock_text_model"]["status"] == "connected"
    assert data["stability_image_model"]["status"] == "connected"
