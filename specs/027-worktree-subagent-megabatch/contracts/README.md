# Contracts Notes

This batch intentionally avoids introducing new public API surfaces.

Touched behavior surfaces:

- `ReActAgent` runtime path (`print` yielding and stream state reset)
- plan notebook serialization/test expectations
- formatter/model parsing compatibility (OpenAI/Gemini/tool-result media)
- word reader VML compatibility in RAG

Contract policy:

- keep easy baseline behavior as source of truth when conflict arises;
- absorb only point-fix intent from upstream commits;
- avoid feature/refactor/version-downgrade drift in this batch.
