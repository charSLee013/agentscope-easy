# -*- coding: utf-8 -*-
"""Helpers shared by coding tools for subprocess output handling."""


def normalize_subprocess_stderr(stderr: str) -> str:
    """Remove known parent-process noise that is not user command stderr."""
    if not stderr:
        return stderr

    filtered_lines = []
    for line in stderr.splitlines(keepends=True):
        if _is_grpc_fork_noise(line):
            continue
        filtered_lines.append(line)
    return "".join(filtered_lines)


def _is_grpc_fork_noise(line: str) -> bool:
    """Detect gRPC poller warnings inherited from a forked parent process."""
    normalized = line.strip()
    return (
        "ev_poll_posix.cc" in normalized
        and "FD from fork parent still in poll list" in normalized
    )
