from typing import Any

from pydantic import BaseModel


class APIEndpoint(BaseModel):
    """API endpoint specification."""

    path: str
    method: str
    request_body: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None
