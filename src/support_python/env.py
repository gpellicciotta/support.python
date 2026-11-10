"""Environment file parsing and property configuration utilities."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Mapping, Optional, Union


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


def user_config_dir(tool_name: str, *, environ: Optional[Mapping[str, str]] = None, platform: Optional[str] = None) -> Path:
    """Return the per-user configuration directory of ``tool_name``, per the configuration guidelines.

    The first location that applies wins:

    1. ``$XDG_CONFIG_HOME/{tool_name}`` on any platform, when ``XDG_CONFIG_HOME`` is an absolute path.
    2. On Windows, ``%APPDATA%/{tool_name}`` when ``APPDATA`` is absolute, else ``~/AppData/Roaming/{tool_name}``.
    3. Elsewhere, ``~/.config/{tool_name}``.

    The directory is only computed, never created. ``platform`` only picks the branch: paths are always host-native,
    and whether ``XDG_CONFIG_HOME`` or ``APPDATA`` is absolute follows the host's path rules.

    Args:
        tool_name: Tool or application name used as the directory name.
        environ: Environment variables to read; defaults to :data:`os.environ`.
        platform: Platform identifier in :data:`sys.platform` form; defaults to :data:`sys.platform`.

    Returns:
        The configuration directory path.

    Raises:
        ValueError: If ``tool_name`` is empty, ``.``, ``..``, or contains ``/``, ``\\``, or ``:``.
    """
    if tool_name in ("", ".", "..") or any(char in tool_name for char in "/\\:"):
        raise ValueError(f"Invalid tool name for a configuration directory: {tool_name!r}")
    env = os.environ if environ is None else environ
    xdg_config_home = env.get("XDG_CONFIG_HOME", "")
    if xdg_config_home and Path(xdg_config_home).is_absolute():
        return Path(xdg_config_home) / tool_name
    if (platform if platform is not None else sys.platform).startswith("win"):
        app_data = env.get("APPDATA", "")
        if app_data and Path(app_data).is_absolute():
            return Path(app_data) / tool_name
        return Path.home() / "AppData" / "Roaming" / tool_name
    return Path.home() / ".config" / tool_name


def user_config_path(
    tool_name: str,
    filename: str = "config.json",
    *,
    environ: Optional[Mapping[str, str]] = None,
    platform: Optional[str] = None,
) -> Path:
    """Return the per-user configuration file of ``tool_name``: ``filename`` inside :func:`user_config_dir`.

    Args:
        tool_name: Tool or application name used as the directory name.
        filename: Configuration file name, not a path; defaults to ``config.json``.
        environ: Environment variables to read; defaults to :data:`os.environ`.
        platform: Platform identifier in :data:`sys.platform` form; defaults to :data:`sys.platform`.

    Returns:
        The configuration file path, which may not exist.

    Raises:
        ValueError: If ``tool_name`` is empty, ``.``, ``..``, or contains ``/``, ``\\``, or ``:``.
    """
    return user_config_dir(tool_name, environ=environ, platform=platform) / filename


__all__ = ["read_env_file", "user_config_dir", "user_config_path"]
