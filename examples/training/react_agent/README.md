# Training agent workflows with RL using Trinity-RFT

AgentScope exposes a `tune` interface to train agent workflows with
reinforcement learning. The training entrypoint integrates with
[Trinity-RFT](https://github.com/modelscope/Trinity-RFT) while keeping the
workflow surface close to ordinary AgentScope code.

## Workflow contract

To be trainable, a workflow should have this signature:

```python
from typing import Dict

from agentscope.model import TrinityChatModel


async def workflow_function(task: Dict, model: TrinityChatModel) -> float:
    """Run one task and return a scalar reward."""
```

- `task`: one sample from the training dataset.
- `model`: an OpenAI-compatible client adapter injected by Trinity-RFT.
- return value: a scalar reward for the finished rollout.

## Example

The bundled [main.py](./main.py) demonstrates a simple GSM8K training loop
with:

- `ReActAgent` as the workflow runtime.
- `TrinityChatModel` as the training-time model adapter.
- a structured response model for reward extraction.
- a boxed-answer reward function derived from Trinity-RFT.

## How to run

1. Install Trinity-RFT by following its official installation guide.
2. Adjust [config.yaml](./config.yaml) to match your cluster and model.
3. Start the required Ray cluster.
4. Run:

```bash
python main.py
```

## Notes

- The `tune()` helper imports Trinity-RFT lazily. Importing
  `agentscope.tune` does not require the dependency, but calling `tune()`
  does.
- The training example is intentionally local-only and is not part of docs CI.
