<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## 📑 Table of Contents

- [AgentScope-easy: Developer-First Multi-Agent Framework](#agentscope-easy-developer-first-multi-agent-framework)
  - [🚀 Why AgentScope-easy?](#-why-agentscope-easy)
  - [✨ Core Philosophy](#-core-philosophy)
    - [Transparency First](#transparency-first)
    - [Architectural Excellence](#architectural-excellence)
  - [🎯 Key Features](#-key-features)
    - [⚡ Real-Time Steering](#-real-time-steering)
    - [Advanced Capabilities](#advanced-capabilities)
  - [🛠️ Feature Matrix](#-feature-matrix)
  - [🚀 Quickstart](#-quickstart)
    - [Installation](#installation)
      - [From Source (recommended)](#from-source-recommended)
    - [Hello AgentScope-easy!](#hello-agentscope-easy)
  - [💡 Advanced Features](#-advanced-features)
    - [Real-Time Steering](#real-time-steering)
    - [Multi-Agent Conversation](#multi-agent-conversation)
  - [🔧 Architecture Overview](#-architecture-overview)
  - [📖 Documentation](#-documentation)
  - [🤝 Acknowledgment](#-acknowledgment)
  - [📄 License](#-license)
  - [📞 Contact](#-contact)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AgentScope-easy: Developer-First Multi-Agent Framework

<p align="center">
  <strong>Fork Notice</strong><br/>
  Thanks to the original authors and community of AgentScope — upstream:
  <a href="https://github.com/agentscope-ai/agentscope">agentscope-ai/agentscope</a>.
  <br/>
  AgentScope-easy is a streamlined variant branched from the AgentScope ecosystem.
  This repository is developed on the <code>easy</code> branch, offering several unique additions while maintaining compatibility with the core AgentScope framework.
</p>

---

## 🚀 Why AgentScope-easy?

**Easy for beginners, powerful for experts** — AgentScope-easy provides a developer-centric approach to multi-agent application development.

## ✨ Core Philosophy

### Transparency First
- **Everything Visible**: Prompt engineering, API invocation, agent building, workflow orchestration — all are visible and controllable for developers.
- **No Deep Encapsulation Magic**: Reject implicit logic and black-box patterns.

### Architectural Excellence
- **Asynchronous Native**: Full embrace of async/await patterns for realtime responsiveness.
- **Multi-Agent Oriented**: Explicit message passing and workflow orchestration designed specifically for multi-agent scenarios.

## 🎯 Key Features

### ⚡ Real-Time Steering
Native support for interruption handling with robust memory preservation.

### Advanced Capabilities
- **Agentic Tools Management**: Tools that can manage other tools dynamically.
- **LEGO-Style Composition**: Every component is modular and independent, enabling flexible agent construction.

## 🛠️ Feature Matrix

| Module | Capabilities | Documentation |
|--------|--------------|----------------|
| **Agent** | ReAct pattern implementation, structured output, parallel tool calling | [Agent Tutorial](https://doc.agentscope.io/tutorial/task_agent.html) |
| **Model** | Async execution, streaming/non-streaming returns, tool calls |
| **Tool** | Tool registration/grouping/JSON-Schema/MCP integration | [Tool Guide](https://doc.agentscope.io/tutorial/task_tool.html) |
| **Pipeline** | Sequential processing, concurrent execution, dynamic message routing | [Pipeline Tutorial](https://doc.agentscope.io/tutorial/task_pipeline.html) |
| **Memory** | Short/long-term memory systems | [Memory Guide](https://doc.agentscope.io/tutorial/task_memory.html) |

## 🚀 Quickstart

### Installation

#### From Source (recommended)
```bash
git clone -b easy https://github.com/charSLee013/agentscope-easy.git
cd agentscope-easy
pip install -e .[dev]
# or
# uv pip install -e .[dev]
```

### Hello AgentScope-easy!

```python
import asyncio
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg

async def main():
    agent = ReActAgent(
        name="Friday",
        sys_prompt="You're a helpful assistant named Friday.",
        model=OpenAIChatModel(model_name="gpt-4o", stream=True),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
    )

    # single round
    reply = await agent(Msg("user", "Hello!", "user"))
    print(reply.get_text_content())

asyncio.run(main())
```

## 💡 Advanced Features

### Real-Time Steering
Native interruption support allows for dynamic conversation control without losing context.

### Multi-Agent Conversation

AgentScope-easy provides comprehensive support for complex multi-agent workflows.

## 🔧 Architecture Overview

AgentScope-easy follows a **modular, composable architecture** with clear separation between framework scaffolding and business logic.

## 📖 Documentation

- **Tutorials**: [Quick Start](https://doc.agentscope.io/tutorial/quickstart_message.html) | [Key Concepts](https://doc.agentscope.io/tutorial/quickstart_key_concept.html)
- **Training Example**: [RL with Trinity-RFT](./examples/training/react_agent/README.md)

## 🤝 Acknowledgment

This project is built upon the foundation of the upstream project:
[AgentScope](https://github.com/agentscope-ai/agentscope).

---

## 📄 License

AgentScope-easy is released under the **Apache License 2.0**.

<p align="center">
  <em>Special thanks to the original AgentScope authors and community for their invaluable contributions to the open-source AI ecosystem.</em>
</p>

<p align="center">
  <a href="https://www.apache.org/licenses/LICENSE-2.0">
    <img src="./assets/images/agentscope_logo.png" alt="AgentScope-easy Logo" width="200" />
  </a>
</p>

## 📞 Contact

Join our community to discuss development, share ideas, and contribute to the evolution of agent-oriented programming.
