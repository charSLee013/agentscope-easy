# -*- coding: utf-8 -*-
"""Real provider-backed validation for the wave-036 MCP example chain."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple, Sequence

from pydantic import BaseModel, Field

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.mcp import HttpStatelessClient, HttpStatefulClient
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.tool import ToolResponse, Toolkit


EXPECTED_RESULT = 8108887
EXPECTED_TOOL_NAMES = {"multiply", "add"}


class OpenAIRuntimeSettings(NamedTuple):
    """Settings required for the OpenAI-compatible validation run."""

    api_key: str
    model_name: str
    base_url: str


class ServerHandle(NamedTuple):
    """Runtime handle for a spawned MCP server process."""

    name: str
    process: subprocess.Popen[Any]
    log_handle: Any
    log_path: Path


class NumberResult(BaseModel):
    """Structured result for the MCP arithmetic demo."""

    result: int = Field(description="The final calculation result.")


def parse_env_file(env_file: Path) -> dict[str, str]:
    """Parse a minimal `.env` file without requiring extra dependencies."""
    parsed: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        cleaned = value.strip().strip("'").strip('"')
        parsed[key.strip()] = cleaned

    return parsed


def load_openai_runtime_settings(env_file: Path) -> OpenAIRuntimeSettings:
    """Load OpenAI-compatible settings with the repo `.env` as truth."""
    env_values = parse_env_file(env_file)

    def _pick(key: str) -> str:
        value = env_values.get(key) or os.environ.get(key)
        if not value:
            raise ValueError(
                f"Missing required setting {key!r} in {env_file} or env.",
            )
        return value

    return OpenAIRuntimeSettings(
        api_key=_pick("OPENAI_API_KEY"),
        model_name=_pick("OPENAI_MODEL"),
        base_url=_pick("OPENAI_BASE_URL"),
    )


def collect_tool_trace(messages: Sequence[Msg]) -> list[dict[str, str]]:
    """Collect tool-use and tool-result events from the agent memory."""
    trace: list[dict[str, str]] = []
    for message in messages:
        for block in message.get_content_blocks("tool_use"):
            trace.append(
                {
                    "event": "tool_use",
                    "name": str(block["name"]),
                },
            )
        for block in message.get_content_blocks("tool_result"):
            trace.append(
                {
                    "event": "tool_result",
                    "name": str(block["name"]),
                },
            )
    return trace


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _tail_text(path: Path, lines: int = 40) -> str:
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


async def _wait_for_port(host: str, port: int, timeout: float) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError(
                    f"Timed out waiting for {host}:{port} to accept connections.",
                ) from None
            await asyncio.sleep(0.25)


def _spawn_server(
    *,
    python_bin: str,
    script_path: Path,
    project_root: Path,
    log_dir: Path,
    name: str,
) -> ServerHandle:
    log_path = log_dir / f"{name}.log"
    log_handle = log_path.open("w", encoding="utf-8")
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    source_root = str(project_root / "src")
    env["PYTHONPATH"] = (
        f"{source_root}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else source_root
    )

    process = subprocess.Popen(
        [python_bin, str(script_path)],
        cwd=str(script_path.parent),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )
    return ServerHandle(
        name=name,
        process=process,
        log_handle=log_handle,
        log_path=log_path,
    )


def _stop_server(handle: ServerHandle) -> None:
    process = handle.process
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    handle.log_handle.close()


def _extract_int_from_tool_response(response: ToolResponse) -> int:
    for block in response.content:
        if block["type"] == "text":
            return int(block["text"])
    raise ValueError("Tool response does not contain a text block.")


async def run_validation(
    *,
    env_file: Path,
    python_bin: str,
    output_json: Path | None = None,
) -> dict[str, Any]:
    """Run the real MCP validation with a live OpenAI-compatible provider."""
    project_root = _repo_root()
    example_dir = project_root / "examples/functionality/mcp"
    log_dir = project_root / "artifacts/036-real-runtime"
    log_dir.mkdir(parents=True, exist_ok=True)

    settings = load_openai_runtime_settings(env_file)
    add_server = _spawn_server(
        python_bin=python_bin,
        script_path=example_dir / "mcp_add.py",
        project_root=project_root,
        log_dir=log_dir,
        name="mcp_add",
    )
    multiply_server = _spawn_server(
        python_bin=python_bin,
        script_path=example_dir / "mcp_multiply.py",
        project_root=project_root,
        log_dir=log_dir,
        name="mcp_multiply",
    )

    add_mcp_client = HttpStatefulClient(
        name="add_mcp",
        transport="sse",
        url="http://127.0.0.1:8001/sse",
    )
    multiply_mcp_client = HttpStatelessClient(
        name="multiply_mcp",
        transport="streamable_http",
        url="http://127.0.0.1:8002/mcp",
    )

    try:
        try:
            await asyncio.gather(
                _wait_for_port("127.0.0.1", 8001, timeout=15),
                _wait_for_port("127.0.0.1", 8002, timeout=15),
            )
        except TimeoutError as exc:
            raise RuntimeError(
                "Failed to start local MCP servers.\n"
                f"[mcp_add tail]\n{_tail_text(add_server.log_path)}\n\n"
                f"[mcp_multiply tail]\n{_tail_text(multiply_server.log_path)}",
            ) from exc

        await add_mcp_client.connect()

        toolkit = Toolkit()
        await toolkit.register_mcp_client(add_mcp_client)
        await toolkit.register_mcp_client(multiply_mcp_client)

        agent = ReActAgent(
            name="Jarvis",
            sys_prompt=(
                "You are a careful arithmetic assistant. "
                "You must use the provided tools for arithmetic, "
                "never compute in your head, and only call "
                "`generate_response` after the required tool calls succeed."
            ),
            model=OpenAIChatModel(
                model_name=settings.model_name,
                api_key=settings.api_key,
                stream=False,
                client_kwargs={"base_url": settings.base_url},
            ),
            formatter=OpenAIChatFormatter(),
            toolkit=toolkit,
            max_iters=8,
        )

        reply = await agent(
            Msg(
                "user",
                (
                    "First call `multiply` with 2345 and 3456. "
                    "Then call `add` with that result and 4567. "
                    "Do not skip tools or do mental math. "
                    "Return the final integer only."
                ),
                "user",
            ),
            structured_model=NumberResult,
        )

        memory_messages = await agent.memory.get_memory()
        tool_trace = collect_tool_trace(memory_messages)
        used_tool_names = {
            item["name"]
            for item in tool_trace
            if item["event"] == "tool_use"
        }

        add_tool_function = await add_mcp_client.get_callable_function(
            "add",
            wrap_tool_result=True,
        )
        manual_add_response = await add_tool_function(a=5, b=10)
        manual_add_result = _extract_int_from_tool_response(
            manual_add_response,
        )

        structured_result = reply.metadata.get("result")
        if structured_result != EXPECTED_RESULT:
            raise RuntimeError(
                "Real runtime validation returned an unexpected structured "
                f"result: {structured_result!r}",
            )

        if not EXPECTED_TOOL_NAMES.issubset(used_tool_names):
            raise RuntimeError(
                "Real runtime validation did not use both MCP tools.\n"
                f"Observed tool trace: {json.dumps(tool_trace, indent=2)}",
            )

        if manual_add_result != 15:
            raise RuntimeError(
                f"Manual MCP callable returned {manual_add_result!r}, expected 15.",
            )

        evidence = {
            "env_file": str(env_file),
            "model_name": settings.model_name,
            "base_url": settings.base_url,
            "structured_result": structured_result,
            "reply_text": reply.get_text_content(),
            "tool_trace": tool_trace,
            "manual_add_result": manual_add_result,
            "server_logs": {
                "mcp_add": str(add_server.log_path),
                "mcp_multiply": str(multiply_server.log_path),
            },
        }

        if output_json is not None:
            output_json.parent.mkdir(parents=True, exist_ok=True)
            output_json.write_text(
                json.dumps(evidence, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return evidence
    finally:
        if add_mcp_client.is_connected:
            await add_mcp_client.close()
        _stop_server(add_server)
        _stop_server(multiply_server)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the wave-036 real provider-backed MCP validation chain."
        ),
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        required=True,
        help="Path to the authoritative `.env` file for OPENAI_* settings.",
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python interpreter used to start the local MCP servers.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=_repo_root() / "artifacts/036-real-runtime/evidence.json",
        help="Optional JSON evidence output path.",
    )
    return parser


def main() -> None:
    """CLI entry for the real runtime validation."""
    args = _build_arg_parser().parse_args()
    evidence = asyncio.run(
        run_validation(
            env_file=args.env_file,
            python_bin=args.python_bin,
            output_json=args.output_json,
        ),
    )
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
