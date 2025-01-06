import json
from unittest.mock import AsyncMock, patch

import pytest
import yaml
from aiounittest import AsyncTestCase

from ai_api_testing.agents.api_specs.swagger_extractor import SwaggerExtractor


@pytest.fixture
def simple_openapi_spec():
    """Simple OpenAPI spec with a GET and POST endpoint."""
    return {
        "paths": {
            "/pets": {
                "get": {
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "type": "string",
                            "required": True,
                        }
                    ]
                },
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer"},
                                    },
                                }
                            }
                        }
                    }
                },
            }
        }
    }


def test_parse_spec_with_query_params(simple_openapi_spec):
    """Test parsing of spec with query params."""
    extractor = SwaggerExtractor()
    extractor._spec = simple_openapi_spec

    endpoints = extractor._parse_spec()

    assert len(endpoints) == 2
    get_endpoint = next(ep for ep in endpoints if ep.method == "GET")
    assert get_endpoint.path == "/pets"
    assert get_endpoint.request_body == {
        "type": "object",
        "properties": {"status": {"type": "string", "description": "", "required": True}},
    }


def test_parse_spec_with_request_body(simple_openapi_spec):
    """Test parsing of spec with request body."""
    extractor = SwaggerExtractor()
    extractor._spec = simple_openapi_spec

    endpoints = extractor._parse_spec()

    post_endpoint = next(ep for ep in endpoints if ep.method == "POST")
    assert post_endpoint.path == "/pets"
    assert post_endpoint.request_body == {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
    }


def test_parse_spec_with_endpoint_list(simple_openapi_spec):
    """Test parsing of spec with endpoint list."""
    extractor = SwaggerExtractor()
    extractor._spec = simple_openapi_spec

    endpoints = extractor._parse_spec(endpoint_list=["/pets"])
    assert len(endpoints) == 2
    assert endpoints[0].path == "/pets"
    assert endpoints[0].method == "GET"
    assert endpoints[1].path == "/pets"
    assert endpoints[1].method == "POST"

    endpoints = extractor._parse_spec(endpoint_list=["/non-existent"])
    assert len(endpoints) == 0


def test_parse_spec_with_invalid_spec():
    """Test parsing of spec with invalid spec."""
    extractor = SwaggerExtractor()
    extractor._spec = {}
    with pytest.raises(ValueError):
        extractor._parse_spec()


class TestSwaggerExtractor(AsyncTestCase):
    """Test SwaggerExtractor class."""

    async def test_try_direct_spec_access(self):
        """Test direct access to OpenAPI spec with different response scenarios."""
        simple_openapi_spec = {"paths": {"/test": {"get": {}}}}  # Simple mock spec
        extractor = SwaggerExtractor()

        # Create a mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=simple_openapi_spec)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await extractor._try_direct_spec_access("http://api.example.com")
            self.assertTrue(result)
            self.assertEqual(extractor._spec, simple_openapi_spec)

    async def test_try_direct_spec_access_parse_failure(self):
        """Test direct access when both JSON and YAML parsing fail."""
        extractor = SwaggerExtractor()

        # Create a mock response that will fail JSON parsing
        mock_response = AsyncMock()
        mock_response.status = 200
        json_error = json.JSONDecodeError("Expecting value", "<string>", 0)
        mock_response.json.side_effect = json_error
        mock_response.text = AsyncMock(return_value="Invalid YAML content")
        mock_response.close = AsyncMock()

        # Create a mock session with context manager methods
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("aiohttp.ClientSession", return_value=mock_session),
            patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")),
        ):
            result = await extractor._try_direct_spec_access("http://api.example.com")

            # Verify not available to parse JSON nor YAML
            self.assertFalse(result)
            self.assertIsNone(extractor._spec)

            # Verify all paths were tried
            expected_calls = len(
                [
                    "",
                    "/openapi.json",
                    "/swagger.json",
                    "/api-docs",
                    "/api-docs.json",
                    "/swagger/v1/swagger.json",
                ]
            )
            self.assertEqual(mock_session.get.call_count, expected_calls)

            self.assertEqual(mock_response.close.call_count, expected_calls)
