from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel


class APIEndpoint(BaseModel):
    """API endpoint specification."""

    path: str
    method: str
    request_body: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None


class FastAPISpecsExtractor(BaseModel):
    """Agent for extracting OpenAPI specifications from FastAPI endpoints."""

    def extract_specs(self, app: FastAPI) -> list[APIEndpoint]:
        """Extract API specifications from the FastAPI application."""
        openapi_schema = app.openapi()
        if not openapi_schema or "paths" not in openapi_schema:
            return []
        paths: dict[str, dict[str, Any]] = openapi_schema.get("paths")

        endpoints: list[APIEndpoint] = []
        for path, path_info in paths.items():
            for method, operation in path_info.items():
                endpoint = APIEndpoint(
                    path=path,
                    method=method.upper(),
                    request_body=self._extract_request_body(operation, app),
                    response_schema=self._extract_response_schema(operation),
                )
                endpoints.append(endpoint)

        return endpoints

    def _extract_request_body(self, operation: dict[str, Any], app: FastAPI) -> dict[str, Any] | None:
        """Extract request body schema from operation details."""
        try:
            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {}).get("application/json", {})
            schema = content.get("schema", {})

            if "$ref" in schema:
                components = app.openapi()["components"]["schemas"]
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
