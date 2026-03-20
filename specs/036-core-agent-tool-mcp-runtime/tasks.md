---

description: "Rebuild core agent/tool + MCP runtime on the new easy trunk"

---

# Tasks: Rebuild core agent/tool + MCP runtime on the new `easy` trunk

**Input**: `specs/036-core-agent-tool-mcp-runtime/spec.md`, `specs/036-core-agent-tool-mcp-runtime/plan.md`
**Base Branch**: `easy`
**Branch**: `036-core-agent-tool-mcp-runtime`

## Constitution Gates (applies to all tasks)

- This wave may not implement `SubAgent`, `RealtimeAgent`, TTS/audio, memory/ReMe, `search`, `web`, or raw text I/O side families.
- Remote `git push` remains user-owned.
- Every major block must end with a read-only subagent review that compares the current diff against `.codex/long-horizon/Prompt.md` and `Plan.md`.
- No production code before a failing test is observed.

## Phase 1: Freeze wave docs (P1)

- [x] T001 Create `.codex/long-horizon/{Prompt,Plan,Implement,Documentation}.md` for this wave.
- [x] T002 Create `specs/036-core-agent-tool-mcp-runtime/{spec,plan,tasks}.md`.
- [x] T003 Record the include/exclude matrix and candidate legacy commits for this wave.
- [x] T004 Validate long-horizon docs with `validate_long_horizon_docs.py`.

---

## Phase 2: Tool/MCP core block (P1)

- [x] T005 Write or port failing tests for toolkit and MCP contracts still missing on current `easy`.
- [x] T006 Run the targeted Tool/MCP tests and observe the intended failures.
- [x] T007 Implement the minimum Tool/MCP runtime changes to make those tests pass.
- [x] T008 Re-run the targeted Tool/MCP tests until green.
- [x] T009 Run a read-only subagent review for the Tool/MCP block and resolve any `fix` findings before continuing.

---

## Phase 3: ReActAgent core block (P1)

- [x] T010 Write or port failing tests for the selected ReActAgent core-loop fixes.
- [x] T011 Run `tests/react_agent_test.py` and observe the intended failures.
- [x] T012 Implement the minimum ReActAgent runtime changes to make those tests pass.
- [x] T013 Re-run `tests/react_agent_test.py` until green.
- [x] T014 Run a read-only subagent review for the ReAct block and resolve any `fix` findings before continuing.

---

## Phase 4: Minimal SOP + closeout (P1)

- [x] T015 Add/update only the minimal `docs/agent/SOP.md`, `docs/tool/SOP.md`, and `docs/mcp/SOP.md` rules needed for long-term truth if they are still missing.
- [x] T016 Run the final targeted test bundle for Tool/MCP + ReAct.
- [x] T017 Run `pre-commit run --all-files`.
- [x] T018 Run the final proof loop with `finalize_long_horizon_run.py`.
- [x] T019 Verify `git status --short` is clean except the intended wave files.
- [x] T020 Commit locally with message: `feat(agent-tool): rebuild core toolkit mcp and react loop on easy`.
