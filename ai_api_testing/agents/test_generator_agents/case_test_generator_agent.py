from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

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


test_case_generator_agent = Agent(
    "openai:gpt-4o-mini",
    name="test_case_generator_agent",
    retries=1,
    result_type=list[TestCase],
)


@dataclass
class TestCaseGeneratorDeps:
    """Dependencies for the test case generator agent."""

    pass


@test_case_generator_agent.system_prompt
def test_case_generator_prompt(ctx: RunContext[TestCaseGeneratorDeps]) -> str:
    """System prompt for the test case generator agent."""
    return """
    Role:
    You are a data refinement and expansion specialist, responsible for ensuring wide parameter coverage and generating realistic, constraint-aware data for API and ML/AI testing. Your task is to take high-level test cases and enrich them by expanding parameter ranges, exploring edge values, and ensuring the data reflects real-world patterns and constraints.

    Objective:

    Expand test cases by generating diverse parameter values, ensuring broad coverage of normal, edge, and extreme conditions.
    Apply realistic data constraints (e.g., date ranges, field dependencies) to avoid infeasible test scenarios.
    Maximize variability across inputs while adhering to domain-specific logic and operational limits.
    Instructions:

    Parameter Expansion:

    For each test case, vary key parameters (e.g., numeric ranges, string lengths, boolean flags).
    Generate values across full ranges, including minimum, maximum, and boundary values.
    Incorporate random sampling where appropriate to introduce variability.
    Constraint Application:

    Ensure expanded data respects logical dependencies (e.g., start_date must precede end_date).
    Reflect real-world limits (e.g., phone numbers must follow local formats, user IDs must be alphanumeric).
    Apply domain-specific constraints (e.g., healthcare data must pass validation rules, financial data must align with regulations).
    Data Types and Formats:

    Generate diverse formats for fields like dates, strings, and numerical values (e.g., ISO dates, various string encodings).
    Vary payload sizes, testing both minimal and maximal inputs.
    Edge and Adversarial Data:

    Create inputs that test unusual conditions (e.g., empty payloads, long strings, nested JSON structures).
    Ensure adversarial data (e.g., special characters, SQL injection patterns) is included to assess API security.
    """
