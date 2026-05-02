# -*- coding: utf-8 -*-
"""
A2UI Example Viewer - Tool for viewing A2UI UI template examples.

This module provides a tool for retrieving A2UI UI template examples.
"""
from __future__ import annotations

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from .UI_templete_examples import (
    SINGLE_COLUMN_LIST_WITH_IMAGE_EXAMPLE,
    TWO_COLUMN_LIST_WITH_IMAGE_EXAMPLE,
    SIMPLE_LIST_EXAMPLE,
    BOOKING_FORM_WITH_IMAGE,
    SEARCH_FILTER_FORM_EXAMPLE,
    CONTACT_FORM_EXAMPLE,
    EMAIL_COMPOSE_FORM_EXAMPLE,
    SUCCESS_CONFIRMATION_WITH_IMAGE_EXAMPLE,
    ERROR_MESSAGE_EXAMPLE,
    INFO_MESSAGE_EXAMPLE,
    ITEM_DETAIL_CARD_EXAMPLE_WITH_IMAGE,
    PROFILE_VIEW_WITH_IMAGE_EXAMPLE,
    SELECTION_CARD_EXAMPLE,
    MULTIPLE_SELECTION_CARDS_EXAMPLE,
)

# Template name to example mapping
TEMPLATE_MAP = {
    "SINGLE_COLUMN_LIST_WITH_IMAGE": SINGLE_COLUMN_LIST_WITH_IMAGE_EXAMPLE,
    "TWO_COLUMN_LIST_WITH_IMAGE": TWO_COLUMN_LIST_WITH_IMAGE_EXAMPLE,
    "SIMPLE_LIST": SIMPLE_LIST_EXAMPLE,
    "BOOKING_FORM_WITH_IMAGE": BOOKING_FORM_WITH_IMAGE,
    "SEARCH_FILTER_FORM_WITH_IMAGE": SEARCH_FILTER_FORM_EXAMPLE,
    "CONTACT_FORM_WITH_IMAGE": CONTACT_FORM_EXAMPLE,
    "EMAIL_COMPOSE_FORM_WITH_IMAGE": EMAIL_COMPOSE_FORM_EXAMPLE,
    "SUCCESS_CONFIRMATION_WITH_IMAGE": SUCCESS_CONFIRMATION_WITH_IMAGE_EXAMPLE,
    "ERROR_MESSAGE": ERROR_MESSAGE_EXAMPLE,
    "INFO_MESSAGE": INFO_MESSAGE_EXAMPLE,
    "ITEM_DETAIL_CARD_WITH_IMAGE": ITEM_DETAIL_CARD_EXAMPLE_WITH_IMAGE,
    "PROFILE_VIEW": PROFILE_VIEW_WITH_IMAGE_EXAMPLE,
    "SELECTION_CARD": SELECTION_CARD_EXAMPLE,
    "MULTIPLE_SELECTION_CARDS": MULTIPLE_SELECTION_CARDS_EXAMPLE,
}


async def view_a2ui_examples(template_name: str):
    """View A2UI UI template examples for generating UI responses.

    Args:
        template_name: Specific template name to load. Available templates:
            - SINGLE_COLUMN_LIST_WITH_IMAGE
            - TWO_COLUMN_LIST_WITH_IMAGE
            - SIMPLE_LIST
            - BOOKING_FORM_WITH_IMAGE
            - SEARCH_FILTER_FORM_WITH_IMAGE
            - CONTACT_FORM_WITH_IMAGE
            - EMAIL_COMPOSE_FORM_WITH_IMAGE
            - SUCCESS_CONFIRMATION_WITH_IMAGE
            - ERROR_MESSAGE
            - INFO_MESSAGE
            - ITEM_DETAIL_CARD_WITH_IMAGE
            - PROFILE_VIEW
            - SELECTION_CARD
            - MULTIPLE_SELECTION_CARDS

    Returns:
        ToolResponse containing the requested template example.
    """
    if not template_name:
        raise ValueError("template_name is required and cannot be empty")
    if template_name not in TEMPLATE_MAP:
        available = ", ".join(sorted(TEMPLATE_MAP.keys()))
        raise ValueError(
            f"Unknown template name: {template_name}. "
            f"Available templates: {available}",
        )

    example = TEMPLATE_MAP[template_name]
    return ToolResponse(content=[TextBlock(type="text", text=f"""## A2UI Template: {template_name}

{example}

---
Adapt this template to your specific data and styling requirements.
""")])
