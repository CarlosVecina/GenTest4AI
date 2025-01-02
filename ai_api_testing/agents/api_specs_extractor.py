import json
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field


class APIEndpoint(BaseModel):
    """API endpoint specification."""

    path: str
    method: str
    request_body: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None


class APISpecsExtractor(BaseModel):
    """Agent for extracting OpenAPI specifications from FastAPI endpoints."""

    app: FastAPI = Field(description="FastAPI application instance to analyze")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def extract_specs(self) -> list[APIEndpoint]:
        """Extract API specifications from the FastAPI application."""
        openapi_schema = self.app.openapi()
        if not openapi_schema or "paths" not in openapi_schema:
            return []
        paths: dict[str, dict[str, Any]] = openapi_schema.get("paths")

        endpoints: list[APIEndpoint] = []
        for path, path_info in paths.items():
            for method, operation in path_info.items():
                endpoint = APIEndpoint(
                    path=path,
                    method=method.upper(),
                    request_body=self._extract_request_body(operation),
                    response_schema=self._extract_response_schema(operation),
                )
                endpoints.append(endpoint)

        return endpoints

    def _extract_request_body(self, operation: dict[str, Any]) -> dict[str, Any] | None:
        """Extract request body schema from operation details."""
        try:
            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {}).get("application/json", {})
            schema = content.get("schema", {})

            if "$ref" in schema:
                components = self.app.openapi()["components"]["schemas"]
                return components[schema["$ref"].split("/")[-1]]
            return schema or None
        except (KeyError, AttributeError):
            return None

    def _extract_response_schema(self, operation: dict[str, Any]) -> dict[str, Any] | None:
        """Extract response schema from operation details."""
        responses = operation.get("responses", {})
        if "200" in responses:
            content = responses["200"].get("content", {})
            if "application/json" in content:
                return content["application/json"].get("schema", {})
        return None

    def to_json(self) -> str:
        """Convert extracted specifications to JSON string."""
        return json.dumps([endpoint.model_dump() for endpoint in self._endpoints], indent=2)
