# SOP：`agentscope.browser` 网页抓取浏览器兜底

## 1. 功能定义

- `agentscope.browser` 提供“网页正文抓取”的第一方公共能力。
- 当前公共能力只覆盖：
  - HTTP 快速抓取
  - challenge 特征检测
  - 浏览器级正文抓取兜底
  - 最小 Toolkit 工具接线
- 当前明确不交付：
  - 完整 BrowserAgent / browser automation
  - 点击、截图、表单、登录态管理
  - whitelist / PDF / URL rewrite 绕路

## 2. 文件映射

- `src/agentscope/browser/_service.py`：抓取服务、challenge 检测、Playwright 启动策略与结果对象。
- `src/agentscope/browser/_tools.py`：最小工具函数包装。
- `src/agentscope/browser/__init__.py`：公共导出面。

## 3. 对外规则

- 默认必须先走 HTTP 快速路径；只有命中 challenge / hard failure 才允许切浏览器。
- 浏览器依赖只能作为 optional extra 暴露，不得污染 base install。
- 当前 shipped 浏览器后端为 Playwright；启动时优先尝试系统 Chrome / Edge channel，并兼容 new headless。
- 工具注入方式固定为：
  - `Toolkit.register_tool_function(tool, preset_kwargs={"service": service})`
- `service` 参数不得出现在模型可见 schema 中。
- 本模块工具面只保留 `038` 等集成所需的最小网页抓取能力，不扩成通用 browser toolset。

## 4. 交互调用链

- Host / SubAgent / 调用方 → `BrowserPageService.fetch_page()`
- `BrowserPageService.fetch_page()` → HTTP 快速抓取
- HTTP 命中 challenge → Playwright browser path
- Tool 调用链：`Toolkit` → `fetch_webpage` → `BrowserPageService`

## 5. 验收与守门

- `import agentscope.browser` 可用，且 `import agentscope` 暴露 `browser` 子模块。
- 正常 HTML 页面走 HTTP 快速路径，不额外启动浏览器。
- challenge 页面触发浏览器兜底，缺少 Playwright 时给出安装提示，而不是 import-time 崩溃。
- `tests/browser/test_service.py`、`tests/browser/test_tools.py`、`tests/browser/test_host_wiring.py` 负责守门。
