# -*- coding: utf-8 -*-
"""Train a ReAct agent with Trinity-RFT reinforcement learning."""
from __future__ import annotations

import os
from typing import Dict

from pydantic import BaseModel, Field
from trinity.common.rewards import MathBoxedRewardFn

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg
from agentscope.model import TrinityChatModel
from agentscope.tune import tune


class GSM8KResponseStructure(BaseModel):
    """Structured response for GSM8K-style tasks."""

    result: str = Field(
        description=(
            "Your solution to the math problem. Put the final answer in "
            "boxed format, e.g. \\boxed{42}."
        ),
    )


class GSM8KRewardFn(MathBoxedRewardFn):
    """Reward function for GSM8K."""

    def __call__(
        self,
        response: Dict,
        truth: str,
        format_score_coef: float = 0.1,
        **kwargs: Dict,
    ) -> dict[str, float]:
        """Calculate the reward based on response and ground truth."""
        if isinstance(truth, str) and "####" in truth:
            truth = truth.split("####")[1].strip()
        else:
            truth = str(truth)

        return super().__call__(
            response=response["result"],
            truth=truth,
            with_think=False,
            format_score_coef=format_score_coef,
            **kwargs,
        )


async def run_react_agent(task: Dict, model: TrinityChatModel) -> float:
    """Solve one task and return a scalar reward."""
    agent = ReActAgent(
        name="react_agent",
        sys_prompt=(
            "You are an agent specialized in solving math problems with "
            "tools. You may write and execute Python code to verify the "
            "answer. Return the final answer within \\boxed{{}}."
        ),
        model=model,
        enable_meta_tool=True,
        formatter=OpenAIChatFormatter(),
    )
    response = await agent.reply(
        msg=Msg("user", task["question"], role="user"),
        structured_model=GSM8KResponseStructure,
    )
    reward = GSM8KRewardFn()(
        response=response.metadata,
        truth=task["answer"],
    )
    return sum(reward.values())


if __name__ == "__main__":
    tune(
        workflow_func=run_react_agent,
        config_path=os.path.join(
            os.path.dirname(__file__),
            "config.yaml",
        ),
    )
