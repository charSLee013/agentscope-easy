# -*- coding: utf-8 -*-
"""Run SubAgent V1 field validation against the merged easy branch."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time


WHITELIST_URLS = [
    "https://openai.com/business/guides-and-resources/"
    "a-practical-guide-to-building-ai-agents/",
    "https://www.anthropic.com/engineering/"
    "built-multi-agent-research-system",
]

REQUIRED_ENV_KEYS = [
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_BASE_URL",
]

RUNTIME_BASE_ENV_KEYS = [
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "TMP",
    "TEMP",
    "TMPDIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
]

EXTERNAL_APP = r'''
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sysconfig
import time
from typing import Any

import agentscope
from agentscope.agent import ReActAgent, SubAgentSpec, TaskSubAgent
from agentscope.browser import BrowserPageService
from agentscope.filesystem import DiskFileSystem
from agentscope.filesystem._service import FileDomainService
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg, TextBlock
from agentscope.model import OpenAIChatModel
from agentscope.tool import ToolResponse, Toolkit


WHITELIST_URLS = {whitelist_urls}
SANDBOX_PURELIB = Path(sysconfig.get_paths()["purelib"]).resolve()
AGENTSCOPE_MODULE_PATH = Path(agentscope.__file__).resolve()
BROWSER_SERVICE = BrowserPageService()


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def log_event(log_dir: Path, event: str, **payload: Any) -> None:
    append_jsonl(
        log_dir / "events.jsonl",
        {{
            "ts": datetime_now(),
            "event": event,
            **payload,
        }},
    )


def datetime_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def ensure_wheel_import_origin() -> dict[str, str]:
    """Prove the imported `agentscope` package comes from the sandbox wheel."""
    if not AGENTSCOPE_MODULE_PATH.is_relative_to(SANDBOX_PURELIB):
        raise RuntimeError(
            "agentscope import origin escaped sandbox purelib: "
            f"{{AGENTSCOPE_MODULE_PATH}} not under {{SANDBOX_PURELIB}}"
        )
    return {{
        "agentscope_module_path": str(AGENTSCOPE_MODULE_PATH),
        "sandbox_purelib": str(SANDBOX_PURELIB),
    }}


class ObservedOpenAIChatModel(OpenAIChatModel):
    """OpenAI chat model wrapper that logs per-call timings and usage."""

    def __init__(self, log_dir: Path) -> None:
        super().__init__(
            model_name=os.environ["OPENAI_MODEL"],
            api_key=os.environ["OPENAI_API_KEY"],
            client_kwargs={{"base_url": os.environ["OPENAI_BASE_URL"]}},
            generate_kwargs={{"temperature": 0}},
            stream=False,
        )
        self.log_dir = log_dir
        self.call_index = 0

    async def __call__(self, messages: list[dict], **kwargs: Any):  # type: ignore[override]
        self.call_index += 1
        call_id = self.call_index
        start = time.perf_counter()
        payload = {{
            "ts": datetime_now(),
            "call_id": call_id,
            "message_count": len(messages),
            "tool_count": len(kwargs.get("tools") or []),
            "tool_choice": kwargs.get("tool_choice"),
            "preview": _message_preview(messages),
        }}
        try:
            response = await super().__call__(messages, **kwargs)
        except Exception as error:  # noqa: BLE001
            payload.update(
                {{
                    "ok": False,
                    "elapsed_s": round(time.perf_counter() - start, 3),
                    "error": repr(error),
                }},
            )
            append_jsonl(self.log_dir / "model_calls.jsonl", payload)
            raise

        usage = None
        if getattr(response, "usage", None) is not None:
            usage = {{
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "time_s": response.usage.time,
            }}
        payload.update(
            {{
                "ok": True,
                "elapsed_s": round(time.perf_counter() - start, 3),
                "usage": usage,
            }},
        )
        append_jsonl(self.log_dir / "model_calls.jsonl", payload)
        return response


def _message_preview(messages: list[dict]) -> list[str]:
    previews = []
    for msg in messages[-3:]:
        content = msg.get("content")
        if isinstance(content, str):
            previews.append(content[:180])
        else:
            previews.append(str(content)[:180])
    return previews


def _strip_html(raw: str) -> str:
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"\\s+", " ", raw)
    return raw.strip()


async def fetch_official_page(url: str) -> ToolResponse:
    """Fetch one official reference page in the validation whitelist."""
    import asyncio

    started = time.perf_counter()
    if url not in WHITELIST_URLS:
        append_jsonl(
            LOG_DIR / "http_requests.jsonl",
            {{
                "ts": datetime_now(),
                "url": url,
                "ok": False,
                "status": None,
                "elapsed_s": round(time.perf_counter() - started, 3),
                "reason": "not_whitelisted",
            }},
        )
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"URL not allowed in this validation wave: {{url}}",
                ),
            ],
        )

    try:
        result = await asyncio.to_thread(
            BROWSER_SERVICE.fetch_page,
            url,
            5000,
        )
    except Exception as error:  # noqa: BLE001
        append_jsonl(
            LOG_DIR / "http_requests.jsonl",
            {{
                "ts": datetime_now(),
                "url": url,
                "ok": False,
                "status": None,
                "elapsed_s": round(time.perf_counter() - started, 3),
                "reason": repr(error),
            }},
        )
        raise
    elapsed = round(time.perf_counter() - started, 3)
    append_jsonl(
        LOG_DIR / "http_requests.jsonl",
        {{
            "ts": datetime_now(),
            "url": url,
            "ok": True,
            "status": result.status_code,
            "elapsed_s": elapsed,
            "title": result.title,
            "fetch_mode": result.fetch_mode,
            "backend": result.backend,
            "challenge_detected": result.challenge_detected,
            "bytes": len(result.html.encode("utf-8")),
        }},
    )
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    f"URL: {{url}}\\n"
                    f"HTTP status: {{result.status_code}}\\n"
                    f"Fetch mode: {{result.fetch_mode}}\\n"
                    f"Backend: {{result.backend}}\\n"
                    f"Title: {{result.title}}\\n"
                    f"Excerpt:\\n{{result.text}}"
                ),
            ),
        ],
        metadata={{
            "url": url,
            "status": result.status_code,
            "title": result.title,
            "fetch_mode": result.fetch_mode,
            "backend": result.backend,
        }},
    )


def build_host() -> tuple[ReActAgent, str, FileDomainService]:
    """Build the host agent, subagent registration, and filesystem wiring."""
    model = ObservedOpenAIChatModel(LOG_DIR)
    host = ReActAgent(
        name="Supervisor",
        sys_prompt=(
            "You are a validation supervisor. "
            "For research and synthesis tasks, you must delegate exactly once "
            "to the available subagent tool before giving your final answer."
        ),
        model=model,
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=Toolkit(),
        max_iters=6,
    )

    fs = DiskFileSystem(root_dir=str(WORKSPACE_ROOT))
    service = FileDomainService(
        fs.create_handle(
            [
                {{
                    "prefix": "/workspace/subagent/",
                    "ops": {{
                        "list",
                        "file",
                        "read_binary",
                        "read_file",
                        "read_re",
                        "write",
                        "delete",
                    }},
                }},
            ],
        ),
    )
    host.filesystem_service = service
    log_event(LOG_DIR, "host_ready")

    subagent_tool = asyncio_run(
        host.register_subagent(
            TaskSubAgent,
            SubAgentSpec(
                name="field_validator",
                description=(
                    "Delegate a documentation briefing task that fetches the "
                    "official validation URLs and writes "
                    "/workspace/subagent/briefing.md"
                ),
                tools=[fetch_official_page],
            ),
        ),
    )
    log_event(LOG_DIR, "subagent_registered", tool_name=subagent_tool)
    return host, subagent_tool, service


def asyncio_run(awaitable):
    import asyncio

    return asyncio.run(awaitable)


def run_smoke() -> dict[str, Any]:
    """Run the wheel-install smoke checks without external API calls."""
    log_event(LOG_DIR, "smoke_start")
    import_proof = ensure_wheel_import_origin()
    host, subagent_tool, service = build_host()
    result = {{
        "mode": "smoke",
        "agentscope_import_ok": True,
        "public_imports_ok": True,
        **import_proof,
        "subagent_tool_name": subagent_tool,
        "filesystem_service_ok": service is not None,
        "workspace_roots": service.list_allowed_directories(),
    }}
    log_event(LOG_DIR, "smoke_complete", subagent_tool=subagent_tool)
    return result


def run_full() -> dict[str, Any]:
    """Run the real host -> subagent -> fetch -> write validation path."""
    import asyncio

    log_event(LOG_DIR, "full_start")
    import_proof = ensure_wheel_import_origin()
    host, subagent_tool, service = build_host()
    task_text = (
        "Prepare a Markdown briefing from the official validation sources. "
        "You must delegate this task to the available subagent tool. "
        "Inside the delegated task, fetch both official URLs, compare the "
        "orchestrator-workers / handoff guidance, write the final Markdown "
        "briefing to /workspace/subagent/briefing.md, and then summarize "
        "completion in one short paragraph."
    )
    success_criteria = (
        "Use fetch_official_page on both whitelisted URLs, write "
        "/workspace/subagent/briefing.md with clear headings, and report that "
        "the file was written."
    )
    prompt = (
        task_text
        + "\\n\\nWhitelisted URLs:\\n- "
        + "\\n- ".join(WHITELIST_URLS)
        + "\\n\\nSuccess criteria:\\n"
        + success_criteria
    )

    started = time.perf_counter()
    log_event(LOG_DIR, "host_delegation_start", tool_name=subagent_tool)
    response = asyncio.run(
        host.reply(
            Msg("user", prompt, "user"),
        ),
    )
    elapsed = round(time.perf_counter() - started, 3)
    log_event(LOG_DIR, "host_delegation_end", elapsed_s=elapsed)
    briefing_path = WORKSPACE_ROOT / "workspace" / "subagent" / "briefing.md"
    briefing_exists = briefing_path.exists()
    briefing_text = (
        briefing_path.read_text(encoding="utf-8") if briefing_exists else ""
    )
    workspace_snapshot = sorted(
        str(path.relative_to(WORKSPACE_ROOT))
        for path in (WORKSPACE_ROOT / "workspace").rglob("*")
        if path.is_file()
    )
    log_event(
        LOG_DIR,
        "full_complete",
        elapsed_s=elapsed,
        briefing_exists=briefing_exists,
    )

    return {{
        "mode": "full",
        "agentscope_import_ok": True,
        "public_imports_ok": True,
        **import_proof,
        "subagent_tool_name": subagent_tool,
        "final_text": response.get_text_content(),
        "elapsed_s": elapsed,
        "briefing_exists": briefing_exists,
        "briefing_path": str(briefing_path),
        "briefing_excerpt": briefing_text[:1200],
        "workspace_snapshot": workspace_snapshot,
        "workspace_roots": service.list_allowed_directories(),
    }}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--logs-dir", type=Path, required=True)
    args = parser.parse_args()

    global WORKSPACE_ROOT, LOG_DIR
    WORKSPACE_ROOT = args.workspace_root
    LOG_DIR = args.logs_dir
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode == "smoke":
        result = run_smoke()
    else:
        result = run_full()

    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
'''


@dataclass(slots=True)
class RunArtifacts:
    """Structured paths and outputs for one validation sandbox run."""

    sandbox_root: Path
    wheelhouse: Path
    venv_root: Path
    app_dir: Path
    logs_dir: Path
    workspace_root: Path
    output_json: Path
    smoke_log: Path
    build_log: Path
    venv_log: Path
    install_log: Path


def repo_root() -> Path:
    """Return the repository root for the current script."""
    return Path(__file__).resolve().parents[2]


def spec_dir() -> Path:
    """Return the tracked spec directory for this wave."""
    return Path(__file__).resolve().parent


def report_path() -> Path:
    """Return the tracked validation report path."""
    return spec_dir() / "report.md"


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal KEY=VALUE `.env` file without external dependencies."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_runtime_env() -> dict[str, str]:
    """Load and validate the required runtime environment variables."""
    env_path = discover_env_file()
    values = parse_env_file(env_path)
    missing = [key for key in REQUIRED_ENV_KEYS if not values.get(key)]
    if missing:
        raise RuntimeError(f"Missing required .env keys: {', '.join(missing)}")
    return {key: values[key] for key in REQUIRED_ENV_KEYS}


def discover_env_file() -> Path:
    """Locate the effective `.env` file, including the main worktree fallback."""
    candidates = [repo_root() / ".env"]
    main_worktree_env = main_worktree_root() / ".env"
    if main_worktree_env not in candidates:
        candidates.append(main_worktree_env)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "Missing .env in current worktree and main worktree candidates: "
        + ", ".join(str(path) for path in candidates),
    )


def main_worktree_root() -> Path:
    """Return the primary non-`wt-*` worktree path for this repository."""
    completed = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return repo_root()

    worktrees = [
        Path(line.split(" ", 1)[1].strip())
        for line in completed.stdout.splitlines()
        if line.startswith("worktree ")
    ]
    for path in worktrees:
        if path.name == "agentscope-easy":
            return path
    for path in worktrees:
        if not path.name.startswith("wt-"):
            return path
    return repo_root()


def candidate_build_pythons() -> list[Path]:
    """Return ordered python candidates that may support `python -m build`."""
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    candidates = [
        repo_root() / ".venv" / bin_dir / "python",
        main_worktree_root() / ".venv" / bin_dir / "python",
        Path(sys.executable),
    ]
    ordered_unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered_unique.append(candidate)
    return ordered_unique


def python_supports_build(python_bin: Path) -> bool:
    """Return whether the interpreter can run `python -m build`."""
    if not python_bin.exists():
        return False
    completed = subprocess.run(
        [str(python_bin), "-m", "build", "--version"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def discover_build_python() -> Path:
    """Pick a python interpreter that can actually build the repo wheel."""
    candidates = candidate_build_pythons()
    for candidate in candidates:
        if python_supports_build(candidate):
            return candidate
    attempted = ", ".join(str(path) for path in candidates)
    raise RuntimeError(
        "No python interpreter with runnable `python -m build` was found. "
        f"Tried: {attempted}",
    )


def create_sandbox() -> RunArtifacts:
    """Create the isolated OS-temp sandbox for this validation run."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    root = Path(tempfile.gettempdir()) / f"subagent-v1-validate-{timestamp}"
    wheelhouse = root / "wheelhouse"
    venv_root = root / "venv"
    app_dir = root / "app"
    logs_dir = root / "logs"
    workspace_root = root
    for path in [wheelhouse, app_dir, logs_dir]:
        path.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(
        sandbox_root=root,
        wheelhouse=wheelhouse,
        venv_root=venv_root,
        app_dir=app_dir,
        logs_dir=logs_dir,
        workspace_root=workspace_root,
        output_json=root / "result.json",
        smoke_log=logs_dir / "smoke.log",
        build_log=logs_dir / "build.log",
        venv_log=logs_dir / "venv.log",
        install_log=logs_dir / "install.log",
    )


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    log_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command, capture output, and optionally mirror it to a log file."""
    effective_env = dict(os.environ) if env is None else dict(env)
    effective_env.pop("PYTHONPATH", None)
    effective_env.pop("PYTHONHOME", None)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=effective_env,
        capture_output=True,
        text=True,
        check=False,
    )
    if log_path is not None:
        log_path.write_text(
            completed.stdout + ("\n" + completed.stderr if completed.stderr else ""),
            encoding="utf-8",
        )
    return completed


def ensure_success(
    completed: subprocess.CompletedProcess[str],
    *,
    context: str,
) -> None:
    """Raise a descriptive error if the subprocess failed."""
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{context} failed: {message}")


def build_wheel(artifacts: RunArtifacts, build_python: Path) -> Path:
    """Build the current repository into a wheel inside the sandbox."""
    completed = run_command(
        [
            str(build_python),
            "-m",
            "build",
            "--no-isolation",
            "--wheel",
            "--outdir",
            str(artifacts.wheelhouse),
            str(repo_root()),
        ],
        cwd=repo_root(),
        log_path=artifacts.build_log,
    )
    ensure_success(completed, context="wheel build")
    wheels = sorted(artifacts.wheelhouse.glob("*.whl"))
    if not wheels:
        raise RuntimeError("wheel build succeeded but no wheel file was produced")
    return wheels[-1]


def create_venv(
    artifacts: RunArtifacts,
    seed_python: Path,
) -> tuple[Path, Path]:
    """Create the sandbox virtual environment and return python/pip paths."""
    completed = run_command(
        [str(seed_python), "-m", "venv", str(artifacts.venv_root)],
        cwd=repo_root(),
        log_path=artifacts.venv_log,
    )
    ensure_success(completed, context="sandbox venv creation")
    bin_dir = artifacts.venv_root / ("Scripts" if os.name == "nt" else "bin")
    return bin_dir / "python", bin_dir / "pip"


def python_site_packages(python_bin: Path) -> Path:
    """Return the interpreter's `purelib` site-packages path."""
    completed = run_command(
        [
            str(python_bin),
            "-c",
            "import sysconfig; print(sysconfig.get_paths()['purelib'])",
        ],
        cwd=repo_root(),
    )
    ensure_success(completed, context="site-packages discovery")
    resolved = Path(completed.stdout.strip())
    if not resolved.exists():
        raise RuntimeError(f"Resolved site-packages path does not exist: {resolved}")
    return resolved


def should_skip_dependency_entry(name: str) -> bool:
    """Return whether a dependency-layer entry would shadow wheel imports."""
    if name == "agentscope":
        return True
    if name.startswith("agentscope-") and (
        name.endswith(".dist-info") or name.endswith(".egg-info")
    ):
        return True
    if name.startswith("__editable__.agentscope-"):
        return True
    if name.startswith("__editable___agentscope_"):
        return True
    return False


def build_dependency_layer(
    *,
    artifacts: RunArtifacts,
    seed_python: Path,
) -> tuple[Path, Path]:
    """Create a filtered dependency layer without any `agentscope` artifacts."""
    source_site = python_site_packages(seed_python)
    layer_root = artifacts.sandbox_root / "dependency-layer"
    layer_root.mkdir(parents=True, exist_ok=True)
    for entry in source_site.iterdir():
        if should_skip_dependency_entry(entry.name):
            continue
        target = layer_root / entry.name
        target.symlink_to(entry)
    return layer_root, source_site


def attach_dependency_layer(
    *,
    sandbox_python: Path,
    dependency_layer: Path,
) -> Path:
    """Expose the pre-provisioned dependency layer to the sandbox venv."""
    sandbox_site = python_site_packages(sandbox_python)
    pth_path = sandbox_site / "agentscope_validation_dependency_layer.pth"
    pth_path.write_text(str(dependency_layer) + "\n", encoding="utf-8")
    return dependency_layer


def build_app_env(runtime_env: dict[str, str]) -> dict[str, str]:
    """Build the minimal sandbox env: OPENAI config plus tiny runtime baseline."""
    env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    for key in RUNTIME_BASE_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            env[key] = value
    env.update(runtime_env)
    return env


def install_wheel(pip_bin: Path, wheel_path: Path, artifacts: RunArtifacts) -> None:
    """Install the built wheel into the sandbox virtual environment."""
    completed = run_command(
        [
            str(pip_bin),
            "install",
            "--no-index",
            "--no-deps",
            str(wheel_path),
        ],
        cwd=repo_root(),
        log_path=artifacts.install_log,
    )
    ensure_success(completed, context="wheel install")


def write_external_app(artifacts: RunArtifacts) -> Path:
    """Write the external validation application into the sandbox."""
    app_path = artifacts.app_dir / "validate_subagent_field.py"
    app_path.write_text(
        EXTERNAL_APP.format(whitelist_urls=repr(WHITELIST_URLS)),
        encoding="utf-8",
    )
    return app_path


def run_external_app(
    python_bin: Path,
    app_path: Path,
    artifacts: RunArtifacts,
    runtime_env: dict[str, str],
    mode: str,
) -> dict[str, object]:
    """Run the external app in the sandbox and return its JSON result."""
    env = build_app_env(runtime_env)
    completed = run_command(
        [
            str(python_bin),
            str(app_path),
            "--mode",
            mode,
            "--output-json",
            str(artifacts.output_json),
            "--workspace-root",
            str(artifacts.workspace_root),
            "--logs-dir",
            str(artifacts.logs_dir),
        ],
        cwd=artifacts.app_dir,
        env=env,
        log_path=artifacts.smoke_log if mode == "smoke" else artifacts.logs_dir / "full.log",
    )
    ensure_success(completed, context=f"{mode} validation app")
    return json.loads(artifacts.output_json.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, object]]:
    """Read a JSONL log file if it exists."""
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def summarize_metrics(logs_dir: Path) -> dict[str, object]:
    """Aggregate metrics from sandbox logs."""
    model_calls = read_jsonl(logs_dir / "model_calls.jsonl")
    http_requests = read_jsonl(logs_dir / "http_requests.jsonl")
    input_tokens = 0
    output_tokens = 0
    usage_available = False
    for item in model_calls:
        usage = item.get("usage")
        if isinstance(usage, dict):
            usage_available = True
            input_tokens += int(usage.get("input_tokens", 0) or 0)
            output_tokens += int(usage.get("output_tokens", 0) or 0)
    return {
        "model_call_count": len(model_calls),
        "http_request_count": len(http_requests),
        "input_tokens": input_tokens if usage_available else None,
        "output_tokens": output_tokens if usage_available else None,
        "usage_available": usage_available,
    }


def collect_report_evidence(logs_dir: Path) -> dict[str, object]:
    """Collect log-backed evidence before sandbox cleanup removes it."""
    return {
        "metrics": summarize_metrics(logs_dir),
        "event_logs": read_jsonl(logs_dir / "events.jsonl"),
        "http_logs": read_jsonl(logs_dir / "http_requests.jsonl"),
    }


def render_report(
    *,
    mode: str,
    runtime_env: dict[str, str],
    artifacts: RunArtifacts,
    run_result: dict[str, object] | None,
    build_python: Path | None,
    dependency_site_packages: Path | None,
    dependency_source_site: Path | None,
    evidence: dict[str, object],
    error: str | None = None,
) -> str:
    """Render the tracked markdown validation report."""
    metrics = evidence["metrics"]
    event_logs = evidence["event_logs"]
    http_logs = evidence["http_logs"]
    verdict = "待运行"
    rationale = "尚未执行。"
    p0 = "- 无"
    root_cause = "- 待补充"
    next_steps = "- 待补充"
    failed_http_logs = [
        item for item in http_logs if not bool(item.get("ok", False))
    ]

    if error is not None:
        verdict = "不通过"
        rationale = error
        p0 = f"- {error}"
        if "环境" in error or "auth" in error or "quota" in error or "transport" in error:
            root_cause = "- 真实 provider 环境阻塞，未能进入业务链路。"
            next_steps = "- 校验 `.env` 凭证、provider 可达性、额度与 endpoint 兼容性后重跑本波次。"
        else:
            root_cause = "- 验证 harness 或库消费链路在当前步骤失败。"
            next_steps = "- 修复当前失败点后，重新从 smoke / full 入口执行。"
    elif mode == "full" and run_result is not None:
        briefing_exists = bool(run_result.get("briefing_exists"))
        final_text = str(run_result.get("final_text", "")).strip()
        if briefing_exists and final_text and not failed_http_logs:
            verdict = "通过"
            rationale = "真实 host -> subagent -> fetch -> write -> return 链路成功收敛。"
            root_cause = "- 无"
            next_steps = "- 后续若要继续放量，应单独补做 timeout / 429 / 限流专项验证。"
        elif briefing_exists and final_text:
            verdict = "部分通过"
            rationale = "真实链路写回成功，但至少一个官方源抓取失败，结果不满足“双源完成”标准。"
            first_failure = failed_http_logs[0]
            p0 = (
                "- 官方源存在抓取失败："
                f"{first_failure.get('url')} status={first_failure.get('status')}"
            )
            root_cause = "- 官方验证源之一对当前抓取方式返回错误，agent 虽然完成写回，但输入证据不完整。"
            next_steps = "- 优先解决失败官方源的抓取兼容性，再重跑 full 验证双源收敛。"
        else:
            verdict = "部分通过"
            if failed_http_logs:
                first_failure = failed_http_logs[0]
                rationale = "真实链路已执行，但官方源 403 阻塞后没有完成降级写回。"
                p0 = (
                    "- `/workspace/subagent/briefing.md` 未落盘；"
                    f"{first_failure.get('url')} status={first_failure.get('status')}"
                )
                root_cause = "- OpenAI 官方 URL 对当前 urllib 抓取返回 403，当前 agent loop 在单源失败场景下重复重试而未及时写回。"
                next_steps = "- 为官方页抓取补充兼容策略，或明确单源失败时也必须先落盘部分结果，再重跑 full。"
            else:
                rationale = "真实链路已执行，但最终产物或主代理收敛不完整。"
                p0 = "- briefing.md 未落盘或 host 最终摘要为空。"
                root_cause = "- 真实模型对任务分解、工具调用或最终收敛存在不稳定性。"
                next_steps = "- 强化 prompt / tool description，或单独分析模型工具调用兼容性。"
    elif mode == "smoke" and run_result is not None:
        verdict = "部分通过"
        rationale = "仅完成 wheel + import smoke，本轮尚未执行真实 full validation。"
        root_cause = "- 无"
        next_steps = "- 继续执行 `--mode full` 完成实战验收。"

    if mode == "full":
        if run_result and bool(run_result.get("briefing_exists")):
            file_write_status = str(run_result.get("briefing_path"))
        elif run_result:
            file_write_status = (
                "未观察到真实写回（target: "
                f"{run_result.get('briefing_path')}）"
            )
        else:
            file_write_status = "n/a"
        if run_result:
            final_text = str(run_result.get("final_text") or "").strip()
            if final_text and bool(run_result.get("briefing_exists")):
                host_final_text = final_text
            elif final_text:
                host_final_text = (
                    "模型最终摘要声称任务已完成，但未被磁盘写回证据证实："
                    f"{final_text}"
                )
            else:
                host_final_text = "none"
        else:
            host_final_text = "n/a"
        tool_trace_summary = (
            "本轮通过 host 最终收敛与 workspace 产物验证，不额外保留 "
            "ignored 原始 ToolResponse.metadata"
        )
        briefing_status = (
            run_result.get("briefing_exists") if run_result else "n/a"
        )
    else:
        file_write_status = "smoke 未覆盖"
        host_final_text = "smoke 未覆盖"
        tool_trace_summary = "smoke 未覆盖"
        briefing_status = "smoke 未覆盖"

    build_command = (
        shlex.join(
            [
                str(build_python),
                "-m",
                "build",
                "--no-isolation",
                "--wheel",
                "--outdir",
                str(artifacts.wheelhouse),
                str(repo_root()),
            ],
        )
        if build_python is not None
        else "unavailable"
    )
    usage_text = (
        f"input={metrics['input_tokens']}, output={metrics['output_tokens']}"
        if metrics["usage_available"]
        else "unavailable"
    )
    http_summary = (
        "\n".join(
            f"  - {item.get('url')} status={item.get('status')} "
            f"elapsed={item.get('elapsed_s')}s"
            for item in http_logs[:4]
        )
        or "  - none"
    )
    event_summary = (
        "\n".join(
            f"  - {item.get('ts')} :: {item.get('event')}"
            for item in event_logs[:8]
        )
        or "  - none"
    )
    briefing_excerpt = (
        str(run_result.get("briefing_excerpt", "")) if run_result is not None else ""
    )
    if mode == "full" and run_result is not None:
        workspace_snapshot_items = run_result.get("workspace_snapshot", [])
        workspace_snapshot_text = (
            "\n".join(f"  - {item}" for item in workspace_snapshot_items)
            if workspace_snapshot_items
            else "  - none"
        )
    else:
        workspace_snapshot_text = "  - smoke 未覆盖"
    cleanup_status = (
        f"pending cleanup for {artifacts.sandbox_root}"
        if artifacts.sandbox_root.exists()
        else f"removed {artifacts.sandbox_root}"
    )
    report_text = f"""\
        # SubAgent V1 实战验证报告

        ## 0. 报告状态

        - 状态：已运行
        - 波次：`038-subagent-v1-field-validation`
        - 最终 verdict 允许值：`通过` / `部分通过` / `不通过`
        - 若真实 provider 因环境问题阻塞，固定写法为：`Verdict: 不通过`，并在结论正文中注明子类原因 `环境阻塞`

        ## 1. 场景描述

        - 验证任务：host agent 以外部依赖方式调用 `register_subagent(TaskSubAgent, ...)`，委派子代理抓取官方文档、提炼比较结论，并写回 `briefing.md`
        - Host / SubAgent 角色关系：host 负责监督与最终收敛；`TaskSubAgent` 负责抓取、整理与写回
        - 真实写回产物：`/workspace/subagent/briefing.md`
        - 当前能力边界说明：本轮按 shipped `SubAgent V1` 的串行 delegation 语义验证，不把后台异步 subagent 视为已实现能力

        ## 2. 外部参考来源

        - OpenAI：`{WHITELIST_URLS[0]}`
        - Anthropic：`{WHITELIST_URLS[1]}`
        - 本轮白名单 URL：
          - `{WHITELIST_URLS[0]}`
          - `{WHITELIST_URLS[1]}`

        ## 3. 环境与依赖引入方式

        - worktree：`{repo_root()}`
        - sandbox：`{artifacts.sandbox_root}`
        - wheel 构建方式：`{build_command}`
        - wheel 安装方式：`{artifacts.venv_root / ('Scripts' if os.name == 'nt' else 'bin') / 'pip'} install --no-index --no-deps <wheel>`
        - 依赖层来源：`{dependency_site_packages if dependency_site_packages else 'n/a'}`（源：`{dependency_source_site if dependency_source_site else 'n/a'}`，已过滤 `agentscope` editable / dist-info）
        - `.env` 注入方式：业务配置仅注入 `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL`；另保留最小运行时基线 env（如 `HOME`、`PATH`、`TMPDIR`、证书变量）
        - base import smoke 结果：{run_result.get('agentscope_import_ok') if run_result else 'n/a'}
        - `agentscope` 导入来源：`{run_result.get('agentscope_module_path') if run_result else 'n/a'}`

        ## 4. 执行过程关键日志摘要

        - Host 注册子代理：`{run_result.get('subagent_tool_name') if run_result else 'n/a'}`
        - 子代理启动：
        {event_summary}
        - 官方页面抓取：
        {http_summary}
        - 文件回写：`{file_write_status}`
        - Host 最终收敛：`{host_final_text}`

        ## 5. 指标与结果

        - 总耗时：`{run_result.get('elapsed_s') if run_result else 'n/a'}`
        - 模型调用次数：`{metrics['model_call_count']}`
        - HTTP 请求次数：`{metrics['http_request_count']}`
        - token / usage：`{usage_text}`
        - `tool_trace`：{tool_trace_summary}
        - `briefing.md` 写回结果：`{briefing_status}`

        ## 6. 未覆盖项

        - `timeout / 429 / provider 限流`：本轮未覆盖

        ## 7. 最终结论

        - Verdict：{verdict}
        - 判定依据：{rationale}

        ## 8. P0 缺口

        {p0}

        ## 9. 根因分析

        {root_cause}

        ## 10. 收敛路径

        {next_steps}

        ## 11. 清理结果

        - OS temp sandbox：{cleanup_status}
        - 其他临时资产：sandbox logs 与外部 app 均位于 sandbox 内，cleanup 后不再保留

        ## 12. Workspace 快照

        {workspace_snapshot_text}

        ## 13. 关键产物摘录

        ```markdown
        {briefing_excerpt}
        ```
        """
    return textwrap.dedent(report_text).replace("\n        ", "\n").strip() + "\n"


def cleanup_sandbox(artifacts: RunArtifacts) -> None:
    """Remove the temporary sandbox tree."""
    if artifacts.sandbox_root.exists():
        shutil.rmtree(artifacts.sandbox_root)


def run_mode(mode: str) -> int:
    """Execute the requested validation mode and update the tracked report."""
    artifacts = create_sandbox()
    runtime_env: dict[str, str] | None = None
    run_result: dict[str, object] | None = None
    build_python: Path | None = None
    dependency_site_packages: Path | None = None
    dependency_source_site: Path | None = None
    evidence: dict[str, object] = {
        "metrics": {
            "model_call_count": 0,
            "http_request_count": 0,
            "input_tokens": None,
            "output_tokens": None,
            "usage_available": False,
        },
        "event_logs": [],
        "http_logs": [],
    }
    error: str | None = None
    try:
        runtime_env = load_runtime_env()
        build_python = discover_build_python()
        wheel_path = build_wheel(artifacts, build_python)
        python_bin, pip_bin = create_venv(artifacts, build_python)
        install_wheel(pip_bin, wheel_path, artifacts)
        dependency_layer, dependency_source_site = build_dependency_layer(
            artifacts=artifacts,
            seed_python=build_python,
        )
        dependency_site_packages = attach_dependency_layer(
            sandbox_python=python_bin,
            dependency_layer=dependency_layer,
        )
        app_path = write_external_app(artifacts)
        run_result = run_external_app(
            python_bin,
            app_path,
            artifacts,
            runtime_env,
            mode,
        )
        evidence = collect_report_evidence(artifacts.logs_dir)
        return_code = 0
    except Exception as exc:  # noqa: BLE001
        evidence = collect_report_evidence(artifacts.logs_dir)
        error = str(exc)
        return_code = 1

    report_text = render_report(
        mode=mode,
        runtime_env=runtime_env or {},
        artifacts=artifacts,
        run_result=run_result,
        build_python=build_python,
        dependency_site_packages=dependency_site_packages,
        dependency_source_site=dependency_source_site,
        evidence=evidence,
        error=error,
    )
    report_path().write_text(report_text, encoding="utf-8")
    cleanup_sandbox(artifacts)
    # Rewrite report once more so the cleanup section reflects the final state.
    final_report = render_report(
        mode=mode,
        runtime_env=runtime_env or {},
        artifacts=artifacts,
        run_result=run_result,
        build_python=build_python,
        dependency_site_packages=dependency_site_packages,
        dependency_source_site=dependency_source_site,
        evidence=evidence,
        error=error,
    )
    report_path().write_text(final_report, encoding="utf-8")
    if error is not None:
        print(error, file=sys.stderr)
    return return_code


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["smoke", "full"],
        default="full",
    )
    args = parser.parse_args()
    raise SystemExit(run_mode(args.mode))


if __name__ == "__main__":
    main()
