# Source Matrix

## Summary

- Range: `easy..main`
- Snapshot date: 2026-03-15
- Current main-only commit count: 82
- Ledger coverage: 82 / 82 classified
- Processing rule:
  - `absorb-direct`: low-conflict leaf fix, safe to port directly or near-directly
  - `absorb-fused`: same intent is needed, but must be hand-merged into `easy`
  - `skip-equivalent`: `easy` already has the same effective behavior
  - `skip-nonessential`: version/media/governance/docs/example/test-only commit
  - `defer-feature`: large feature postponed until prerequisites are stable

## Frozen Policies

- Keep `easy` policy boundaries as source of truth.
- Do not re-enable docs example execution in `CI`.
- Do not restore native Windows support for `RayEvaluator`.
- High-conflict files are semantic-port only:
  - `src/agentscope/agent/_react_agent.py`
  - `src/agentscope/tool/_toolkit.py`
  - `src/agentscope/evaluate/_evaluator/_ray_evaluator.py`
  - `src/agentscope/tracing/*`

## Final Ledger

| SHA | Theme | Action | Batch | Reason |
| --- | --- | --- | --- | --- |
| `2af3430` | version bump | `skip-equivalent` | M1 | `easy` is already on `1.0.10` |
| `08be504` | version bump | `skip-equivalent` | M1 | superseded by later version state |
| `2984902` | mem0 pin | `skip-equivalent` | M1 | `easy` already carries the version pin |
| `c2c59e5` | docs build cleanup | `skip-equivalent` | M1 | `easy` docs build scripts already clean outputs |
| `073d16d` | contributing/docs layout | `skip-equivalent` | M1 | `CONTRIBUTING.md` already exists on `easy` |
| `a1e681a` | memory compression example | `skip-equivalent` | M1 | equivalent example already exists on `easy` |
| `2d3cbe7` | copilot repo config | `skip-nonessential` | M1 | repo governance noise for this fork |
| `6c25ef0` | studio GIF refresh | `skip-nonessential` | M1 | media-only change |
| `654921f` | tracing tutorial docs | `skip-nonessential` | M1 | docs-only, not current product blocker |
| `9f7c410` | tutorial refine | `skip-equivalent` | M4 | current tutorial `conf.py` theme/footer state already matches the refined upstream docs presentation |
| `81490c8` | tts tutorial docs | `absorb-fused` | M4 | core TTS tutorial is now indexed and aligned with easy-specific playback gating and speech-side-channel semantics |
| `b56c4dd` | tutorial port fix | `skip-nonessential` | M1 | docs-only, no runtime effect |
| `5c3a770` | MsgHub docstring typo | `skip-equivalent` | M1 | current `MsgHub` docstrings and annotations are already in the corrected state |
| `93938ee` | ReMe docs | `absorb-fused` | M4 | long-term memory tutorial is now rewritten around the ReMe-only public direction on easy |
| `6bc219a` | json repair hardening | `skip-equivalent` | M1 | `_json_loads_with_repair` already matches intent on `easy` |
| `5e0adc3` | agent console env | `absorb-direct` | M2 | single-file leaf behavior missing on `easy`; absorbed in `f7a7890` with test + SOP sync |
| `c8da685` | config timestamp | `skip-equivalent` | M1 | `easy` top-level config path has already moved on |
| `62aa639` | `py.typed` packaging | `skip-equivalent` | M2 | `easy` already ships `src/agentscope/py.typed` and includes it from `pyproject.toml` |
| `141b2c4` | `client_kwargs` unification | `skip-equivalent` | M2 | current model constructors on `easy` already use `client_kwargs` |
| `d2fcea0` | remove `client_args` | `skip-equivalent` | M2 | `easy` has already hard-cut the old `client_args` path |
| `45c63bf` | plan subtask state save | `skip-equivalent` | M2 | current plan state serialization and tests already cover the fix |
| `9954400` | plan notebook idx cast | `skip-equivalent` | M2 | `easy` already coerces string `subtask_idx` to `int` in plan notebook paths |
| `58a4858` | word reader + plan notebook | `skip-equivalent` | M2 | same effective fixes were previously fused into `easy` |
| `a2bf80e` | awaitable plan hooks | `skip-equivalent` | M2 | `PlanNotebook.register_plan_change_hook()` already accepts awaitable hooks in the current easy type surface |
| `176d53b` | MCP embedded text resource | `absorb-direct` | M2 | bounded MCP client fix; absorbed locally with targeted test coverage |
| `5f62604` | Ollama embedding API update | `absorb-direct` | M2 | current `easy` still used old Ollama embeddings API; absorbed locally with mock test |
| `3b67178` | OpenAI delta None guard | `skip-equivalent` | M2 | current OpenAI streaming parser already uses `getattr(choice.delta, "content", None) or ""` and no longer crashes on empty delta payloads |
| `267cea0` | DashScope embedding dimension arg | `skip-equivalent` | M2 | current DashScope text embedding calls already use the correct `dimension` argument name |
| `da5a6e9` | DashScope multimodal api_key | `skip-equivalent` | M2 | current multimodal embedding runtime already injects `api_key` before invoking DashScope |
| `1f1946d` | quiet NLTK download | `skip-equivalent` | M2 | current `TextReader` already downloads `punkt` / `punkt_tab` with `quiet=True` |
| `51b6b83` | toolkit async postprocess | `absorb-fused` | M2 | high-conflict area overall, but async postprocess support was safely extracted and fused as a narrow patch |
| `28547e7` | deprecated `tool_choice` warning | `skip-equivalent` | M2 | `easy` already has equivalent one-time warning / required semantics in model base |
| `c0f2aff` | mem0 integration fix | `skip-nonessential` | M3 | superseded by the frozen `ReMe`-only public direction; `mem0` is now treated as a legacy internal lane |
| `56f6299` | tracing GenAI semantics | `absorb-fused` | M2 | helper layer plus `llm/tool/agent/formatter/embedding/generic` decorators are now wired; `easy` keeps legacy dual-write so evaluation stats stay intact |
| `b840745` | tracing list input | `absorb-fused` | M2 | `_get_agent_messages(list[Msg])` is now covered and the new extractor path is wired into `trace_reply` |
| `7df0148` | otel dependency pin | `skip-equivalent` | M3 | current `easy` `pyproject.toml` already matches the intended OpenTelemetry pin range |
| `c245029` | evaluation metadata | `absorb-fused` | M2 | alignment has been revalidated against the new `config + tracing` slice through both general and ray evaluator tests |
| `f5fdc37` | formatter tool-result images | `skip-equivalent` | M4 | current `easy` formatter stack already carries the same effective image extraction capability |
| `bd5d926` | formatter video promotion | `absorb-fused` | M4 | formatter tree diverged, but the DashScope-specific media promotion delta was safely fused locally |
| `19cba5c` | formatter test ID alignment | `skip-equivalent` | M5 | current formatter unit tests already use the corrected tool-use / tool-result ID pairs consistently |
| `44b6806` | DeepSeek reasoning_content input | `skip-equivalent` | M4 | current DeepSeek formatter already lifts `thinking` blocks into `reasoning_content` for deepseek-reasoner |
| `233915d` | mem0 graphstore case | `skip-equivalent` | M6 | current `easy` mem0 path already contains the graphstore result formatting logic |
| `9a6f452` | config `ContextVar` refactor | `absorb-fused` | M2 | `ContextVar` backend + `init(run_id)` + isolation tests have landed; full call-site cleanup can continue incrementally from the compatibility layer |
| `d662bec` | toolkit duplicate strategies | `absorb-fused` | M1 | already absorbed as part of the agent/tool backbone before the frozen route changed |
| `873cfe2` | toolkit nested `$defs` | `skip-equivalent` | M5 | current `easy` registered tool schema merging already supports the nested `$defs` case |
| `5bc937a` | toolkit meta tool deactivate | `skip-equivalent` | M5 | current toolkit already preserves the intended deactivate/reset semantics |
| `8071463` | toolkit `original_name` | `absorb-fused` | M1 | already absorbed as part of the agent/tool backbone before the frozen route changed |
| `811c127` | Anthropic agent skills | `absorb-fused` | M1 | toolkit skill registry + prompt injection core has now landed on `easy`; docs/examples stay deferred to M4 |
| `d3c0c1d` | knowledge retrieval None filter | `skip-equivalent` | M1 | current ReActAgent knowledge retrieval already filters empty text fragments before joining a list of messages |
| `5a24797` | meta tool registration gate | `skip-equivalent` | M1 | current ReActAgent only registers `reset_equipped_tools` when `enable_meta_tool=True` |
| `7f83c1e` | plan tools vs meta tool split | `skip-equivalent` | M1 | current ReActAgent already separates `plan_notebook` activation from `enable_meta_tool` and only uses `plan_related` when meta tool mode is enabled |
| `f4c6b6f` | structured-output tool choice | `skip-equivalent` | M5 | current `easy` already forces `tool_choice=\"required\"` in the structured-output path |
| `23fb3c8` | structured output refactor | `absorb-fused` | M1 | compatible reply-exit semantics have now landed without removing `generate_response` as a default finish tool |
| `224e8a3` | stream finish tool-use leak | `skip-equivalent` | M1 | current ReActAgent already clones the plain-text reply before converting it into the finish tool call, so streaming prints do not leak the internal `generate_response` tool-use block |
| `34a8a30` | interruption CancelError | `skip-equivalent` | M5 | `easy` current interruption path already raises `CancelledError` on interrupted tool execution |
| `df96805` | `handle_interrupt` params | `skip-equivalent` | M5 | current `easy` `handle_interrupt` signature already reflects the upstream fix |
| `8299e1b` | Windows coding tool utf-8 env | `skip-equivalent` | M5 | current `execute_python_code` runtime already exports `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8`; native Windows remains outside the supported platform target anyway |
| `dd05db2` | memory write timing | `absorb-fused` | M1 | final reply timing is now locked by the compatibility layer and targeted long-term-memory regression tests |
| `4d105b7` | ReMe long-term memory | `absorb-fused` | M3 | ReMe runtime core is now landed on `easy` with personal/task/tool memories and public exports; docs/examples remain deferred |
| `04ece23` | long-term memory limit | `absorb-fused` | M3 | base `LongTermMemoryBase` contract now exposes `limit`; concrete `ReMe` follow-up remains in the same memory wave |
| `c7266f6` | ReMe OpenAI embedding fix | `absorb-fused` | M3 | OpenAI embedding/client base_url normalization and dimensions wiring were included in the landed ReMe base adapter |
| `c7b1ff0` | ReMe short-term memory example | `skip-nonessential` | M6 | the runtime-compatible `reme-ai>=0.2.0.3` and base adapter fixes are already covered elsewhere; the remaining delta is example-heavy and outside the core docs wave |
| `a000954` | TTS support | `absorb-fused` | M3 | `agentscope.tts` runtime core plus `ReActAgent`/pipeline speech transport is now landed; docs/examples stay deferred to M4 |
| `7a61962` | audio playback from URL | `absorb-fused` | M3 | URL audio playback is now landed behind `easy` runtime-config gating; default playback remains off |
| `ca5718d` | stream exception re-raise | `skip-equivalent` | M3 | current `stream_printing_messages()` already re-raises the task exception after flushing queued output, and the pipeline tests cover the error-after-print path |
| `9d4cefa` | stream queue deepcopy | `skip-equivalent` | M3 | current streaming path already deep-copies queued messages and preserves the final chunk scheduling behavior needed by the pipeline |
| `303f0f9` | Qwen-Omni input audio format | `skip-equivalent` | M3 | current OpenAI-compatible model runtime already rewrites base64 audio into the Qwen-Omni-specific format before request dispatch |
| `51145a9` | MsgHub Sequence variance | `skip-equivalent` | M2 | current MsgHub already accepts `Sequence[AgentBase]` and stores a copied participant list |
| `03be75e` | deployment example | `skip-nonessential` | M6 | deployment example assets are absent on easy and remain outside the frozen core runtime / docs CI scope |
| `f8ac994` | planner example refactor | `skip-nonessential` | M6 | meta planner example redesign and asset churn do not affect the frozen runtime objectives for this run |
| `fd1335f` | meta planner example tool_names fix | `skip-equivalent` | M6 | current meta planner example already handles invalid `tool_names` input defensively |
| `1c9d88b` | deep research example response fix | `skip-equivalent` | M6 | current deep research example already carries `max_tool_results_words`, `generate_response` registration, and tool result truncation fixes |
| `340510f` | Alibaba Cloud OAuth MCP example | `skip-equivalent` | M6 | easy already carries an equivalent Alibaba Cloud OAuth MCP integration example under `examples/integration/alibabacloud_api_mcp/` |
| `cb35287` | werewolves example + tutorial copy button | `skip-nonessential` | M6 | the remaining delta is example / tutorial / version churn and is not part of the frozen core runtime target |
| `c635281` | browser-use example await formatter | `skip-equivalent` | M6 | current browser agent example already awaits `self.formatter.format(...)` and no longer hits the old coroutine misuse bug |
| `0864a8d` | werewolves prompt fix | `skip-nonessential` | M6 | pure example prompt wording change, not a core runtime concern |
| `9a0ac21` | word reader | `skip-equivalent` | M6 | the WordReader capability was already fused into `easy` through earlier RAG sync work |
| `e900d9c` | milvus lite store | `skip-equivalent` | M6 | the MilvusLite-backed RAG store is already present on `easy` |
| `9f018b6` | RL `tune` module | `absorb-fused` | M6 | `TrinityChatModel`、`agentscope.tune`、训练示例与 SOP 已按 easy 的 import-safe 和 docs 约束吸收落地 |
| `fa85f38` | docs tutorial build fix | `skip-equivalent` | M1 | the effective studio hook and RAG tutorial fixes already exist on `easy` |
| `3ca8561` | README update news | `skip-nonessential` | M1 | README news does not affect runtime or CI behavior |
| `c7ee6b1` | `uv` package manager support | `skip-nonessential` | M1 | tooling-only packaging workflow churn, not required for `easy` runtime parity |

## Final Notes

- This ledger now covers every `easy..main` commit in the 2026-03-15 snapshot.
- `M6` labels mean "explicitly skipped or separately deferred after review", not
  "still unclassified".
- No core `defer-feature` item remains in this run's frozen scope.
