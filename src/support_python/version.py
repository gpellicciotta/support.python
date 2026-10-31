"""Project and package version resolution utilities."""

from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import re
from typing import Optional, Union


def get_project_version(search_dir: Optional[Union[str, Path]] = None) -> str:
    """Resolve the current project version from project descriptor files or environment.

    Searches upwards from the specified directory inspecting common project metadata files:
    1. ``gradle.properties`` (looking for ``version = <ver>``)
    2. ``server/build.gradle``, ``build.gradle``, or Kotlin DSL equivalents (``version = '<ver>'``)
    3. ``clients/python/pyproject.toml`` or ``pyproject.toml`` (``version = "<ver>"``)
    4. Environment variable ``PROJECT_VERSION``
    5. Fallback string ``"0.0.0+unknown"`` if no version can be discovered.

    Args:
        search_dir: Path to start searching upwards from. Defaults to the current working directory.

    Returns:
        Resolved semantic version string, or ``"0.0.0+unknown"`` if none is found.
    """
    start_dir = Path(search_dir).resolve() if search_dir is not None else Path.cwd().resolve()

    # Traverse start_dir and all its parent directories
    dirs_to_check: list[Path] = [start_dir]
    dirs_to_check.extend(start_dir.parents)

    for directory in dirs_to_check:
        # 1. Check gradle.properties
        gradle_props = directory / "gradle.properties"
        if gradle_props.is_file():
            try:
                text = gradle_props.read_text(encoding="utf-8")
                match = re.search(r"^version\s*=\s*(\S+)", text, re.MULTILINE)
                if match:
                    ver = match.group(1).strip()
                    if ver and ver != "unspecified":
                        return ver
            except OSError:
                pass

        # 2. Check server/build.gradle or build.gradle
        for gradle_name in ("server/build.gradle", "build.gradle", "server/build.gradle.kts", "build.gradle.kts"):
            gradle_file = directory / gradle_name
            if gradle_file.is_file():
                try:
                    text = gradle_file.read_text(encoding="utf-8")
                    match = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", text)
                    if match:
                        ver = match.group(1).strip()
                        if ver and ver != "unspecified":
                            return ver
                except OSError:
                    pass

        # 3. Check clients/python/pyproject.toml or pyproject.toml
        for toml_name in ("clients/python/pyproject.toml", "pyproject.toml"):
            toml_file = directory / toml_name
            if toml_file.is_file():
                try:
                    text = toml_file.read_text(encoding="utf-8")
                    match = re.search(r'version\s*=\s*"([^"]+)"', text)
                    if match:
                        ver = match.group(1).strip()
                        if ver:
                            return ver
                except OSError:
                    pass

    # Check environment variable fallback
    env_ver = os.environ.get("PROJECT_VERSION")
    if env_ver:
        return env_ver.strip()

    return "0.0.0+unknown"


def get_package_version(distribution: str) -> str:
    """Resolve an installed distribution's version, restoring the ``-pre`` suffix of in-development versions.

    Packaging tools normalize ``2.0.1-pre`` to ``2.0.1rc0`` in installed metadata. This maps that form back to
    the ``-pre`` form used in ``pyproject.toml`` and ``CHANGELOG.md``.

    Args:
        distribution: Installed distribution name, such as ``"support-python"``.

    Returns:
        Version string, or ``"0.0.0+unknown"`` if the distribution is not installed.
    """
    try:
        version = importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0+unknown"
    return re.sub(r"rc0$", "-pre", version)


__all__ = ["get_package_version", "get_project_version"]
