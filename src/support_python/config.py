"""Shared configuration key normalization: kebab-case and snake_case keys are interchangeable."""

from __future__ import annotations

from typing import Any, Literal


def normalize_config_keys(
    data: dict[str, Any],
    *,
    style: Literal["snake", "kebab"] = "snake",
    source: object | None = None,
    logger: Any | None = None,
) -> dict[str, Any]:
    """Return a copy of data whose top-level keys use one spelling, snake_case or kebab-case.

    When a file sets the same key in both spellings, the kebab-case value wins and one warning is logged.
    Values are returned untouched.
    """
    sep = "_" if style == "snake" else "-"
    result: dict[str, Any] = {}
    kebab_seen: set[str] = set()
    for key, value in data.items():
        canonical = key.replace("_", sep).replace("-", sep)
        is_kebab = "-" in key
        if canonical in result:
            if logger is None:
                from support_python.logging import CliLogger

                logger = CliLogger()
            where = f" in {source}" if source is not None else ""
            logger.warn(f"Config key '{canonical.replace('_', '-')}' is set in both spellings{where}; using the kebab-case value.")
            if not is_kebab or canonical in kebab_seen:
                continue
        if is_kebab:
            kebab_seen.add(canonical)
        result[canonical] = value
    return result


def kebab_keys(keys: Any) -> list[str]:
    """Return the sorted keys spelled in kebab-case, for error messages."""
    return sorted(str(key).replace("_", "-") for key in keys)
