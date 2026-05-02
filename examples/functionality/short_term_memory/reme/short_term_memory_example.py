# -*- coding: utf-8 -*-
"""Example demonstrating ReMeShortTermMemory usage with ReActAgent."""
# noqa: E402
import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from agentscope.agent import ReActAgent
from agentscope.filesystem import DiskFileSystem, FileDomainService
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg, TextBlock
from agentscope.model import DashScopeChatModel
from agentscope.tool import ToolResponse, Toolkit

_WORKSPACE_README_PATH = "/workspace/README.md"
_DEMO_ROOT: Path | None = None


def _demo_root() -> Path:
    """Return the shared host root used by the ReMe demo."""
    global _DEMO_ROOT  # pylint: disable=global-statement
    if _DEMO_ROOT is None:
        _DEMO_ROOT = Path(tempfile.mkdtemp(prefix="agentscope-reme-fs-"))
    return _DEMO_ROOT


def _workspace_dir() -> Path:
    """Return the demo workspace directory shared by tools and offload."""
    return _demo_root() / "workspace"


def _reme_store_dir() -> Path:
    """Return the offload directory under the demo workspace."""
    return _workspace_dir() / "reme"


def _source_readme_path() -> Path:
    """Return the repository README path used to seed the demo workspace."""
    return Path(__file__).resolve().parents[4] / "README.md"


def _seed_workspace_readme(service: FileDomainService) -> str:
    """Write the repository README into the logical workspace and read it back."""
    readme_content = _source_readme_path().read_text(encoding="utf-8")
    service.write_file(_WORKSPACE_README_PATH, readme_content)
    return service.read_text_file(_WORKSPACE_README_PATH)


async def _grep_workspace(
    service: FileDomainService,
    file_path: str,
    pattern: str,
    limit: str,
) -> ToolResponse:
    """Search for regex patterns in files."""
    matches = service.read_re(file_path, pattern)
    output = "\n".join(matches[: int(limit)])
    return ToolResponse(content=[TextBlock(type="text", text=output)])


async def _read_workspace_file(
    service: FileDomainService,
    file_path: str,
    offset: int,
    limit: int,
) -> ToolResponse:
    """Read and number a slice of a logical workspace file."""
    raw = service.read_text_file(
        file_path,
        start_line=offset + 1,
        read_lines=limit,
    )
    lines = raw.splitlines()
    numbered = [f"line{offset + i + 1}: {line}" for i, line in enumerate(lines)]
    return ToolResponse(content=[TextBlock(type="text", text="\n".join(numbered))])


async def main() -> None:
    """Main function demonstrating ReMeShortTermMemory with tool usage."""
    from reme_short_term_memory import ReMeShortTermMemory

    load_dotenv()
    toolkit = Toolkit()

    # Setup filesystem service
    fs = DiskFileSystem(
        root_dir=str(_demo_root()),
        workspace_dir=str(_workspace_dir()),
    )
    handle = fs.create_handle(
        [
            {
                "prefix": "/workspace/",
                "ops": {"list", "file", "read_binary", "read_file", "read_re", "write", "delete"},
            },
        ],
    )
    service = FileDomainService(handle)

    async def grep(file_path: str, pattern: str, limit: str) -> ToolResponse:
        """Search for regex patterns in files.

        Args:
            file_path (`str`):
                Absolute logical path (must be under /workspace/ in this example).
            pattern (`str`):
                The search pattern or regular expression to match.
            limit (`str`):
                Maximum number of regex match fragments to return.
        """
        return await _grep_workspace(service, file_path, pattern, limit)

    async def read_file(
        file_path: str,
        offset: int,
        limit: int,
    ) -> ToolResponse:
        """Reads and returns the content of a specified file.

        For text files, it can read specific line ranges using the 'offset' and
        'limit' parameters. Use offset and limit to paginate through large
        files.

        Note: It's recommended to use the `grep` tool first to locate the line
        numbers of interest before calling this function.

        Args:
            file_path (`str`):
                Absolute logical path (must start with /, e.g. /workspace/filename).
            offset (`int`):
                The starting line number to read from (0-indexed). Use this to
                skip to a specific position in the file.
            limit (`int`):
                The maximum number of lines to read from the offset position.
                Helps control memory usage when reading large files. Should
                not exceed 100.
        """

        return await _read_workspace_file(service, file_path, offset, limit)

    # These two tools are provided as examples. You can replace them with your
    # own retrieval tools, such as vector database embedding retrieval or other
    # search solutions that fit your use case.
    toolkit.register_tool_function(grep)
    toolkit.register_tool_function(read_file)

    llm = DashScopeChatModel(
        model_name="qwen3-max",
        # model_name="qwen3-coder-30b-a3b-instruct",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        stream=False,
        generate_kwargs={
            "temperature": 0.001,
            "seed": 0,
        },
    )
    short_term_memory = ReMeShortTermMemory(
        model=llm,
        working_summary_mode="auto",
        compact_ratio_threshold=0.75,
        max_total_tokens=20000,
        max_tool_message_tokens=2000,
        group_token_threshold=None,  # Max tokens per compression batch
        keep_recent_count=1,  # Set to 1 for demo; use 10 in production
        store_dir=str(_reme_store_dir()),
    )

    async with short_term_memory:
        # Simulate ultra long context
        readme_content = _seed_workspace_readme(service)

        memories = [
            {
                "role": "user",
                "content": "Search for project information",
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "call_6596dafa2a6a46f7a217da",
                        "function": {
                            "arguments": "{}",
                            "name": "web_search",
                        },
                        "type": "function",
                    },
                ],
            },
            {
                "role": "tool",
                "content": readme_content * 10,
                "tool_call_id": "call_6596dafa2a6a46f7a217da",
            },
        ]
        await short_term_memory.add(
            ReMeShortTermMemory.list_to_msg(memories),
            allow_duplicates=True,
        )

        agent = ReActAgent(
            name="react",
            sys_prompt=(
                "You are a helpful assistant. "
                "Tool calls may be cached locally. "
                "You can first use `Grep` to match keywords or regular "
                "expressions to find line numbers, then use `ReadFile` "
                "to read the code near that location. "
                "If no matches are found, never give up trying - try "
                "other parameters or relax the matching conditions, such "
                "as searching for only partial keywords. "
                "After `Grep`, you can use the `ReadFile` command to "
                "view content starting from a specified offset position "
                "`offset` with length `limit`. "
                "The maximum limit is 100. "
                "If the current content is insufficient, the `ReadFile` "
                "command can continuously try different `offset` and "
                "`limit` parameters."
            ),
            model=llm,
            formatter=DashScopeChatFormatter(),
            toolkit=toolkit,
            memory=short_term_memory,
            max_iters=20,
        )

        msg = Msg(
            role="user",
            content=(
                "In the project documentation, who is the first author "
                "of the agentscope_v1 paper?"
            ),
            name="user",
        )
        msg = await agent(msg)
        print(f"✓ Agent response: {msg.get_text_content()}\n")


if __name__ == "__main__":
    asyncio.run(main())
