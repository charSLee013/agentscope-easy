# Prompt

## 项目概述

- 项目名称：agentscope-easy
- 冻结日期：2026-03-14
- 背景：
  - `easy` 是长期维护的独立分支，但本轮同步不再走保守的
    “边界优先/叶子优先” 路线，而是接受主线重构式吸收。
  - 用户已经冻结高冲突决策：先深度合并 `agent/tool`，再全量迁移
    `tracing/config`，最后整合 `ReMe + TTS/audio` 大功能族。
  - 已明确保留的仓库级边界：
    - docs tutorial 在 `CI` 中不执行真实外部示例
    - `RayEvaluator` 不支持原生 Windows，推荐 `WSL2` 或 Linux/macOS
    - `SOP` 仍是 `easy` 的规范源
- 目标用户：
  - 维护 `easy` 的仓库维护者
  - 后续接手执行该长期任务的 Codex/工程师

## 目标

- 逐步把 `main` 相对 `easy` 的 `82` 个 main-only 提交全部记账为：
  - 已直接吸收
  - 已手工融合
  - 已等效覆盖
  - 安全跳过
  - 延后处理
- 在当前真实状态下，将 `--cherry-pick --right-only` 口径下剩余的
  `58` 条未等价吸收提交按子里程碑持续收口
- 每次按可验证子里程碑推进，并以新的 squash commit 方式提交到 `easy`
- 每个批次都必须通过最小必要验证：`pre-commit`、`ruff check src`、
  `pylint -E src` 和相关 `pytest`
- 在前述主干吸收完成后，继续清掉最后保留的新功能 deferred backlog，
  直至本轮 `easy..main` 不再存在需要单独延后的核心功能面

## 非目标

- 不把 docs tutorial 重新带回 `CI` 可执行链
- 不逐个机械 cherry-pick 所有提交
- 不吸收纯版本号、纯素材、纯 README 新闻、纯仓库治理类提交
- 不在未经验证的情况下宣称任何大块功能已完成

## 硬约束

- 性能：
  - 每个里程碑必须控制在一个可验证闭环内
- 平台：
  - `easy` 保持 Linux/macOS 与 `WSL2` 友好
  - 原生 Windows 不作为 `RayEvaluator` 支持目标
- 依赖：
  - 纯发版/纯展示/纯治理提交允许跳过
- 安全 / 合规：
  - 不引入新的 secrets 依赖
  - 不把 docs tutorial 重新带回 `CI` 可执行链
- 其他：
  - 实现层冲突必须先按冻结决策自行消化，不能把可本地裁决的问题
    抛回给用户
  - 每个里程碑后必须更新 `.codex/long-horizon/Documentation.md`
  - 每个里程碑后必须运行
    `validate_long_horizon_docs.py --target .`

## 冻结决策

- `tracing`：走全面迁移
- `agent/tool`：走深度合并
- `big features`：尽量全收
- 推进顺序：先 `agent/tool`，再 `tracing/config`，最后 `memory/tts/audio`
- `ContextVar`：接受完全切换
- 音频/TTS：能力先行，但播放默认关闭
- 播放控制面：放进新的运行时配置层，不做独立 Agent 级开关
- `easy` 特性：允许可重塑，不是硬保留
- `SubAgent`：允许打破重建，但在 `agent/tool` 里程碑结束前必须恢复为
  可运行能力
- 兼容性：允许硬切
- `memory` 方向：只做 `ReMe`
- `mem0` 最终状态：允许从主公开面移除
- 文档波次：核心先行
- docs CI：只执行纯本地示例
- 依赖面：可以进核心

## 交付物

- 主交付物：
  - 一系列经过验证的 `easy` 分支 squash commits
  - `.codex/long-horizon/source-matrix.md`
    作为 `easy..main` 提交吸收台账
- 过程文档：
  - `.codex/long-horizon/Prompt.md`
  - `.codex/long-horizon/Plan.md`
  - `.codex/long-horizon/Implement.md`
  - `.codex/long-horizon/Documentation.md`
- 额外 artifact：
  - 最终 `artifacts/final-manifest.json`

## 完成标准

- `source-matrix.md` 维持全量记账，无漏项
- `--cherry-pick --right-only` 口径下的剩余 main-only 提交全部被处理、
  跳过或纳入明确延后说明
- 本轮冻结目标下不再保留核心功能级 `defer-feature` 条目
- 所有被吸收或融合的批次都形成独立 squash commit
- 每个批次都保留验证证据
- 结束前必须运行 `finalize_long_horizon_run.py`

## 演示路径

- 查看 `.codex/long-horizon/source-matrix.md` 的提交去向
- 查看 `easy` 上按批次形成的 squash commits
- 查看 `Documentation.md` 中每个里程碑的验证证据

## 关键问题与澄清

- 问题：实现中如果 upstream 方案与冻结决策冲突怎么办？
  - 答案：必须本地改写以满足冻结决策，不能把实现层冲突升级为新的
    用户决策点。
- 问题：大功能是否与文档示例同波推进？
  - 答案：否，runtime 与测试先行，文档示例第二波跟进。
- 问题：如果主干收口后仍剩独立大功能 backlog 怎么办？
  - 答案：继续开新里程碑吸收，直到只剩明确允许跳过的非核心项。

## 备注

- 本文件是冻结后的规格说明；如需扩 scope，先更新本文件再更新 `Plan.md`。
- 不允许在收尾阶段删除主交付物或 `Documentation.md`。
