"""Environment file parsing and property configuration utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Union


def read_env_file(file_path: Union[str, Path]) -> dict[str, str]:
    """Parse a key=value properties or .env file into a dictionary.

    Lines that are empty or begin with ``#`` are ignored. Keys and values are stripped of
    surrounding whitespace, and values have single and double quotes trimmed.

    Args:
        file_path: Path to the properties or .env file to parse.

    Returns:
        Dictionary mapping environment property keys to their string values.
        Returns an empty dictionary if the file does not exist or cannot be read.
    """
    path = Path(file_path)
    env_vars: dict[str, str] = {}
    if not path.is_file():
        return env_vars

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return env_vars

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'\"")
        env_vars[k] = v

    return env_vars


__all__ = ["read_env_file"]
