"""Tests for the shared configuration key normalizer."""

from __future__ import annotations

import unittest

from support_python.config import normalize_config_keys


class _Recorder:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.debugs: list[str] = []

    def warn(self, message: str, *args: object, **kwargs: object) -> None:
        self.messages.append(message)

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        self.debugs.append(message)


class NormalizeConfigKeysTests(unittest.TestCase):
    def test_kebab_and_snake_twins_normalize_identically(self) -> None:
        kebab = {"digest-path": "a", "skills-dir": "b"}
        snake = {"digest_path": "a", "skills_dir": "b"}
        self.assertEqual(normalize_config_keys(kebab), normalize_config_keys(snake))
        self.assertEqual(normalize_config_keys(kebab), {"digest_path": "a", "skills_dir": "b"})

    def test_kebab_output_style(self) -> None:
        self.assertEqual(normalize_config_keys({"seven_zip": 1, "roots": []}, style="kebab"), {"seven-zip": 1, "roots": []})

    def test_both_spellings_use_kebab_value_and_warn_once(self) -> None:
        logger = _Recorder()
        result = normalize_config_keys({"digest_path": "old", "digest-path": "new"}, source="x.json", logger=logger)
        self.assertEqual(result, {"digest_path": "new"})
        self.assertEqual(len(logger.messages), 1)
        self.assertIn("digest-path", logger.messages[0])

    def test_kebab_wins_regardless_of_order(self) -> None:
        result = normalize_config_keys({"digest-path": "new", "digest_path": "old"}, logger=_Recorder())
        self.assertEqual(result, {"digest_path": "new"})

    def test_values_are_not_touched(self) -> None:
        nested = {"some_name": 1}
        self.assertEqual(normalize_config_keys({"tools": nested}), {"tools": nested})


if __name__ == "__main__":
    unittest.main()


class _SettingsFixture(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        from pathlib import Path

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.project_dir = self.root / "project"
        self.project_dir.mkdir()
        self.xdg = self.root / "xdg"
        self.system_file = self.root / "system" / "config.json"
        self.environ: dict[str, str] = {"XDG_CONFIG_HOME": str(self.xdg)}

    def schema(self, **kwargs: object):
        from support_python.config import Setting, SettingsSchema

        settings = [
            Setting("retries", "integer", 3, "Number of retries."),
            Setting("endpoint", "string", "https://default", "Service endpoint."),
            Setting("labels", "dict", {}, "Labels to attach."),
            Setting("token", "string", None, "API token.", secret=True),
            Setting("timeout", "duration", 30.0, "Request timeout."),
            Setting("verbose-mode", "boolean", False, "Verbose mode."),
            Setting("roots", "list", [], "Root folders."),
        ]
        return SettingsSchema(
            "demo", settings, project_dir=self.project_dir, environ=self.environ, system_path=self.system_file, **kwargs
        )

    @staticmethod
    def write(path, data: dict) -> None:
        import json

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")


class ResolveSettingsTests(_SettingsFixture):
    def test_each_source_wins_over_every_lower_source(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()

        def seen(**kwargs: object) -> tuple[object, str]:
            got = resolve_settings(schema, **kwargs)["retries"]
            return got.value, got.source

        self.assertEqual(seen(), (3, "default"))
        self.write(self.system_file, {"retries": 1})
        self.assertEqual(seen(), (1, "system"))
        self.write(schema.path("user"), {"retries": 2})
        self.assertEqual(seen(), (2, "user"))
        self.write(schema.path("project"), {"retries": 4})
        self.assertEqual(seen(), (4, "project"))
        self.environ["DEMO_RETRIES"] = "5"
        self.assertEqual(seen(), (5, "env"))
        self.assertEqual(seen(cli={"retries": "6"}), (6, "cli"))

    def test_project_file_name_and_snake_case_keys(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()
        self.assertEqual(schema.path("project").name, ".demo.json")
        self.write(schema.path("project"), {"verbose_mode": True})
        got = resolve_settings(schema)["verbose-mode"]
        self.assertEqual((got.value, got.source), (True, "project"))

    def test_alias_keys_map_to_the_setting_and_the_setting_key_wins(self) -> None:
        from support_python.config import Setting, SettingsSchema, resolve_settings

        schema = SettingsSchema(
            "demo",
            [Setting("exclude", "list", [], "Excluded.", aliases=("excludes",))],
            project_dir=self.project_dir,
            environ=self.environ,
            system_path=self.system_file,
        )
        self.write(schema.path("project"), {"excludes": ["a"]})
        self.assertEqual(resolve_settings(schema)["exclude"].value, ["a"])
        self.write(schema.path("project"), {"excludes": ["a"], "exclude": ["b"]})
        self.assertEqual(resolve_settings(schema)["exclude"].value, ["b"])

    def test_env_name_derivation_and_empty_is_unset(self) -> None:
        from support_python.config import resolve_settings

        self.environ["DEMO_VERBOSE_MODE"] = "yes"
        self.assertTrue(resolve_settings(self.schema())["verbose-mode"].value)
        self.environ["DEMO_VERBOSE_MODE"] = ""
        self.assertEqual(resolve_settings(self.schema())["verbose-mode"].source, "default")

    def test_dictionary_merges_key_by_key_across_tiers(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()
        self.write(schema.path("user"), {"labels": {"a": "user", "b": "user"}})
        self.write(schema.path("project"), {"labels": {"b": "project", "c": "project"}})
        got = resolve_settings(schema)["labels"]
        self.assertEqual(got.value, {"a": "user", "b": "project", "c": "project"})
        self.assertEqual(got.source, "project")

    def test_invalid_env_value_warns_once_and_falls_through(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()
        self.write(schema.path("project"), {"retries": 7})
        self.environ["DEMO_RETRIES"] = "many"
        logger = _Recorder()
        got = resolve_settings(schema, logger=logger)["retries"]
        self.assertEqual((got.value, got.source), (7, "project"))
        self.assertEqual(len(logger.messages), 1)
        self.assertIn("DEMO_RETRIES", logger.messages[0])

    def test_unreadable_file_warns_and_is_ignored(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()
        schema.path("project").write_text("{not json", encoding="utf-8")
        logger = _Recorder()
        self.assertEqual(resolve_settings(schema, logger=logger)["retries"].source, "default")
        self.assertEqual(len(logger.messages), 1)
        self.assertIn(".demo.json", logger.messages[0])

    def test_unknown_keys_are_ignored_and_listed_at_debug(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()
        self.write(schema.path("project"), {"mystery": 1})
        logger = _Recorder()
        resolve_settings(schema, logger=logger)
        self.assertEqual(logger.messages, [])
        self.assertIn("mystery", logger.debugs[0])

    def test_config_option_replaces_discovery(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()
        self.write(schema.path("project"), {"retries": 4})
        other = self.root / "other.json"
        self.write(other, {"endpoint": "x"})
        got = resolve_settings(schema, config_path=other)
        self.assertEqual(got["retries"].source, "default")
        self.assertEqual(got["endpoint"].value, "x")

    def test_value_types(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema()
        self.write(schema.path("project"), {"timeout": "1m", "roots": ["a", "b"]})
        self.environ["DEMO_LABELS"] = '{"k": "v"}'
        got = resolve_settings(schema)
        self.assertEqual(got["timeout"].value, 60.0)
        self.assertEqual(got["roots"].value, ["a", "b"])
        self.assertEqual(got["labels"].value, {"k": "v"})
        self.assertEqual(resolve_settings(schema, cli={"roots": "x,y"})["roots"].value, ["x", "y"])

    def test_tiers_limit_supported_files(self) -> None:
        from support_python.config import resolve_settings

        schema = self.schema(tiers=("user",))
        self.write(schema.path("project"), {"retries": 4})
        self.assertEqual(resolve_settings(schema)["retries"].source, "default")
