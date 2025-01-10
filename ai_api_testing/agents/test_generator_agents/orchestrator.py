import asyncio
import json
from asyncio import create_task
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from ai_api_testing.agents.test_generator_agents.case_family_agent import (
    test_case_family_agent,
)
from ai_api_testing.agents.test_generator_agents.case_test_generator_agent import (
    test_case_generator_agent,
)
from ai_api_testing.agents.test_generator_agents.user_persona_modelling_agent import (
    user_modelling_agent,
)
from ai_api_testing.utils.logger import logger
from pydantic_ai import Agent


class AgentStatus(Enum):
    """Status of an agent."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


T = TypeVar("T")


class AgentResult(BaseModel, Generic[T]):
    """Result of an agent."""

    status: AgentStatus
    data: T | list[T] | None = None
    msg: str | None = None


class AgentOrchestrator:
    """Orchestrator for running agents in sequence or parallel."""

    def __init__(self, agents: list[tuple[Agent, dict[str, Any]]]):
        self.agents: list[tuple[Agent, dict[str, Any]]] = agents
        self.results: dict[str, dict[str, AgentResult]] = {}

    async def execute_agent_with_evaluation(
        self,
        agent_tuple: tuple[Agent, dict[str, Any]],
        **kwargs,
    ) -> AgentResult:
        """Execute an agent with evaluation."""
        agent, agent_kwargs = agent_tuple
        logger.info(f"Executing agent: {agent.name}")
        try:
            # Initialize results structure if not exists
            if agent.name not in self.results:
                self.results[agent.name] = {}
                logger.info(f"Initialized results structure for agent: {agent.name}")

            # Track execution under parent agent if it exists
            if "previous_agent" in kwargs:
                parent_key = f"{kwargs['previous_agent'].name}_{kwargs.get('task_id', 'default')}"
                self.results[agent.name][parent_key] = AgentResult(status=AgentStatus.RUNNING)
                logger.info(f"Tracking execution under parent agent: {kwargs['previous_agent'].name}")

            # Execute agent
            if "previous_agent" in kwargs:
                user_prompt = agent_kwargs.get("user_prompt", "") + f"{kwargs['previous_result']}"
                logger.info(f"Running agent with previous result from: {kwargs['previous_agent'].name}")
                result = await agent.run(
                    user_prompt=user_prompt,
                    **{k: v for k, v in agent_kwargs.items() if k != "user_prompt"},
                )
            else:
                logger.info("Running agent without previous result")
                result = await agent.run(**agent_kwargs)

            # Store result
            result_key = f"{kwargs.get('previous_agent', agent).name}_{kwargs.get('task_id', 'default')}"
            self.results[agent.name][result_key] = AgentResult(
                status=AgentStatus.COMPLETED,
                data=result.data,
            )
            logger.info(f"Stored result for key: {result_key}")

            return self.results[agent.name][result_key]

        except Exception as e:
            error_key = f"{kwargs.get('previous_agent', agent).name}_{kwargs.get('task_id', 'default')}"
            self.results[agent.name][error_key] = AgentResult(status=AgentStatus.FAILED, msg=str(e))
            logger.error(f"Error executing agent {agent.name}: {str(e)}")
            raise

    async def run_parallel(self, *args, **kwargs) -> dict[str, AgentResult]:
        """Execute agents in sequence, but parallelize based on list outputs."""
        logger.info("Starting parallel execution of agents")

        async def process_agent_level(
            agent_tuple: tuple[Agent, dict[str, Any]],
            previous_results: list[tuple[str, Any]] | None = None,
            level: int = 0,
        ) -> list[AgentResult]:
            agent_name = agent_tuple[0].name
            logger.info(f"\nProcessing agent level {level} with agent: {agent_name}")
            results = []

            if previous_results is None:
                logger.info(f"Executing first agent: {agent_name}")
                # First agent - single execution
                result = await self.execute_agent_with_evaluation(
                    agent_tuple, task_id=f"level_{level}_task_0", **kwargs
                )
                results.append(("task_0", result))
            else:
                logger.info(f"Processing {len(previous_results)} previous results for agent: {agent_name}")
                # Create tasks for each previous result
                tasks = []
                for task_id, prev_result in previous_results:
                    logger.info(f"Creating task for previous result: {task_id}")
                    task = create_task(
                        self.execute_agent_with_evaluation(
                            agent_tuple,
                            previous_agent=self.agents[level - 1][0],
                            previous_result=prev_result,
                            task_id=f"level_{level}_{task_id}",
                            **kwargs,
                        )
                    )
                    tasks.append((task_id, task))

                # Execute all tasks for this level
                for task_id, task in tasks:
                    try:
                        result = await task
                        results.append((task_id, result))
                        logger.info(f"Completed task: {task_id}")
                    except Exception as e:
                        logger.error(f"Error in task {task_id}: {e}")

            # Prepare results for next level
            expanded_results = []
            for task_id, result in results:
                if result.data:
                    data_list = result.data if isinstance(result.data, list) else [result.data]
                    logger.info(f"Expanding {len(data_list)} results from task: {task_id}")
                    for i, data_item in enumerate(data_list):
                        expanded_results.append((f"{task_id}_subtask_{i}", data_item))

            logger.info(f"Level {level} completed with {len(expanded_results)} expanded results")
            return expanded_results

        # Process each level
        current_results = None
        for level, agent_tuple in enumerate(self.agents):
            logger.info(f"\nStarting level {level} with agent: {agent_tuple[0].name}")
            current_results = await process_agent_level(agent_tuple, previous_results=current_results, level=level)

        logger.info("\nAll levels completed")
        return self.results


if __name__ == "__main__":
    dummy_api_spec = """
        api_spec = {
            "paths": {
                "/pets": {
                    "get": {
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "type": "string",
                                "required": True,
                            }
                        ]
                    },
                    "post": {
                        "operationId": "adoptPet",
                        "parameters": [
                            {
                                "name": "petId",
                                "in": "query",
                                "type": "string",
                                "required": True,
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Pet adoption successful",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {
                                                    "type": "string"
                                                },
                                                "adoptionId": {
                                                    "type": "string"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        }
    """
    orchestrator = AgentOrchestrator(
        [
            (
                user_modelling_agent,
                {"user_prompt": "Generate test cases for API spec: " + str(dummy_api_spec)},
            ),
            (
                test_case_family_agent,
                {"user_prompt": "Generate the test case families for this user persona: "},
            ),
            (
                test_case_generator_agent,
                {"user_prompt": "Expand the test case family of tests: "},
            ),
        ]
    )

    results: dict[str, dict[str, AgentResult]] = asyncio.run(orchestrator.run_parallel())

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tmp_test_cases_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                agent_name: {
                    task_id: {
                        "status": result.status.value,
                        "data": result.data.model_dump(),
                        "msg": result.msg,
                    }
                    for task_id, result in agent_results.items()
                }
                for agent_name, agent_results in results.items()
            },
            f,
            indent=2,
            default=str,
        )

    logger.info(f"\nResults exported to {output_file}")
