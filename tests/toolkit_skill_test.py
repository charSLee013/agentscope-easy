# -*- coding: utf-8 -*-
"""Regression tests for register_agent_skill logical_dir semantics."""
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import pytest

from agentscope.tool import Toolkit


def _write_skill_md(skill_path: Path) -> None:
    skill_path.mkdir()
    (skill_path / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: test\n---\n# Test\n",
        encoding="utf-8",
    )


class RegisterAgentSkillLogicalDirTest(TestCase):
    """Verify skill registration wiring and prompt semantics."""

    def test_explicit_logical_dir_appears_in_skill_prompt(self) -> None:
        """Explicit logical_dir must appear in get_agent_skill_prompt()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()
            toolkit.register_agent_skill(
                str(skill_path),
                logical_dir="/internal/my-skill",
            )
            prompt = toolkit.get_agent_skill_prompt()
            self.assertIn("/internal/my-skill/SKILL.md", prompt)

    def test_default_logical_dir_derived_from_skill_name(self) -> None:
        """Default logical_dir should be /internal/<skill_name>."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()
            toolkit.register_agent_skill(str(skill_path))
            prompt = toolkit.get_agent_skill_prompt()
            self.assertIn("/internal/my-skill/SKILL.md", prompt)
            self.assertEqual(
                toolkit.skills["my-skill"]["logical_dir"],
                "/internal/my-skill",
            )
            self.assertNotIn("dir", toolkit.skills["my-skill"])

    def test_skill_prompt_no_host_path(self) -> None:
        """Prompt must contain logical_dir and must not leak host paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()
            toolkit.register_agent_skill(
                str(skill_path),
                logical_dir="/internal/my-skill",
            )
            prompt = toolkit.get_agent_skill_prompt()
            self.assertNotIn("./", prompt)
            self.assertNotIn(tmpdir, prompt)

    def test_custom_template_uses_logical_dir_placeholder(self) -> None:
        """Custom templates should use {logical_dir}."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit(agent_skill_template="- {name}({logical_dir})")
            toolkit.register_agent_skill(
                str(skill_path),
                logical_dir="/internal/my-skill",
            )

            prompt = toolkit.get_agent_skill_prompt()

            self.assertIn("- my-skill(/internal/my-skill)", prompt)
            self.assertNotIn(tmpdir, prompt)

    def test_custom_template_dir_alias_is_rejected(self) -> None:
        """Legacy {dir} placeholder should fail without compatibility alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit(agent_skill_template="- {name}({dir})")
            toolkit.register_agent_skill(
                str(skill_path),
                logical_dir="/internal/my-skill",
            )

            with pytest.raises(KeyError, match="dir"):
                toolkit.get_agent_skill_prompt()

    def test_register_agent_skill_log_uses_logical_dir(self) -> None:
        """Registration logs should not expose the host skill directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()

            with patch("agentscope.tool._toolkit.logger.info") as info:
                toolkit.register_agent_skill(
                    str(skill_path),
                    logical_dir="/internal/my-skill",
                )

            log_args = info.call_args.args
            self.assertIn("/internal/my-skill", log_args)
            self.assertNotIn(str(skill_path), log_args)

    def test_logical_dir_rejects_relative_path(self) -> None:
        """logical_dir='relative/path' must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()
            with pytest.raises(ValueError, match="absolute logical path"):
                toolkit.register_agent_skill(
                    str(skill_path),
                    logical_dir="relative/path",
                )

    def test_logical_dir_rejects_workspace_domain(self) -> None:
        """logical_dir='/workspace/...' must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()
            with pytest.raises(ValueError, match="must be under /internal/"):
                toolkit.register_agent_skill(
                    str(skill_path),
                    logical_dir="/workspace/my-skill",
                )

    def test_logical_dir_rejects_trailing_slash(self) -> None:
        """logical_dir='/internal/my-skill/' must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()
            with pytest.raises(ValueError, match="trailing slash"):
                toolkit.register_agent_skill(
                    str(skill_path),
                    logical_dir="/internal/my-skill/",
                )

    def test_logical_dir_rejects_internal_root(self) -> None:
        """logical_dir='/internal' (no sub-path) must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "my-skill"
            _write_skill_md(skill_path)
            toolkit = Toolkit()
            with pytest.raises(ValueError, match="must be under /internal/"):
                toolkit.register_agent_skill(
                    str(skill_path),
                    logical_dir="/internal",
                )
