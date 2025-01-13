from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from ai_api_testing.agents.promp_templates.general_API.api_generator_prompt import API_GENERATOR_PROMPT
from pydantic_ai import Agent, RunContext


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


@dataclass
class TestCaseGeneratorDeps:
    """Dependencies for the test case generator agent."""

    pass


def create_test_case_generator_agent(name: str) -> Agent:
    """Create a test case generator agent."""
    return Agent(
        "openai:gpt-4o-mini",
        name=name,
        retries=1,
        result_type=list[TestCase],
    )


default_test_case_generator_agent = create_test_case_generator_agent("default_test_case_generator_agent")


@default_test_case_generator_agent.system_prompt
def test_case_generator_prompt(ctx: RunContext[TestCaseGeneratorDeps]) -> str:
    """System prompt for the test case generator agent."""
    return API_GENERATOR_PROMPT
