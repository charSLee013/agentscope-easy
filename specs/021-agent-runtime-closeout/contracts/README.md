# Contracts Notes

This batch does not introduce new public API schemas intentionally, but runtime
behavior changed in agent/model interaction points.

Touched behavior surfaces:

- `ReActAgent.reply` / `_reasoning` tool-choice flow
- interruption handling in agent runtime path
- deepresearch example response handling

Contract policy:

- preserve easy package initialization contract (`__init__.py` lazy import);
- avoid pulling in unrelated refactor-only interface changes.
