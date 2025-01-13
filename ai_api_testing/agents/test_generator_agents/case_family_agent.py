from dataclasses import dataclass

from pydantic import BaseModel, Field

from ai_api_testing.agents.promp_templates.general_API.api_family_prompt import (
    API_FAMILY_PROMPT,
)
from pydantic_ai import Agent, RunContext


class TestCaseFamily(BaseModel):
    """A test case family is a group of test cases that are related to a specific user or service persona."""

    name: str = Field(description="The name of the test case family")
    description: str = Field(description="The description of the test case family")
    test_case_type: str = Field(description="The type of the test case family")
    test_variations: list[str] = Field(description="The variations of the test case family")


@dataclass
class TestCaseFamilyDeps:
    """Dependencies for the test case family agent."""

    pass


def create_test_case_family_agent(name: str) -> Agent:
    """Create a test case family agent."""
    return Agent(
        "openai:gpt-4o-mini",
        name=name,
        retries=1,
        result_type=list[TestCaseFamily],
    )


default_test_case_family_agent = create_test_case_family_agent("default_test_case_family_agent")


@default_test_case_family_agent.system_prompt
def test_case_family_prompt(ctx: RunContext[TestCaseFamilyDeps]) -> str:
    """System prompt for the test case family agent."""
    return API_FAMILY_PROMPT
