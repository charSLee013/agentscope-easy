# Contracts Notes

This batch is primarily docs/example/ci/version absorption with some runtime
file touch points. No intentional new public API contract is introduced.

Observed behavioral touch points:

- `src/agentscope/message/_message_base.py`
- `src/agentscope/hooks/_studio_hooks.py`
- `src/agentscope/memory/_reme/*`

Contract policy:

- preserve existing public behavior unless commit intent explicitly requires
  adjustment;
- avoid hidden field/schema additions in tool/message contracts.
