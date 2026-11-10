"""Tests for the shared configuration key normalizer."""

from __future__ import annotations

import unittest

from support_python.config import normalize_config_keys


class _Recorder:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def warn(self, message: str, *args: object, **kwargs: object) -> None:
        self.messages.append(message)


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
