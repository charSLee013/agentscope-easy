# Browser fallback selection and validation report

## 0. 状态

- 状态：已运行
- 波次：`039-fetch-browser-fallback`
- 最终结论：部分通过（实现与真实抓取已通过；最终 closeout 仍待 finalizer）

## 1. 背景

- `038` 中对 OpenAI 官方 HTML 的 `urllib` 抓取被 Cloudflare challenge
  拦截并持续返回 `403`。
- 本报告记录本波次的选型、实现与真实验证结果。

## 2. 冻结约束

- 禁止 PDF/白名单绕路
- `Lightpanda-first`
- `Playwright` 作为稳定性对照 / 兜底
- 浏览器依赖保持 optional extra 边界

## 3. 选型结果

- `requests` 对 OpenAI 官方 HTML 持续返回 `403 cloudflare`，正文中包含
  `cdn-cgi/challenge-platform`，无法作为稳定路径。
- `Lightpanda` 官方 Node 包在当前环境下对 `example.com` 与 OpenAI 文章页
  都稳定 `OperationTimedout`，不具备本波次交付条件。
- `Playwright` 自带 bundled Chromium 在当前环境也无法稳定联网，但系统
  Chrome / Edge channel 配合 new headless 与基础 anti-detection 配置后，
  能真实抓到 OpenAI 正文。
- 结论：本波次 shipped backend 选 `Playwright`；`Lightpanda-first`
  只保留为选型探索结论，不进入当前 shipped runtime。

## 4. 实现结果

- 新增 `src/agentscope/browser/`：
  - `BrowserPageService`
  - `BrowserFetchResult`
  - `fetch_webpage`
- 新增 `docs/browser/SOP.md`，把长期稳定规则写入 SOP。
- `pyproject.toml` 新增 `browser` optional extra，并保持其不进入 `full`，
  只进入 `dev`。
- `import agentscope` 现在暴露 `browser` 子模块，但 Playwright 依赖仍延迟
  到实际浏览器抓取路径才导入。
- `specs/038-subagent-v1-field-validation/run_field_validation.py` 已改为通过
  公共 browser 能力抓取 OpenAI 官方页，不再保留内嵌 `urllib` 方案。

## 5. 真实验证结果

- `specs/039-fetch-browser-fallback/browser_runtime_validation.py` 已成功：
  - OpenAI official article：`status=200`，`fetch_mode=browser`，
    `backend=playwright:chrome`
  - Anthropic official article：`status=200`，`fetch_mode=http`
- `artifacts/browser_runtime_validation/summary.json` 已落盘。
- `specs/038-subagent-v1-field-validation/run_field_validation.py --mode full`
  已成功，`038` 报告 verdict 为 `通过`。
- 在真实回归过程中额外修复了两条 integration root cause：
  - wheel sandbox 子进程会被外层 `PYTHONPATH` 污染，导致 pip 误判
    `agentscope` 已安装；现已在 harness subprocess 边界显式移除
    `PYTHONPATH` / `PYTHONHOME`
  - Playwright Sync API 不能直接在 async tool loop 中调用；现已在公共
    tool 层与 `038` 适配层统一改为 `asyncio.to_thread(...)`

## 6. 风险与后续

- 本波次尚未覆盖 timeout / 429 / 限流专项验证。
- 当前 shipped browser backend 仍依赖本机存在可用的 Chrome / Edge /
  或可联网的 Playwright browser runtime；后续若要进一步降低前置条件，
  可单开波次继续评估 `Lightpanda` 或其他 remote-browser 方案。
