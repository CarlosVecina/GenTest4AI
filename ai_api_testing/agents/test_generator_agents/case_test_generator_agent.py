from dataclasses import dataclass

from ai_api_testing.agents.test_generator_agents.promp_templates.general_API.api_generator_prompt import (
    API_GENERATOR_PROMPT,
)
from ai_api_testing.core.models import TestCase
from pydantic_ai import Agent, RunContext


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
