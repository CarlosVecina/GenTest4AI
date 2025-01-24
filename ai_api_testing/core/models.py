from typing import Any

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """A test case is a single test scenario that is used to test the API."""

    name: str = Field(description="The name of the test case")
    description: str = Field(description="The description of the test case")
    path: str = Field(description="The path of the test case")
    method: str = Field(description="The method of the test case")
    input_json: dict[str, Any] | list[dict[str, Any]] | None = Field(
        description="The input values for the test case. Should strictly follow the api spec"
    )
    expected_output_prompt: str | None = Field(description="The expected output/behavior of the test case")
    expected_output_json: dict[str, Any] | list[dict[str, Any]] | None = Field(
        description="The expected output/behavior of the test case"
    )
    preconditions: str | None = Field(description="Any relevant preconditions for the test case")


class TestCaseFami(BaseModel):
    """A test case family is a group of test cases that are related to a specific user or service persona."""

    name: str = Field(description="The name of the test case family")
    description: str = Field(description="The description of the test case family")
    test_case_type: str = Field(description="The type of the test case family")
    test_variations: list[str] = Field(description="The variations of the test case family")
