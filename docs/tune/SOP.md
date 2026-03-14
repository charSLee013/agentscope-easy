# SOP：src/agentscope/tune 模块

## 一、功能定义（Scope/非目标）
### 1. 设计思路和逻辑
- 为 AgentScope 工作流提供一个最小训练入口，把普通 async workflow
  适配到 Trinity-RFT 的训练执行面。
- 解决两类问题：
  - 校验训练 workflow 的签名，避免不兼容的函数直接进入训练流程。
  - 在不把 `trinity-rft` 变成顶层硬依赖的前提下，把 workflow 和 YAML
    配置交给 Trinity-RFT。
- 保持“桥接层”定位：不实现 RL 算法、不管理数据集、不替代 Trinity-RFT 的
  配置系统。

### 2. 架构设计
```mermaid
graph TD
  WF[workflow(task, model) -> float]
  SIG[_validate_function_signature]
  TUNE[tune()]
  CFG[TuneConfig adapter]
  TRI[Trinity run_stage]
  TM[TrinityChatModel]

  TM --> WF
  WF --> SIG
  SIG --> TUNE
  TUNE --> CFG
  CFG --> TRI
```

### 3. 核心组件逻辑
- `WorkflowType`：定义训练 workflow 的标准函数签名。
- `_validate_function_signature()`：检查函数是否为 async、参数名和类型是否
  匹配 `task` / `model`、返回值是否标注为 `float`。
- `tune()`：
  - 延迟导入 `trinity-rft` 与 `omegaconf`。
  - 校验 workflow 契约。
  - 用 `TuneConfig` 写入 Trinity-RFT 所需的 workflow adapter 配置。
  - 调用 `run_stage()` 启动训练。

### 4. 关键设计模式
- **适配器模式**：把 AgentScope workflow 适配为 Trinity-RFT 的执行配置。
- **延迟导入**：训练依赖只在 `tune()` 调用时才需要存在。
- **契约校验**：运行前通过签名检查尽早失败。

### 5. 其他组件的交互
- **model**：通过 `TrinityChatModel` 为训练 workflow 提供 OpenAI-compatible
  模型接口。
- **agent**：训练 workflow 内部通常构造 `ReActAgent` 等 Agent；`tune`
  模块不介入 agent 执行细节。
- **examples**：`examples/training/react_agent` 展示最小训练路径；示例只做
  本地使用，不进入 docs CI 执行链。
- **第三方系统**：直接依赖 Trinity-RFT 的 `Config`、`run_stage()` 和配置
  规范。

## 二、文件/类/函数/成员变量映射到 src 路径
- `src/agentscope/tune/_workflow.py`
  - `WorkflowType`：训练 workflow 类型别名。
  - `_validate_function_signature(func)`：签名校验函数。
- `src/agentscope/tune/_tune.py`
  - `tune(workflow_func, config_path)`：训练入口。
  - `TuneConfig`：`tune()` 内部配置包装类，用于把 workflow 注入 Trinity。
- `src/agentscope/tune/__init__.py`
  - 导出 `tune` 与 `WorkflowType`。

## 三、关键数据结构与对外接口（含类型/返回约束）
- `WorkflowType = Callable[[Dict, TrinityChatModel], Awaitable[float]]`
  - `task`：训练样本字典。
  - `model`：训练期注入的模型适配器。
  - 返回：标量 reward。
- `tune(workflow_func: WorkflowType, config_path: str) -> None`
  - `workflow_func`：必须满足 `WorkflowType`。
  - `config_path`：Trinity-RFT YAML 配置文件路径。
  - 异常：
    - 缺少 `trinity-rft` / `omegaconf` 时抛 `ImportError`。
    - workflow 契约不匹配时抛 `ValueError`。
    - 配置不合法时抛 `ValueError`。
- `_validate_function_signature(func: Callable) -> bool`
  - 返回 `True/False`，不抛异常；失败原因通过 logger 输出。

## 四、与其他模块交互（调用链与责任边界）
- 典型调用链：
  `examples/training/.../main.py` -> `agentscope.tune.tune()` ->
  `TuneConfig.to_trinity_config()` -> Trinity `run_stage()` -> 用户 workflow
  -> `ReActAgent` / `TrinityChatModel`
- 责任边界：
  - `tune` 只做 bridge，不做 reward 设计和训练调度策略。
  - checkpoint、分布式执行、数据集处理归 Trinity-RFT。
  - workflow 的业务逻辑仍由 AgentScope 用户代码负责。

## 五、测试文件
- 绑定文件：`tests/tune_test.py`、`tests/model_trinity_test.py`、
  `tests/init_import_test.py`
- 覆盖点：
  - workflow 签名校验的正反路径。
  - `TrinityChatModel` 对训练期 client 的适配。
  - `agentscope.tune` 顶层导入不要求 `trinity-rft`。
  - `tune()` 在缺少 Trinity-RFT 时抛出明确错误。
