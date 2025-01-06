import argparse
import asyncio
import json
from typing import Any

import aiohttp
import yaml
from pydantic import BaseModel

from ai_api_testing.agents.api_specs.base_extractor import APIEndpoint
from ai_api_testing.utils.logger import logger


class SwaggerExtractor(BaseModel):
    """Extract API endpoints from a Swagger/OpenAPI specification."""

    _spec: dict | None = None

    async def extract_endpoints(
        self,
        url: str,
        endpoint_list: list[str] | None = None,
        try_direct_access: bool = True,
    ) -> list[APIEndpoint]:
        """Extract API endpoints from an OpenAPI documentation URL.

        Args:
            url: URL to the OpenAPI documentation
            endpoint_list: List of endpoints to extract. If None, all endpoints are extracted.
            try_direct_access: If True, try to directly access the OpenAPI spec from common paths.

        Returns:
            List of APIEndpoint objects containing endpoint information
        """
        if try_direct_access and await self._try_direct_spec_access(url):
            logger.info("Direct access successful, reading the JSON/YAML spec")
            return self._parse_spec(endpoint_list)

        logger.info("Direct access failed, trying scraping")
        return await self._scrape_and_parse_spec(url, endpoint_list)

    async def _try_direct_spec_access(self, url: str) -> bool:
        """Try to directly access OpenAPI spec from common paths."""
        common_paths = [
            "",
            "/openapi.json",
            "/swagger.json",
            "/api-docs",
            "/api-docs.json",
            "/swagger/v1/swagger.json",
        ]

        async with aiohttp.ClientSession() as session:
            for path in common_paths:
                full_url = f"{url.rstrip('/')}{path}"

                try:
                    response = await session.get(full_url)  # TODO: fix. It was easier mocking this vs nested context
                    logger.info(f"Response status: {response.status}")
                    logger.info(f"Response text: {response.text}")
                except aiohttp.ClientError as e:
                    logger.error(f"Error fetching {full_url}: {e}")
                    continue

                if response.status != 200:
                    logger.error(f"Received non-200 status code {response.status} from {full_url}")
                    response.close()
                    continue

                if response.content_type != "application/json":
                    logger.info("Content type is not application/json")
                    response.close()
                    continue

                # Try to parse as JSON
                try:
                    logger.info(f"Parsing JSON from {full_url}")
                    self._spec = await response.json()
                    logger.info(f"Parsed JSON from {full_url}")
                    response.close()
                    return True
                except (json.JSONDecodeError, aiohttp.ContentTypeError):
                    # If JSON fails, try YAML
                    try:
                        text = await response.text()
                        logger.info(f"Parsing YAML from {full_url}")
                        self._spec = yaml.safe_load(text)
                        response.close()
                        return True
                    except (yaml.YAMLError, aiohttp.ContentTypeError) as e:
                        response.close()
                        logger.error(f"Error parsing YAML from {full_url}: {e}")
                        continue
            return False

    def _parse_spec(self, endpoint_list: list[str] | None = None) -> list[APIEndpoint]:
        """Parse loaded OpenAPI spec into endpoints."""
        if not self._spec:
            raise ValueError("No OpenAPI specification loaded")

        logger.info("Parsing specs")

        paths: dict[str, dict[str, Any]] = self._spec.get("paths", {})

        paths_to_parse = paths
        if endpoint_list:
            paths_to_parse: dict[str, dict[str, Any]] = {}
            for i in endpoint_list:
                if i in paths:
                    paths_to_parse[i] = paths[i]
                else:
                    logger.warning(f"Path {i} not found in OpenAPI specification")

        endpoints = []
        for path, path_info in paths_to_parse.items():
            for method, operation in path_info.items():
                endpoint = APIEndpoint(
                    path=path,
                    method=method.upper(),
                    request_body=self._extract_request_body(operation),
                    # TODO: Add response schema
                    response_schema=None,  # self._extract_response_schema(operation)
                )
                endpoints.append(endpoint)

        return endpoints

    async def _scrape_and_parse_spec(self, url: str, endpoint_list: list[str] | None = None) -> list[APIEndpoint]:
        """Scrape and parse OpenAPI spec from Swagger UI page using browser automation."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                page = await browser.new_page()
                await page.goto(url)
                await page.wait_for_selector("#swagger-ui")
                # Wait a bit more to ensure the spec is fully loaded
                await page.wait_for_timeout(2000)

                # Extract the spec from the window object
                spec_json = await page.evaluate(
                    """
                    () => {
                        const dom = document.querySelector('.swagger-ui')
                        if (!dom) return null;
                        // Access the spec from the Swagger UI's Redux store
                        const specSelectors = window.ui.getState().get('spec').toJS();
                        return specSelectors.json;
                    }
                """
                )

                if spec_json:
                    self._spec = spec_json
                    return self._parse_spec(endpoint_list)

            finally:
                await browser.close()

        raise ValueError("Could not extract OpenAPI specification from Swagger UI")

    def _extract_request_body(self, operation: dict[str, Any]) -> dict[str, Any] | None:
        """Extract request body schema from operation details."""
        try:
            # Handle OpenAPI 3.0 style requestBody
            if "requestBody" in operation:
                request_body = operation["requestBody"]
                content = request_body.get("content", {}).get("application/json", {})
                schema = content.get("schema", {})
                if "$ref" in schema:
                    return self._resolve_reference(schema["$ref"])
                return schema or None

            # Handle Swagger/OpenAPI 2.0 style parameters
            parameters = operation.get("parameters", [])
            for param in parameters:
                if param.get("in") == "body":
                    schema = param.get("schema", {})
                    if "$ref" in schema:
                        return self._resolve_reference(schema["$ref"])
                    return schema
                elif param.get("in") == "query":
                    query_params = {}
                    for p in parameters:
                        if p.get("in") == "query":
                            param_schema = {
                                "type": p.get("type", "string"),
                                "description": p.get("description", ""),
                                "required": p.get("required", False),
                            }
                            if p.get("type") == "array":
                                param_schema["items"] = p.get("items", {})
                            query_params[p["name"]] = param_schema
                    return {"type": "object", "properties": query_params} if query_params else None
                elif param.get("in") == "formData":
                    form_params = {}
                    for p in parameters:
                        if p.get("in") == "formData":
                            form_params[p["name"]] = {
                                "type": p.get("type", "string"),
                                "description": p.get("description", ""),
                                "required": p.get("required", False),
                            }
                            if p.get("type") == "file":
                                form_params[p["name"]]["format"] = "binary"
                    return {"type": "object", "properties": form_params} if form_params else None

            return None

        except (KeyError, AttributeError):
            return None

    def _resolve_reference(self, ref: str) -> dict[str, Any]:
        """Resolve a JSON reference in the OpenAPI spec recursively."""

        def _resolve_nested_refs(schema: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(schema, dict):
                return schema

            resolved = schema.copy()

            # Handle direct reference
            if "$ref" in resolved:
                ref_parts = resolved["$ref"].split("/")
                if ref_parts[1] == "definitions":
                    resolved = self._spec["definitions"][ref_parts[2]].copy()
                elif ref_parts[1] == "components":
                    resolved = self._spec["components"]["schemas"][ref_parts[2]].copy()

            # Recursively resolve nested references
            for key, value in resolved.items():
                if isinstance(value, dict):
                    resolved[key] = _resolve_nested_refs(value)
                elif isinstance(value, list):
                    resolved[key] = [_resolve_nested_refs(item) if isinstance(item, dict) else item for item in value]

            return resolved

        parts = ref.split("/")
        if parts[1] == "definitions":  # OpenAPI 2.0
            initial_schema = self._spec["definitions"][parts[2]]
        elif parts[1] == "components":  # OpenAPI 3.0
            initial_schema = self._spec["components"]["schemas"][parts[2]]
        else:
            raise ValueError(f"Unsupported reference format: {ref}")
        return _resolve_nested_refs(initial_schema)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract API endpoints from Swagger/OpenAPI spec")
    parser.add_argument(
        "--url",
        default="https://petstore.swagger.io",
        help="URL to the OpenAPI documentation",
    )
    parser.add_argument("--endpoints", nargs="+", help="Optional list of specific endpoints to extract")
    parser.add_argument(
        "--try-direct-access",
        action="store_false",
        default=False,
        help="Try direct access to OpenAPI spec before scraping",
    )

    args = parser.parse_args()

    extractor = SwaggerExtractor()
    endpoints = asyncio.run(
        extractor.extract_endpoints(
            args.url,
            endpoint_list=args.endpoints,
            try_direct_access=args.try_direct_access,
        )
    )
    print(endpoints)
