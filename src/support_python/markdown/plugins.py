"""Loader for Markdown lint rule plugins given as Python file paths or dotted module names."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Iterable

from support_python.markdown.registry import Rule, RuleRegistry


class PluginError(ValueError):
    """Raised when a rule plugin cannot be loaded or registers a conflicting rule."""


class _StagingRegistry(RuleRegistry):
    """Empty registry collecting one plugin's rules, rejecting duplicate rule IDs within the plugin."""

    def __init__(self) -> None:
        super().__init__([])

    def register(self, rule: Rule) -> None:
        """Register rule, raising ValueError when its rule ID is already staged."""
        if isinstance(rule, Rule) and rule.rule_id.strip().upper() in self.rule_ids():
            raise ValueError(f"rule ID '{rule.rule_id.strip().upper()}' is registered twice")
        super().register(rule)


def _import_path_plugin(entry: str, path: Path) -> ModuleType:
    """Import a plugin file under a module name unique to its resolved path."""
    if not path.is_file():
        raise PluginError(f"Plugin '{entry}': file not found: {path}")
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    module_name = f"_lint_markdown_plugin_{path.stem}_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PluginError(f"Plugin '{entry}': failed to import: unsupported file {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise PluginError(f"Plugin '{entry}': failed to import: {exc}") from exc
    return module


def _import_module_plugin(entry: str) -> ModuleType:
    """Import a plugin by dotted module name."""
    try:
        return importlib.import_module(entry)
    except Exception as exc:
        raise PluginError(f"Plugin '{entry}': failed to import: {exc}") from exc


def load_plugins(
    entries: Iterable[str],
    registry: RuleRegistry,
    base_dir: Path | None = None,
    *,
    loaded: set[str] | None = None,
) -> dict[str, str]:
    """Load each plugin entry into registry and return a mapping of added uppercase rule IDs to their plugin entry.

    An entry ending in '.py' is a file path relative to base_dir (default: the current directory);
    any other entry is a dotted module name. Each plugin's module-level 'register(registry)' is called;
    a plugin's rules are added only when all of them register cleanly and none collides with a registered rule ID.
    Entries already in loaded (resolved paths or module names) are skipped; pass one set across calls to
    load each plugin once when entries come from several sources.
    """
    base = base_dir if base_dir is not None else Path.cwd()
    sources: dict[str, str] = {}
    loaded = loaded if loaded is not None else set()
    for entry in entries:
        is_path = entry.endswith(".py")
        path = (base / entry).resolve() if is_path else None
        key = str(path) if path is not None else entry
        if key in loaded:
            continue
        loaded.add(key)
        module = _import_path_plugin(entry, path) if path is not None else _import_module_plugin(entry)
        register = getattr(module, "register", None)
        if not callable(register):
            raise PluginError(f"Plugin '{entry}': does not define a callable 'register'")
        staging = _StagingRegistry()
        try:
            register(staging)
        except Exception as exc:
            raise PluginError(f"Plugin '{entry}': register() failed: {exc}") from exc
        for rule_id in staging.rule_ids():
            if rule_id in registry.rule_ids():
                raise PluginError(f"Plugin '{entry}': rule ID '{rule_id}' is already registered")
        for rule in staging:
            registry.register(rule)
        sources.update(dict.fromkeys(staging.rule_ids(), entry))
    return sources


__all__ = ["PluginError", "load_plugins"]
