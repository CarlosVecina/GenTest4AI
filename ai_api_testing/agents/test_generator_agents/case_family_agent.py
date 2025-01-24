from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from ai_api_testing.agents.test_generator_agents.promp_templates.general_API.api_family_prompt import (
    API_FAMILY_PROMPT,
)
from ai_api_testing.core.models import TestCaseFami


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
        result_type=list[TestCaseFami],
    )


default_test_case_family_agent = create_test_case_family_agent(
    "default_test_case_family_agent"
)


@default_test_case_family_agent.system_prompt
def test_case_family_prompt(ctx: RunContext[TestCaseFamilyDeps]) -> str:
    """System prompt for the test case family agent."""
    return API_FAMILY_PROMPT
