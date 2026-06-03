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


@pytest.mark.asyncio
async def test_aws_diagnostics_no_credentials(client):
    """Test diagnostics endpoint when AWS credentials are not configured."""
    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = None
        mock_settings.aws_secret_access_key = None
        mock_settings.aws_region = "eu-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        mock_settings.bedrock_image_model_id = "bria.bria-2.3-fast-v1:0"

        response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["aws_credentials_configured"] is False
    assert data["aws_region"] == "eu-central-1"
    assert data["bedrock_text_model"]["status"] == "error"
    assert data["bedrock_image_model"]["status"] == "error"
    assert "not configured" in data["bedrock_text_model"]["message"].lower()


@pytest.mark.asyncio
async def test_aws_diagnostics_with_credentials_success(client):
    """Test diagnostics endpoint when AWS credentials work correctly."""
    mock_bedrock = MagicMock()
    mock_bedrock.list_foundation_models.return_value = {"modelSummaries": []}

    mock_runtime = MagicMock()

    # Mock text model response
    text_response_body = json.dumps({
        "content": [{"text": "Hello"}],
    }).encode()
    mock_text_stream = MagicMock()
    mock_text_stream.read.return_value = text_response_body
    mock_runtime.invoke_model.side_effect = [
        {"body": mock_text_stream},
        _make_image_response(),
    ]

    def mock_client_factory(service_name, **kwargs):
        if service_name == "bedrock":
            return mock_bedrock
        return mock_runtime

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "eu-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        mock_settings.bedrock_image_model_id = "bria.bria-2.3-fast-v1:0"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.side_effect = mock_client_factory
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["aws_credentials_configured"] is True
    assert data["aws_region"] == "eu-central-1"
    assert data["bedrock_text_model"]["status"] == "connected"
    assert data["bedrock_text_model"]["response_preview"] == "Hello"
    assert data["bedrock_image_model"]["status"] == "connected"
    assert data["bedrock_image_model"]["image_size_bytes"] > 0


@pytest.mark.asyncio
async def test_aws_diagnostics_bedrock_client_error(client):
    """Test diagnostics endpoint when Bedrock client initialization fails."""
    from botocore.exceptions import ClientError

    mock_bedrock = MagicMock()
    mock_bedrock.list_foundation_models.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
        "ListFoundationModels",
    )

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "eu-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        mock_settings.bedrock_image_model_id = "bria.bria-2.3-fast-v1:0"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.return_value = mock_bedrock
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["aws_credentials_configured"] is True
    assert data["bedrock_text_model"]["status"] == "error"
    assert "Access denied" in data["bedrock_text_model"]["message"]


@pytest.mark.asyncio
async def test_aws_diagnostics_text_model_error(client):
    """Test diagnostics when text model fails but image model succeeds."""
    from botocore.exceptions import ClientError

    mock_bedrock = MagicMock()
    mock_bedrock.list_foundation_models.return_value = {"modelSummaries": []}

    mock_runtime = MagicMock()
    # First call (text) raises, second call (image) succeeds
    mock_runtime.invoke_model.side_effect = [
        ClientError(
            {"Error": {"Code": "ModelNotReadyException", "Message": "Model not ready"}},
            "InvokeModel",
        ),
        _make_image_response(),
    ]

    def mock_client_factory(service_name, **kwargs):
        if service_name == "bedrock":
            return mock_bedrock
        return mock_runtime

    with patch("app.api.routes.diagnostics.settings") as mock_settings:
        mock_settings.aws_access_key_id = "test-key"
        mock_settings.aws_secret_access_key = "test-secret"
        mock_settings.aws_region = "eu-central-1"
        mock_settings.bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        mock_settings.bedrock_image_model_id = "bria.bria-2.3-fast-v1:0"

        with patch("app.api.routes.diagnostics.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.client.side_effect = mock_client_factory
            mock_session_cls.return_value = mock_session

            response = await client.get("/api/diagnostics/test-aws")

    assert response.status_code == 200
    data = response.json()
    assert data["bedrock_text_model"]["status"] == "error"
    assert "Model not ready" in data["bedrock_text_model"]["message"]
    assert data["bedrock_image_model"]["status"] == "connected"


def _make_image_response():
    """Create a mock image response from Bria."""
    import base64
    # Create a tiny fake PNG (1x1 pixel)
    fake_image = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50).decode()
    response_body = json.dumps({
        "artifacts": [{"base64": fake_image}],
    }).encode()
    mock_stream = MagicMock()
    mock_stream.read.return_value = response_body
    return {"body": mock_stream}
