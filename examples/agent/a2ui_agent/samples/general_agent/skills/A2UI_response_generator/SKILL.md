---
name: A2UI_response_generator
description: A skill for retrieving A2UI UI JSON schematics and templates for generating UI responses.
---

# A2UI Response Generation Skill

## Overview

This skill is **essential and must be used before generating A2UI (Agent to UI) JSON responses**. It provides tools for retrieving the A2UI schema and UI templates.

## Tools

### view_a2ui_schema

Loads the complete A2UI schema for validating JSON responses.

**Parameters:**
- `schema_category` (string, optional): Currently only `"BASE_SCHEMA"` is available.

**Usage:**
```
view_a2ui_schema(schema_category="BASE_SCHEMA")
```

### view_a2ui_examples

Loads UI template examples for generating A2UI responses.

**Parameters:**
- `template_name` (string, required): Specific template to load.

**Available templates:**
- `SINGLE_COLUMN_LIST_WITH_IMAGE` - Vertical list with detailed cards (for ≤5 items)
- `TWO_COLUMN_LIST_WITH_IMAGE` - Grid layout with cards (for >5 items)
- `SIMPLE_LIST` - Compact list without images
- `SELECTION_CARD` - Multiple choice questions
- `MULTIPLE_SELECTION_CARDS` - Multiple selection cards in a list
- `BOOKING_FORM_WITH_IMAGE` - Reservation, booking, registration
- `SEARCH_FILTER_FORM_WITH_IMAGE` - Search forms with filters
- `CONTACT_FORM_WITH_IMAGE` - Contact or feedback forms
- `EMAIL_COMPOSE_FORM_WITH_IMAGE` - Email composition forms
- `SUCCESS_CONFIRMATION_WITH_IMAGE` - Success message after action
- `ERROR_MESSAGE` - Error or warning display
- `INFO_MESSAGE` - Informational messages
- `ITEM_DETAIL_CARD_WITH_IMAGE` - Detailed view of single item with image
- `PROFILE_VIEW` - User or entity profile display

**IMPORTANT**: Always use the **exact template names** listed above. Do NOT use generic terms like 'list' or 'form' - they are NOT valid template names.

**Usage:**
```
view_a2ui_examples(template_name="SINGLE_COLUMN_LIST_WITH_IMAGE")
```

## Workflow

1. Call `view_a2ui_schema` to get the JSON schema for validation
2. Call `view_a2ui_examples` to get appropriate templates for your content
3. Use the schema and templates to construct your A2UI JSON response

## A2UI Response Format

Output your A2UI response as text with two parts separated by `---a2ui_JSON---`:

1. **Conversational response**: Your natural language reply
2. **A2UI JSON**: A raw JSON array of A2UI message objects

```
[Your conversational response here]

---a2ui_JSON---
[
  { "beginRendering": { ... } },
  { "surfaceUpdate": { ... } },
  { "dataModelUpdate": { ... } }
]
```

**Important**: The JSON must conform to the A2UI schema loaded in Step 1.
