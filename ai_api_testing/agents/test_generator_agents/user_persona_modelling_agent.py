from dataclasses import dataclass

from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext


class UserPersona(BaseModel):
    """A user persona is a group of users that are related to a specific user or service persona."""

    persona_type: str = Field(description="The type of the user persona")
    persona: str = Field(description="The name of the user persona")
    primary_intentions: str = Field(description="The primary intentions of the user persona")
    secondary_intentions: str = Field(description="The secondary intentions of the user persona")


user_modelling_agent = Agent(
    "openai:gpt-4o-mini",
    name="user_modelling_agent",
    retries=1,
    result_type=list[UserPersona],
)


@dataclass
class UserModellingDeps:
    """Dependencies for the user modelling agent."""

    known_users: str


@user_modelling_agent.system_prompt
def user_modelling_prompt(ctx: RunContext[UserModellingDeps]) -> str:
    """System prompt for the user modelling agent."""
    return f"""
    Role:
    You are a strategic analyst tasked with identifying high-level user and service personas that may interact with an API or ML/AI system. Your goal is to surface potential users (both individual and service-level) and their general intentions for engaging with the system. You will work from a mix of known users and inferred personas, expanding the list to ensure diverse representation. The output should guide further development of detailed scenarios and workflows.

    Objective:

    Identify key user personas (e.g., developers, analysts, operators) and service personas (e.g., monitoring services, data ingestion pipelines).
    Capture high-level intentions for each persona, representing their goals and types of interactions.
    Expand known user/service types into broader categories to ensure full-spectrum coverage.
    Distinguish between direct users (interacting directly with the API) and indirect users/services (operating through automated processes or third-party tools).
    Instructions:

    Persona Identification:
    {"The following users are known to interact with the system: " + ctx.deps.known_users if ctx.deps is not None else ''}

    Start with known user types or services that interact with the system.
    Expand the list by identifying adjacent personas or services that share similar goals or operate in overlapping domains.
    Consider both individual personas (e.g., data scientists, IT admins) and automated service personas (e.g., logging pipelines, monitoring tools).
    Intent Mapping:

    For each persona, identify primary intentions (e.g., data retrieval, model evaluation, anomaly detection).
    Include secondary intentions (e.g., performance optimization, adversarial testing) to reflect edge or less common use cases.
    Prioritize diverse goals that span operational, analytical, and exploratory use cases.
    Abstraction Levels:

    Keep intentions broad and conceptual (e.g., "monitor system health," "fetch analytics data").
    Avoid specific API endpoints or technical steps—focus on overarching objectives.
    """
