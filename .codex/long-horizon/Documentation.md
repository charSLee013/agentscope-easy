# Documentation

## 当前状态

- 项目状态：已完成
- 当前里程碑：M6 - Trinity / tune 全收口
- 下一步：无新的实现动作；如需继续吸收未来新的 `main` 提交，再开启新一轮
  long-horizon run

## 里程碑状态

- 冻结前地基：已完成
- M1：已完成
- M2：已完成
- M3：已完成
- M4：已完成
- M5：已完成
- M6：已完成

## 决策记录

- 日期：2026-03-14
  - 决策：纯发版/纯素材/纯治理类提交允许跳过
  - 原因：不影响 `easy` 的核心产品目标
- 日期：2026-03-14
  - 决策：`agent/tool -> tracing/config -> ReMe + TTS/audio`
  - 原因：这是冻结后的主推进顺序
- 日期：2026-03-14
  - 决策：`ContextVar` 允许完全切换，`SubAgent` 允许重塑，兼容性允许硬切
  - 原因：本轮目标是有效吸收主干能力，不是保留旧壳
- 日期：2026-03-14
  - 决策：memory 方向只做 `ReMe`，`mem0` 可从主公开面退出
  - 原因：用户已给出单一路线
- 日期：2026-03-14
  - 决策：音频 / `TTS` 能力先行，但播放默认关闭，控制面放在运行时配置层
  - 原因：避免默认副作用和 Agent 级开关继续扩散
- 日期：2026-03-14
  - 决策：docs/examples 第二波推进，docs CI 只执行纯本地示例
  - 原因：先守住 runtime，再避免外部 key 重新进入 CI
- 日期：2026-03-15
  - 决策：继续吸收最后一个核心功能 deferred backlog `9f018b6`
  - 原因：用户要求做到“all done”，而不是停留在记账完成但功能仍延后

## 如何运行与演示

- 安装：仓库现有开发环境
- 启动：从 `easy` 分支按里程碑执行 `main -> easy` 吸收
- 验证：每个里程碑后运行 `validate_long_horizon_docs.py --target .`
- 演示：查看 `source-matrix.md` 与 `easy` 上新增的 squash commits

## 已知问题与后续事项

- 当前 long-horizon 账本已经完整：`easy..main` 的 `82` 条 main-only 提交
  已全部完成台账分类，无漏项。
- docs tutorial 仍保持 `CI` 只执行纯本地示例；需要真实外部 key 的教程脚本
  不会重新进入自动执行链。
- `RayEvaluator` 的原生 Windows 支持已明确切除；支持面保持为 Linux、
  macOS 与 `WSL2`。
- 原先唯一尚未真正吸收的核心功能面是 `9f018b6` 的 `tune` 模块；本轮已把
  它从“后续独立评估”改为当前活跃里程碑并完成吸收。
- 本轮冻结范围内已经不存在核心功能级 `defer-feature` 条目；剩余 M6 条目都
  是明确允许跳过的非核心示例/展示类变更。
- 本轮 proof 只证明当前工作区文件、测试与文档状态，不代替用户后续的
  `git add` / squash commit / PR 操作。

## 最终验证证据

- 最终结果：通过
- finalizer 命令：`python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . --require-path .codex/long-horizon/source-matrix.md --require-path .codex/long-horizon/Prompt.md --require-path .codex/long-horizon/Plan.md --require-path .codex/long-horizon/Implement.md --require-path .codex/long-horizon/Documentation.md --require-path src/agentscope/_run_config.py --require-path src/agentscope/tts/__init__.py --require-path src/agentscope/memory/_reme/__init__.py --require-path src/agentscope/tune/__init__.py --require-path src/agentscope/model/_trinity_model.py --require-path docs/tune/SOP.md --require-path examples/training/react_agent/main.py`
- manifest：`artifacts/final-manifest.json`
- 必需 artifact：`.codex/long-horizon/{Prompt,Plan,Implement,Documentation,source-matrix}.md`、`src/agentscope/_run_config.py`、`src/agentscope/tts/__init__.py`、`src/agentscope/memory/_reme/__init__.py`、`src/agentscope/tune/__init__.py`、`src/agentscope/model/_trinity_model.py`、`docs/tune/SOP.md`、`examples/training/react_agent/main.py`
- 备注：M6 新增训练模块切片的 changed executable coverage 为
  `66/73 = 90.4%`

## 审计日志

- 时间：2026-03-14 01:01
  - 动作：bootstrap long-horizon 工作文档
  - 结果：成功
  - 备注：生成 Prompt/Plan/Implement/Documentation 四份文档
- 时间：2026-03-14 01:20
  - 动作：读取仓库、`main..easy` 差异与 long-horizon skill 参考文档
  - 结果：成功
  - 备注：确认 `main` 相对 `easy` 还有 82 个 main-only 提交
- 时间：2026-03-14 01:38
  - 动作：使用 3 个子代理做批次 triage
  - 结果：成功
  - 备注：确认优先顺序为低风险叶子修复 -> tracing/evaluation -> formatter/model -> toolkit/ReActAgent -> ReMe/TTS
- 时间：2026-03-14 02:02
  - 动作：完成 M1，冻结规格并建立初始 `source-matrix.md`
  - 结果：成功
  - 备注：已运行 `validate_long_horizon_docs.py --target .`
- 时间：2026-03-14 02:18
  - 动作：吸收 `5e0adc3` 的环境变量控制台开关语义
  - 结果：成功
  - 备注：已通过 `pytest -p no:capture tests/agent/test_console_env.py -q`、`ruff check src tests/agent/test_console_env.py`、`pylint -E src`、`pre-commit run --all-files`
- 时间：2026-03-14 02:24
  - 动作：将首批低风险吸收以 squash commit 形式提交到 `easy`
  - 结果：成功
  - 备注：提交 `f7a7890` `sync(main): absorb agent console env toggle`
- 时间：2026-03-14 11:37
  - 动作：吸收 `176d53b` 的 MCP EmbeddedResource 文本资源支持
  - 结果：成功
  - 备注：补充 `tests/mcp_streamable_http_client_test.py` 覆盖文本资源转换
- 时间：2026-03-14 11:41
  - 动作：吸收 `5f62604` 的 Ollama embedding API 更新
  - 结果：成功
  - 备注：补充 `tests/model_ollama_test.py` 锁定 `embed(input=[...])` 调用形态
- 时间：2026-03-14 11:45
  - 动作：从高冲突 toolkit 批次提炼并吸收 `51b6b83` 的 async postprocess 语义
  - 结果：成功
  - 备注：新增 `tests/toolkit_test.py::test_async_postprocess_func`
- 时间：2026-03-14 11:46
  - 动作：增量补全 `source-matrix.md` 的 M2 分类
  - 结果：成功
  - 备注：将多个已等效吸收提交标记为 `skip-equivalent`
- 时间：2026-03-14 11:49
  - 动作：提交 M2 聚合批次到 `easy`
  - 结果：成功
  - 备注：提交 `f2701e4` `sync(main): absorb leaf runtime compatibility fixes`
- 时间：2026-03-14 11:56
  - 动作：吸收 `bd5d926` 的 DashScope formatter 视频提升能力
  - 结果：成功
  - 备注：已通过 `tests/formatter_dashscope_test.py`、`ruff`、`pylint -E`
- 时间：2026-03-14 12:08
  - 动作：吸收 `c245029` 的 evaluation 统计落盘核心语义
  - 结果：成功
  - 备注：新增 `_in_memory_exporter.py`，并通过 `tests/evaluation_test.py`、`pre-commit run --all-files`
- 时间：2026-03-14 12:11
  - 动作：吸收 `d662bec` 的重复工具注册策略核心语义
  - 结果：成功
  - 备注：保留 `easy` 的 `func_name` 行为，并通过 `tests/toolkit_test.py`
- 时间：2026-03-14 12:18
  - 动作：吸收 `8071463` 的 `original_name` 元数据补丁
  - 结果：成功
  - 备注：复用上一批 namesake strategy 逻辑，并通过 `tests/toolkit_test.py`
- 时间：2026-03-14 12:19
  - 动作：补全 `source-matrix.md` 余下未记账提交
  - 结果：成功
  - 备注：`easy..main` 当前 `MISSING 0`
- 时间：2026-03-14 18:36
  - 动作：冻结 long-horizon 新路线并重写工作计划
  - 结果：成功
  - 备注：将主顺序切换为 `agent/tool -> tracing/config -> ReMe + TTS/audio -> docs/examples`
- 时间：2026-03-14 18:36
  - 动作：收齐 3 个 subagent 的 `agent/tool` 冲突分析
  - 结果：成功
  - 备注：确认先吸 `811c127` 的最小 skill runtime，再处理 `23fb3c8/dd05db2` 的兼容层
- 时间：2026-03-14 18:44
  - 动作：吸收 `811c127` 的最小 runtime skill slice
  - 结果：成功
  - 备注：新增 `Toolkit` skill registry / prompt 渲染、`ReActAgent.sys_prompt` skill 注入，以及 `structured_output` 兼容 metadata 回退
- 时间：2026-03-14 18:44
  - 动作：补充 M1 护栏测试并完成本地验证
  - 结果：成功
  - 备注：`unittest` 跑通 `tests.react_agent_test.ReActAgentTest` 与 `tests.toolkit_test.ToolkitTest`，直接执行 `tests/agent/test_subagent_allowlist_schema.py` 新旧两条断言；`ruff`、`pylint -E src`、`pre-commit run --all-files` 全绿
- 时间：2026-03-14 19:29
  - 动作：吸收 `23fb3c8` / `dd05db2` 的最小兼容语义
  - 结果：成功
  - 备注：`ReActAgent` 现支持“先 structured output、再文本回复”的两阶段路径，且会在 reply 结束后重置 finish-tool 扩展 schema
- 时间：2026-03-14 19:29
  - 动作：补齐 SubAgent 模型继承护栏并对齐公开 API
  - 结果：成功
  - 备注：`register_subagent()` 新增 `override_model` 入口；新增默认继承 host.model 与显式 override 两条回归测试
- 时间：2026-03-14 19:44
  - 动作：吸收 `9a6f452` 的 `ContextVar` 配置后端最小语义
  - 结果：成功
  - 备注：新增 `src/agentscope/_run_config.py`、`tests/config_test.py`，保留 `easy` 的 lazy import 与时间戳语义，并通过 `tests.config_test`、`tests.tracer_test`、`tests.init_import_test`
- 时间：2026-03-14 19:44
  - 动作：落地 tracing helper 分层基座
  - 结果：成功
  - 备注：新增 `src/agentscope/tracing/_utils.py`、`_converter.py`、`_extractor.py` 与三组 tracing helper 单测；旧 `tracer_test` 继续通过
- 时间：2026-03-14 23:12
  - 动作：将 tracing 主干 decorator 接到新 extractor/converter 层
  - 结果：成功
  - 备注：`trace_llm`、`trace_reply`、`trace_toolkit` 现同时写新 GenAI attributes 与旧 evaluation 兼容字段；`tests.tracer_test`、`tests.config_test`、`tests.evaluation_test.EvaluatorTest.test_general_evaluator`、`tests.evaluation_test.EvaluatorTest.test_ray_evaluator` 全部通过
- 时间：2026-03-14 23:40
  - 动作：完成 tracing 余下面（`trace_format` / `trace_embedding` /
    generic `trace`）的双写迁移并收口 M2
  - 结果：成功
  - 备注：新增 formatter / embedding / generic extractor helpers，补充真实
    span attrs 单测；`tests.config_test`、`tests.tracing_utils_test`、
    `tests.tracing_converter_test`、`tests.tracing_extractor_test`、
    `tests.tracer_test`、`tests.evaluation_test` 定向全绿，`pre-commit
    run --all-files`、`pylint -E src` 全绿；变更可执行行覆盖率
    `235/241 = 97.5%`
- 时间：2026-03-15 00:10
  - 动作：完成 M3 第一刀，将 audio playback 收敛到运行时配置并吸收
    URL audio 播放能力
  - 结果：成功
  - 备注：新增 `audio_playback_enabled` ContextVar 配置，`AgentBase`
    在默认关闭时跳过音频播放，开启后同时支持 base64 与 URL 音频；
    `tests.config_test`、`tests.agent.test_audio_playback_gate`、
    `tests.tracer_test`、`tests.evaluation_test.EvaluatorTest.test_general_evaluator`
    定向全绿，`pre-commit run --all-files`、`pylint -E src` 全绿；
    变更可执行行覆盖率 `66/73 = 90.4%`
- 时间：2026-03-15 00:15
  - 动作：完成 M3 第二刀，对齐长期记忆基类的 `limit` 检索 contract
  - 结果：成功
  - 备注：`LongTermMemoryBase.retrieve` /
    `retrieve_from_memory` 现显式暴露 `limit: int = 5`，并同步更新
    `docs/memory/SOP.md` 与 contract test；`tests.long_term_memory_base_test`、
    `tests.config_test`、`tests.agent.test_audio_playback_gate`、
    `tests.react_agent_test`、`tests.evaluation_test.EvaluatorTest.test_general_evaluator`
    定向全绿，`pre-commit run --all-files`、`pylint -E src` 全绿；
    当前 M3 累积变更可执行行覆盖率 `68/75 = 90.7%`
- 时间：2026-03-15 00:30
  - 动作：完成 M3 第三刀，吸收 ReMe runtime 核心
  - 结果：成功
  - 备注：新增 `src/agentscope/memory/_reme/` 包、三种 ReMe 长期记忆实现
    和公开导出；`pyproject.toml` 已纳入 `reme-ai>=0.2.0.3` 可选依赖；
    `tests.memory_reme_test` 在不依赖真实 `reme_ai` 安装的前提下覆盖构造、
    context、record/retrieve 与错误路径；`tests.memory_reme_test`、
    `tests.react_agent_test`、`tests.long_term_memory_base_test`、
    `tests.agent.test_audio_playback_gate`、`tests.config_test` 定向全绿
    ，再加上 `tests.init_import_test`、`tests.tracer_test` 与
    `tests.evaluation_test.EvaluatorTest.test_general_evaluator` 组合验证，
    当前累计变更可执行行覆盖率 `668/690 = 96.8%`
- 时间：2026-03-15 01:35
  - 动作：完成 M3 第四刀，吸收 `a000954` 的 TTS runtime 核心与 agent 集成
  - 结果：成功
  - 备注：新增 `src/agentscope/tts/` 公共运行时模块、`agent/_utils.py`
    与三组 provider 单测；`ReActAgent` 现支持 `tts_model`，流式回复会在
    `push()` 与 `synthesize()` 两阶段输出 `speech`，模型自带 `audio`
    时优先透传；`stream_printing_messages(..., yield_speech=True)` 可导出
    语音侧带，`tests.tts_base_test`、`tests.tts_*`、
    `tests.react_agent_test`、
    `tests.pipeline_test`、`tests.agent.test_audio_playback_gate`、
    `tests.init_import_test` 与兼容回归组合验证全绿
- 时间：2026-03-15 01:41
  - 动作：完成 M3 第五刀，按 `ReMe`-only 路线收口 memory 公开面
  - 结果：成功
  - 备注：`src/agentscope/memory/__init__.py` 不再默认导出
    `Mem0LongTermMemory`，`docs/memory/SOP.md` 已将 mem0 重标为遗留内部
    集成；本轮宽回归覆盖 `toolkit`、`tracing`、`evaluation`、memory
    contract 与 import-safe 行为，结果全绿；按 `trace` 对本轮真实改动区间
    与新增文件统计，changed executable coverage 为 `696/742 = 93.8%`
- 时间：2026-03-15 02:06
  - 动作：完成 M4 核心文档第二波
  - 结果：成功
  - 备注：中英文 tutorial 索引已纳入 `task_tts`；`task_tts` 已对齐
    `audio_playback_enabled` 默认关闭与 `speech` 侧带传输语义；
    中英文 `task_long_term_memory` 已重写为 `ReMePersonalLongTermMemory`
    示例，不再引用已经从默认公开面移除的 `Mem0LongTermMemory`；
    `py_compile` 与 `validate_long_horizon_docs.py` 已通过，docs 代码片段未被
    重新带回 CI 执行链
- 时间：2026-03-15 03:08
  - 动作：完成 M5 最终台账收口并重写 `source-matrix.md`
  - 结果：成功
  - 备注：`easy..main` 的 `82` 条 main-only 提交已全部分类完成；
    docs/example/test-only 变更改为明确 `skip-*`，仅保留 `9f018b6`
    作为独立 `defer-feature`
- 时间：2026-03-15 03:08
  - 动作：执行 long-horizon validator 与 finalizer proof loop
  - 结果：成功
  - 备注：`validate_long_horizon_docs.py --target .` 通过；finalizer 已生成
    `artifacts/final-manifest.json`，并校验了五份 long-horizon 文档、
    `src/agentscope/_run_config.py`、`src/agentscope/tts/__init__.py` 与
    `src/agentscope/memory/_reme/__init__.py`
- 时间：2026-03-15 03:25
  - 动作：完成 M6，吸收 `9f018b6` 的 Trinity / tune 模块
  - 结果：成功
  - 备注：新增 `src/agentscope/model/_trinity_model.py`、
    `src/agentscope/tune/`、`docs/tune/SOP.md` 与
    `examples/training/react_agent/`；`agentscope` 顶层 lazy import 已纳入
    `tune`，并补齐 import-safe 护栏测试
- 时间：2026-03-15 03:26
  - 动作：完成 M6 定向验证与覆盖率核对
  - 结果：成功
  - 备注：`./.venv/bin/python -m unittest tests.model_trinity_test
    tests.tune_test tests.init_import_test -v`、`py_compile`、
    `ruff check src tests` 与 `pre-commit run --all-files` 全绿；M6 新增
    切片 changed executable coverage 为 `66/73 = 90.4%`
