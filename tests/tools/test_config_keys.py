"""Tests that tools accept kebab-case and snake_case configuration keys, using the documented examples."""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from support_python.markdown.profiles import load_profile
from support_python.tools import agent_files as agent_files_mod
from support_python.tools import agent_files_config as cfg_mod
from support_python.tools import git_repository_backup as backup_mod

DOCS = Path(__file__).resolve().parents[2] / "docs" / "tools"


class _Recorder:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def warn(self, message: str, *args: object, **kwargs: object) -> None:
        self.messages.append(message)


def _first_json_block(doc_name: str) -> dict[str, Any]:
    text = (DOCS / doc_name).read_text(encoding="utf-8")
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    assert match is not None, doc_name
    return json.loads(match.group(1))


def _snake(data: Any) -> Any:
    """Return data with every dict key rewritten to snake_case, except tool names used as keys."""
    if isinstance(data, dict):
        return {k.replace("-", "_"): _snake(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_snake(v) for v in data]
    return data


def _run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = agent_files_mod.main(argv)
    return code, out.getvalue(), err.getvalue()


class ToolLevelKeyTests(unittest.TestCase):
    def test_kebab_tool_keys_build_the_same_tool_as_snake_keys(self) -> None:
        kebab = {
            "name": "x",
            "command": "x-cmd",
            "target-file": "t.md",
            "review-args": ["--prompt", "{prompt}"],
            "fallback-paths": ["f.md"],
            "skills-dir": "s",
            "native-skill-discovery": True,
            "legacy-skills-dirs": ["old"],
            "bootstrap-skill-names": ["b"],
            "aliases": ["y"],
        }
        tool_kebab = cfg_mod.build_tool_from_dict(kebab)
        tool_snake = cfg_mod.build_tool_from_dict(_snake(kebab))
        for attr in (
            "name",
            "command",
            "target_file",
            "fallback_paths",
            "skills_dir",
            "native_skill_discovery",
            "legacy_skills_dirs",
            "bootstrap_skill_names",
            "aliases",
        ):
            self.assertEqual(getattr(tool_kebab, attr), getattr(tool_snake, attr), attr)
        self.assertEqual(tool_kebab.review_args("p", "t", 1), tool_snake.review_args("p", "t", 1))
        self.assertEqual(tool_kebab.review_args("p", "t", 1), ["--prompt", "p"])
        self.assertTrue(tool_kebab.native_skill_discovery)

    def test_tool_key_clash_prefers_kebab_value_and_warns_once(self) -> None:
        logger = _Recorder()
        tool = cfg_mod.build_tool_from_dict(
            {"name": "x", "command": "c", "target_file": "old.md", "target-file": "new.md"}, logger=logger
        )
        self.assertEqual(tool.target_file, Path("new.md"))
        self.assertEqual(len(logger.messages), 1)
        self.assertIn("'x'", logger.messages[0])


class DocumentedExampleTests(unittest.TestCase):
    def test_agent_files_example_loads_without_warnings(self) -> None:
        example = _first_json_block("agent-files.md")
        logger = _Recorder()
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file = Path(tmp_dir).resolve() / ".agent-files.json"
            cfg_file.write_text(json.dumps(example), encoding="utf-8")
            config = cfg_mod.load_agent_files_config(cfg_file, logger=logger)
            self.assertEqual(logger.messages, [])
            self.assertTrue(all("_" not in key for key in example))
            self.assertEqual(config.marker, example["marker"])
            self.assertEqual(config.digest_path.name, example["digest-path"])
            self.assertIsNotNone(cfg_mod.ToolRegistry(config.tools).get("cursor-agent"))

    def test_lint_markdown_example_loads_without_warnings(self) -> None:
        example = _first_json_block("lint-markdown.md")
        logger = _Recorder()
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file = Path(tmp_dir) / ".lint-markdown.json"
            cfg_file.write_text(json.dumps(example), encoding="utf-8")
            profile = load_profile(cfg_file, logger=logger)
        self.assertEqual(logger.messages, [])
        self.assertTrue(all("_" not in key for key in example))
        self.assertIn("MD015", profile.enabled_rules)
        self.assertNotIn("MD018", profile.enabled_rules)

    def test_git_repository_backup_example_loads_without_warnings(self) -> None:
        example = _first_json_block("git-repository-backup.md")
        logger = _Recorder()
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file = Path(tmp_dir) / "config.json"
            cfg_file.write_text(json.dumps(example), encoding="utf-8")
            data = backup_mod.load_config(cfg_file, logger)
        self.assertEqual(logger.messages, [])
        self.assertEqual(data, example)


class AgentFilesConfigFlagIntegrationTests(unittest.TestCase):
    def _write_project(self, root: Path, kebab: bool) -> Path:
        (root / "agent-skills" / "demo").mkdir(parents=True, exist_ok=True)
        (root / "agent-digest.md").write_text("Digest body.\n", encoding="utf-8")
        (root / "agent-skills" / "demo" / "SKILL.md").write_text("---\nname: demo\n---\nDemo\n", encoding="utf-8")
        config = {
            "digest-path": "agent-digest.md",
            "skills-dir": "agent-skills",
            "replace-tools": True,
            "tools": [
                {
                    "name": "demo-tool",
                    "command": "demo-cmd",
                    "target-file": str(root / "targets" / "RULES.md"),
                    "skills-dir": str(root / "targets" / "skills"),
                    "native-skill-discovery": True,
                }
            ],
        }
        cfg_file = root / ".agent-files.json"
        cfg_file.write_text(json.dumps(config if kebab else _snake(config)), encoding="utf-8")
        return cfg_file

    def test_check_with_kebab_config_behaves_like_snake_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            results = {}
            for kebab in (True, False):
                cfg_file = self._write_project(root, kebab)
                pending = _run_main(["check", "--config", str(cfg_file)])
                sync = _run_main(["sync", "--config", str(cfg_file)])
                clean = _run_main(["check", "--config", str(cfg_file)])
                results[kebab] = (pending[0], sync[0], clean[0], clean[1] + clean[2])
                shutil.rmtree(root / "targets", ignore_errors=True)
            self.assertEqual(results[True], results[False])
            self.assertEqual(results[True][:3], (1, 0, 0))
            self.assertIn("already up to date", results[True][3])


if __name__ == "__main__":
    unittest.main()
