import pytest

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

    endpoints = extractor._parse_spec(endpoint_list=["/non-existent"])
    assert len(endpoints) == 0
