# Plan

## 计划摘要

- 目标：
  - 按冻结决策持续把 `main -> easy` 的剩余 runtime 差异收进 `easy`
  - 用少量高价值 squash commits 吃掉高冲突主干，而不是继续碎步叶子修补
- 当前阶段：
  - M7 `Closeout fixups（已完成）`

## 前置说明

- `easy` 上已有的低风险 runtime/formatter/evaluation 吸收提交视为
  “冻结前地基”，不再作为当前主线里程碑顺序的约束。
- `source-matrix.md` 里这部分历史条目保留原始吸收记录；从当前起，
  活跃 backlog 按新的 M1/M2/M3 顺序推进。

## 架构意图

- 使用“记账 + 分批吸收 + 每批独立验证 + squash commit”的模式推进。
- `easy` 是主线；吸收方向始终是 `main -> easy`，允许同作用逻辑重塑与硬切。
- `agent/tool`、`tracing/config`、`memory/tts/audio` 三条主干都按语义移植
  处理，不做机械 cherry-pick。
- `docs tutorial` 不重新进入需要真实外部 key 的 CI 执行链。
- 原生 Windows 不作为 `RayEvaluator` 支持目标；Linux/macOS/WSL2 为支持面。

## 里程碑

### M1 - Agent / Tool 深度合并

- 目标：
  - 先把 `Toolkit` / `ReActAgent` / `SubAgent` 这一层合并到冻结决策上
  - 优先吸收 `811c127` 的 skill registry + prompt 注入最小核心
  - 在不破坏 `generate_response` 常驻语义的前提下，补 structured output
    / memory timing 兼容层
  - 按新 backbone 重建 `SubAgent` 集成护栏
- 验收标准：
  - `Toolkit` 支持 agent skill registry 与 prompt 渲染
  - `ReActAgent.sys_prompt` 能拼接 skill prompt
  - structured output 和 static long-term-memory timing 有回归测试护栏
  - `SubAgent` 现有 typed contract / allowlist / finish tool 假设不回退
- 验证命令：
  - `./.venv/bin/python -m pytest tests/toolkit_test.py tests/react_agent_test.py tests/agent/test_subagent_allowlist_schema.py -q`
  - `./.venv/bin/python -m ruff check src tests`
  - `./.venv/bin/python -m pylint -E src`
  - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - `ReActAgent` / `Toolkit` / `SubAgent` 共用同一冲突面，稍不注意就会打掉
    `finish tool` 或 typed contract 的现有测试红线。

### M2 - Tracing / Config 全量迁移

- 目标：
  - 完成 `ContextVar` 运行时配置切换
  - 迁移 tracing GenAI semantic conventions
  - 让 evaluation 已落地统计能力回到新的 tracing/config 主线之上
- 验收标准：
  - `ContextVar` 切换完成且调用链稳定
  - tracing / evaluation 语义在新配置层下通过定向验证
- 验证命令：
  - `./.venv/bin/python -m pytest tests/tracer_test.py tests/evaluation_test.py -q`
  - `./.venv/bin/python -m ruff check src tests`
  - `./.venv/bin/python -m pylint -E src`
  - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
- 风险：
  - tracing 和 config 是跨模块地基，迁移不完整会让之前已吸收的 evaluation
    增量重新飘移。

### M3 - ReMe + TTS / Audio

- 目标：
  - 只保留 `ReMe` 作为 memory 主方向
  - 处理 `TTS` / 音频能力，并把播放开关收敛到运行时配置层
  - 允许 `mem0` 从主公开面退出
- 验收标准：
  - `ReMe` runtime 能力和测试闭环成立
  - 音频 / `TTS` 默认不播放，但运行时配置开启后可工作
  - `mem0` 暴露面与 frozen 决策一致
- 验证命令：
  - 对应 memory / audio / tts 定向 `pytest`
  - `./.venv/bin/python -m ruff check src tests`
  - `./.venv/bin/python -m pylint -E src`
  - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
- 风险：
  - 这是功能体量最大的批次，若不坚持 runtime-config 播放门控，很容易把
    `easy` 当前行为重新搞脆。

### M4 - Docs / Examples 第二波

- 目标：
  - 只补 runtime 已落地能力对应的核心文档与示例
  - 保持 docs CI 只执行纯本地示例
- 验收标准：
  - 文档与 runtime 当前能力一致
  - docs CI 不要求真实外部 key
- 验证命令：
  - docs 相关定向命令
  - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
- 风险：
  - 示例一旦重新混入外部依赖执行链，就会把已经清掉的 CI 不稳定性带回来。

### M5 - 收口与最终证明

- 目标：
  - 完成 `source-matrix.md` 的最终记账
  - 跑完 long-horizon finalizer 并生成 manifest
- 验收标准：
  - 活跃 backlog 全部吸收、等效覆盖、延后或跳过并有理由
  - `Documentation.md` 和 `source-matrix.md` 与真实仓库状态一致
  - finalizer 成功
- 验证命令：
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . --require-path .codex/long-horizon/source-matrix.md --require-path .codex/long-horizon/Prompt.md --require-path .codex/long-horizon/Plan.md --require-path .codex/long-horizon/Implement.md --require-path .codex/long-horizon/Documentation.md`
- 风险：
  - 任何一条台账漂移都会让最终证明失真。

### M6 - Trinity / Tune 全收口

- 目标：
  - 吸收 `9f018b6` 的 `TrinityChatModel` 与 `agentscope.tune` 模块
  - 让本轮 `source-matrix.md` 不再保留核心功能级 `defer-feature`
  - 在不破坏当前 import-safe 和 docs/SOP 约束的前提下补齐训练示例与文档
- 验收标准：
  - `agentscope.model` 导出 `TrinityChatModel`
  - `agentscope.tune` 可被安全导入，缺少 `trinity-rft` 时只在真正调用
    `tune()` 时抛出明确错误
  - `docs/SOP.md` 与新增 `docs/tune/SOP.md` 对齐模块契约
  - `source-matrix.md` 中 `9f018b6` 不再是 `defer-feature`
- 验证命令：
  - `./.venv/bin/python -m pytest tests/model_trinity_test.py tests/tune_test.py tests/init_import_test.py -q`
  - `./.venv/bin/python -m ruff check src tests`
  - `./.venv/bin/python -m pylint -E src`
  - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - 训练模块引入新的顶层导出与示例面，若 import-safe 处理不对，会把
    `agentscope` 顶层导入重新搞脆。

### M7 - Closeout fixups

- 目标：
  - 修复吸收后暴露出的真实 correctness gaps，而不回退已落地主干方向
  - 纠正 long-horizon proof 提前宣告完成的问题
- 验收标准：
  - streaming tracing 为 LLM/tool span 写入正确的专有 response attrs
  - `tune` workflow 校验改为语义契约校验
  - OpenAI/Gemini TTS 流式输出统一为累计 payload，最后一个有内容块
    `is_last=True`
  - long-horizon 文档与 final proof 回到真实状态
- 验证命令：
  - `./.venv/bin/python -m pytest tests/tracer_test.py tests/tracing_converter_test.py tests/tracing_extractor_test.py tests/tracing_utils_test.py tests/config_test.py tests/evaluation_test.py tests/tune_test.py tests/model_trinity_test.py tests/init_import_test.py tests/tts_base_test.py tests/tts_openai_test.py tests/tts_gemini_test.py tests/react_agent_test.py tests/pipeline_test.py tests/agent/test_audio_playback_gate.py -q`
  - `./.venv/bin/python -m ruff check src tests`
  - `./.venv/bin/python -m pylint -E src`
  - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . --require-path .codex/long-horizon/source-matrix.md --require-path .codex/long-horizon/Prompt.md --require-path .codex/long-horizon/Plan.md --require-path .codex/long-horizon/Implement.md --require-path .codex/long-horizon/Documentation.md`
- 风险：
  - 若只修代码不重跑 proof，会继续保留错误的“已完成”结论。

## Stop-and-fix 规则

- 任一里程碑验证失败时，先修复并重新验证，再继续后续工作。
- 若关键工作文档或主交付物消失，立即停止并将该次运行判为失败。

## 最终收口

- 先把 `Documentation.md` 更新到真实最终状态。
- 再运行 `finalize_long_horizon_run.py` 校验四文档与必需 artifact。
- 只有 finalizer 成功并生成 manifest，才能声明运行成功。

## 决策记录

- 决策：纯发版/纯素材/纯治理/纯 README 新闻类提交默认允许跳过
  - 原因：这类提交不影响 `easy` 的核心运行时目标
- 决策：`agent/tool` 先于 `tracing/config`，`tracing/config` 先于 `ReMe + TTS/audio`
  - 原因：这是用户冻结的主推进顺序
- 决策：`SubAgent` 允许重塑，但 typed contract、allowlist 和 finish tool 护栏必须保住
  - 原因：用户允许深合并，但不接受无边界回退
- 决策：播放控制面只放在运行时配置层，默认关闭
  - 原因：能力先行，但要避免默认副作用

## 未决问题

- 无新的产品决策未决项；后续实现层冲突按冻结决策本地消化。
