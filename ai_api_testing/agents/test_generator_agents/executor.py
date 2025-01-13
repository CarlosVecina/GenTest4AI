import warnings
from typing import Any, Protocol

import numpy as np
from pydantic import BaseModel

from ai_api_testing.agents.test_generator_agents.case_test_generator_agent import (
    TestCase,
)
from ai_api_testing.agents.test_generator_agents.orchestrator import AgentResult

# TODO: decide if include pandas/polars/NamedArrays...
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")


class Predictable(Protocol):
    """Protocol defining required prediction methods for models.

    Methods:
        predict: Makes predictions on input data
        predict_proba: Makes probability predictions on input data
    """

    def predict(self, *args, **kwargs) -> Any: ...
    def predict_proba(self, *args, **kwargs) -> Any: ...


class Executor(BaseModel):
    """Executes test cases against a model to get predictions.

    The Executor takes test cases generated by agents and runs them through a model
    to get predictions. It supports both regular predictions and probability predictions
    through the model's predict() and predict_proba() methods.

    Attributes:
        None

    Methods:
        execute_results: Executes multiple test cases from agent results against a model
        execute: Executes a single test case against a model
    """

    def execute_results(
        self,
        results_dict: dict[str, AgentResult[TestCase]] | list[TestCase],
        model: Any,
        predict_proba: bool = False,
    ) -> dict[str, int | float]:
        executor_output = {}

        if isinstance(results_dict, list):
            try:
                for testcase in results_dict:
                    executor_output[str(testcase.input_json)] = self.execute(testcase, model, predict_proba)
            except AttributeError:
                print("Wrong output input_json")
        try:
            for _, result in results_dict.items():
                for testcase in result.data:
                    executor_output[str(testcase.input_json)] = self.execute(testcase, model, predict_proba)
        except AttributeError:
            print("Wrong output input_json")
        return executor_output

    def execute(
        self,
        test: TestCase,
        model: Predictable,
        predict_proba: bool = False,
        assertion: Any | None = None,
    ) -> np.ndarray:
        if assertion:
            raise NotImplementedError("Assertion not available yet.")

        func = model.predict
        if predict_proba:
            func = model.predict_proba

        return func(np.array(list(test.input_json.values())).reshape(1, -1))