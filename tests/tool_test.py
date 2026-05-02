# -*- coding: utf-8 -*-
"""The tool module unit tests"""

import platform
import sys
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from agentscope.tool import (
    execute_python_code,
    execute_shell_command,
)


class ToolTest(IsolatedAsyncioTestCase):
    """Test cases for the tool module."""

    class _FakeSubprocess:
        """A minimal fake subprocess for tool execution tests."""

        def __init__(
            self,
            stdout: bytes = b"",
            stderr: bytes = b"",
            returncode: int = 0,
        ) -> None:
            self._stdout = stdout
            self._stderr = stderr
            self.returncode = returncode

        async def wait(self) -> int:
            """Return immediately like a finished process."""
            return self.returncode

        async def communicate(self) -> tuple[bytes, bytes]:
            """Return captured process output."""
            return self._stdout, self._stderr

    async def test_execute_python_code(self) -> None:
        """Test executing Python code."""

        # empty output
        res = await execute_python_code(code="a = 1 + 1")
        self.assertEqual(
            "<returncode>0</returncode>"
            "<stdout></stdout>"
            "<stderr></stderr>",
            res.content[0]["text"],
        )

        # with output
        res = await execute_python_code(code="print('Hello, World!')")

        actual = res.content[0]["text"].replace("\r\n", "\n")
        self.assertEqual(
            "<returncode>0</returncode>"
            "<stdout>Hello, World!\n</stdout>"
            "<stderr></stderr>",
            actual,
        )

        # with exception
        res = await execute_python_code(code="raise Exception('Test error')")
        actual = res.content[0]["text"].replace("\r\n", "\n")

        self.assertTrue(
            actual.startswith(
                "<returncode>1</returncode>"
                "<stdout></stdout>"
                "<stderr>Traceback (most recent call last):\n  File ",
            ),
        )
        self.assertTrue(
            actual.endswith(
                '.py", line 1, in <module>\n'
                "    raise Exception('Test error')\n"
                "Exception: Test error\n"
                "</stderr>",
            ),
        )

        # with timeout
        code = """print("123")
import time
time.sleep(5)
print("456")"""

        res = await execute_python_code(code)
        actual = res.content[0]["text"].replace("\r\n", "\n")
        self.assertEqual(
            "<returncode>0</returncode>"
            "<stdout>123\n456\n</stdout>"
            "<stderr></stderr>",
            actual,
        )

        res = await execute_python_code(code, timeout=2)
        actual = res.content[0]["text"].replace("\r\n", "\n")
        self.assertEqual(
            "<returncode>-1</returncode>"
            "<stdout>123\n</stdout>"
            "<stderr>TimeoutError: The code execution exceeded the "
            "timeout of 2 seconds.</stderr>",
            actual,
        )

    async def test_execute_shell_command(self) -> None:
        """Test executing shell command."""
        # empty output
        python_echo_cmd = f"{sys.executable} -c \"print('Hello, World!')\""
        res = await execute_shell_command(command=python_echo_cmd)
        actual = res.content[0]["text"].replace("\r\n", "\n")
        self.assertEqual(
            "<returncode>0</returncode>"
            "<stdout>Hello, World!\n</stdout>"
            "<stderr></stderr>",
            actual,
        )

        # with exception
        res = await execute_shell_command(command="non_existent_command")
        assert any(
            keyword in res.content[0]["text"].lower()
            for keyword in ["not found", "is not recognized"]
        )

        # without timeout
        normal_cmd = (
            f"{sys.executable} -c \""  # fmt: skip
            f"import time; print('123'); "
            f"time.sleep(0.1); print('456')\""
        )

        res = await execute_shell_command(
            command=normal_cmd,
        )
        actual = res.content[0]["text"].replace("\r\n", "\n")
        self.assertEqual(
            "<returncode>0</returncode>"
            "<stdout>123\n456\n</stdout>"
            "<stderr></stderr>",
            actual,
        )

        # with timeout
        if platform.system() == "Windows":
            return
        else:
            timeout_cmd = 'echo "123"; sleep 5; echo "456"'

        res = await execute_shell_command(
            command=timeout_cmd,
            timeout=2,
        )
        actual = res.content[0]["text"].replace("\r\n", "\n")
        self.assertEqual(
            "<returncode>-1</returncode>"
            "<stdout>123\n</stdout>"
            "<stderr>TimeoutError: The command execution exceeded "
            "the timeout of 2 seconds.</stderr>",
            actual,
        )

    async def test_execute_python_code_filters_grpc_fork_noise(self) -> None:
        """gRPC fork noise should not leak into tool stderr."""
        fake_proc = self._FakeSubprocess(
            stderr=(
                b"I0411 03:34:17.517323   62093 ev_poll_posix.cc:593] "
                b"FD from fork parent still in poll list: fd(36, "
                b"generation: 1)\n"
            ),
        )

        with patch(
            "agentscope.tool._coding._python.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=fake_proc),
        ):
            res = await execute_python_code(code="a = 1 + 1")

        self.assertEqual(
            "<returncode>0</returncode>"
            "<stdout></stdout>"
            "<stderr></stderr>",
            res.content[0]["text"],
        )

    async def test_execute_shell_command_filters_grpc_fork_noise(self) -> None:
        """Shell tool should strip parent-process gRPC fork noise."""
        fake_proc = self._FakeSubprocess(
            stdout=b"Hello, World!\n",
            stderr=(
                b"I0411 03:34:17.822017   62123 ev_poll_posix.cc:593] "
                b"FD from fork parent still in poll list: fd(36, "
                b"generation: 1)\n"
            ),
        )

        with patch(
            "agentscope.tool._coding._shell.asyncio.create_subprocess_shell",
            new=AsyncMock(return_value=fake_proc),
        ):
            res = await execute_shell_command(command="echo 'Hello, World!'")

        self.assertEqual(
            "<returncode>0</returncode>"
            "<stdout>Hello, World!\n</stdout>"
            "<stderr></stderr>",
            res.content[0]["text"],
        )

    async def test_execute_shell_command_keeps_real_stderr(self) -> None:
        """Real stderr should survive even when gRPC fork noise is present."""
        fake_proc = self._FakeSubprocess(
            stderr=(
                b"I0411 03:34:17.822017   62123 ev_poll_posix.cc:593] "
                b"FD from fork parent still in poll list: fd(36, "
                b"generation: 1)\n"
                b"real error\n"
            ),
            returncode=1,
        )

        with patch(
            "agentscope.tool._coding._shell.asyncio.create_subprocess_shell",
            new=AsyncMock(return_value=fake_proc),
        ):
            res = await execute_shell_command(command="bad-command")

        self.assertEqual(
            "<returncode>1</returncode>"
            "<stdout></stdout>"
            "<stderr>real error\n</stderr>",
            res.content[0]["text"],
        )


class LegacyExportsTest(IsolatedAsyncioTestCase):
    """Verify legacy text-file tools are fully retired."""

    def test_legacy_text_file_tools_are_not_in_agentscope_tool(self) -> None:
        """Legacy text-file tools must not be in agentscope.tool exports."""
        import agentscope.tool as tool_module

        for name in ("view_text_file", "write_text_file", "insert_text_file"):
            self.assertNotIn(
                name,
                getattr(tool_module, "__all__", []),
                f"{name} still in __all__",
            )
            self.assertFalse(
                hasattr(tool_module, name),
                f"{name} still exists as attribute",
            )
