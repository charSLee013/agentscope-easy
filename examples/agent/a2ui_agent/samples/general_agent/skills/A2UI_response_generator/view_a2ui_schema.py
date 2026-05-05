# -*- coding: utf-8 -*-
"""
A2UI Schema Viewer - Tool for viewing A2UI schema.

This module provides a tool for retrieving the complete A2UI schema for
generating UI responses.
"""
from __future__ import annotations

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from .schema.base_schema import A2UI_SCHEMA


async def view_a2ui_schema(
    schema_category: str = "BASE_SCHEMA",
) -> ToolResponse:
    """View the complete A2UI schema for generating UI responses.

    This tool returns the complete A2UI JSON schema that defines all
    available UI components and message types.

    Args:
        schema_category: The category of the schema to view.
            Currently only "BASE_SCHEMA" is available.

    Returns:
        ToolResponse containing the A2UI JSON schema.
    """
    if schema_category == "BASE_SCHEMA":
        content = f"""## A2UI JSON Schema

The following is the complete A2UI schema for generating UI responses:

{A2UI_SCHEMA}

---
Use this schema to construct valid A2UI JSON responses.
"""
    else:
        raise ValueError(f"Invalid schema category: {schema_category}")

    return ToolResponse(content=[TextBlock(type="text", text=content)])
