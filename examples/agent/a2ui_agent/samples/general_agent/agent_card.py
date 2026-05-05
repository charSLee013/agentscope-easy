# -*- coding: utf-8 -*-
"""The agent card definition for the A2A agent."""
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from a2ui.extension.a2ui_extension import get_a2ui_agent_extension

agent_card = AgentCard(
    name="Friday",
    description="A simple ReAct agent that handles input queries",
    url="http://localhost:10002",
    version="1.0.0",
    capabilities=AgentCapabilities(
        push_notifications=False,
        state_transition_history=True,
        streaming=True,
        extensions=[get_a2ui_agent_extension()],
    ),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[
        AgentSkill(
            name="view_a2ui_schema",
            id="view_a2ui_schema",
            description="Retrieve the A2UI JSON schema for validation.",
            tags=["retrieval"],
        ),
        AgentSkill(
            name="view_a2ui_examples",
            id="view_a2ui_examples",
            description="Retrieve A2UI UI template examples.",
            tags=["retrieval"],
        ),
        AgentSkill(
            name="read_text_file",
            id="read_text_file",
            description="Read text from an allowed logical file.",
            tags=["file_viewing"],
        ),
    ],
)
