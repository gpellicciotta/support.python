"""Loadable JSON lint profiles ('default' and 'dev-guidelines') for Markdown linting."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Any, Iterable

from support_python.config import kebab_keys, normalize_config_keys
from support_python.markdown.registry import RuleRegistry
from support_python.markdown.rules import DEFAULT_REGISTRY

DEFAULT_CONFIG_FILENAME = ".lint-markdown.json"
LEGACY_CONFIG_FILENAME = ".markdown-lint.json"

ALL_RULE_IDS: frozenset[str] = frozenset(DEFAULT_REGISTRY.rule_ids())
#: Every rule except ``MD015``; no built-in profile uses this set any more.
GENERIC_RULE_IDS: frozenset[str] = frozenset(rid for rid in ALL_RULE_IDS if rid != "MD015")

_ALLOWED_PROFILE_KEYS = frozenset(
    {
        "profile",
        "rules",
        "enabled_rules",
        "enable",
        "enable_rules",
        "disable",
        "disable_rules",
        "disabled_rules",
        "historical_task_exemptions",
        "historical_tasks",
        "exclude",
        "excludes",
        "plugins",
        "github_owners",
    }
)


@dataclass(frozen=True)
class LintProfile:
    """Configuration profile controlling active Markdown lint rules and historical exemptions."""

    name: str
    enabled_rules: frozenset[str]
    historical_task_exemptions: bool = False
    excludes: tuple[str, ...] = ()
    github_owners: tuple[str, ...] = ()


DEFAULT_PROFILE = LintProfile(
    name="default",
    enabled_rules=ALL_RULE_IDS,
    historical_task_exemptions=False,
)

DEV_GUIDELINES_PROFILE = LintProfile(
    name="dev-guidelines",
    enabled_rules=ALL_RULE_IDS,
    historical_task_exemptions=True,
)

PROFILES: dict[str, LintProfile] = {
    "default": DEFAULT_PROFILE,
    "dev-guidelines": DEV_GUIDELINES_PROFILE,
}


def _validate_rule_ids(rule_ids: Iterable[Any], registry: RuleRegistry) -> frozenset[str]:
    """Validate an iterable of rule IDs or names against registry and return canonical uppercase IDs."""
    validated: set[str] = set()
    for raw in rule_ids:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"Rule identifier must be a non-empty string, got: {raw!r}")
        rule = registry.get(raw)
        if rule is None:
            raise ValueError(f"Unknown rule ID: '{raw}'")
        validated.add(rule.rule_id)
    return frozenset(validated)


def get_profile(name: str, registry: RuleRegistry | None = None) -> LintProfile:
    """Return a built-in LintProfile by name, also enabling registry rules beyond the built-in ones."""
    clean = name.strip().lower() if isinstance(name, str) else ""
    if clean not in PROFILES:
        raise ValueError(f"Unknown profile: '{name}' (expected one of: {', '.join(sorted(PROFILES))})")
    base = PROFILES[clean]
    if registry is None:
        return base
    _validate_rule_ids(base.enabled_rules, registry)
    extra_rule_ids = frozenset(registry.rule_ids()) - ALL_RULE_IDS
    return replace(base, enabled_rules=base.enabled_rules | extra_rule_ids) if extra_rule_ids else base


def _resolve_dir_config_file(directory: Path) -> Path | None:
    """Find '.lint-markdown.json' or fallback '.markdown-lint.json' inside directory."""
    primary = directory / DEFAULT_CONFIG_FILENAME
    if primary.is_file():
        return primary
    legacy = directory / LEGACY_CONFIG_FILENAME
    if legacy.is_file():
        return legacy
    return None


def resolve_config_file(config_path: Path) -> Path:
    """Return config_path, or the config file inside it when config_path is a directory."""
    if not config_path.is_dir():
        return config_path
    return _resolve_dir_config_file(config_path) or (config_path / DEFAULT_CONFIG_FILENAME)


def read_plugin_entries(config_path: Path | None) -> list[str]:
    """Return the validated 'plugins' entries of a '.lint-markdown.json' file, or an empty list."""
    if config_path is None or not config_path.is_file():
        return []
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON in {config_path}: {exc}") from exc
    entries = raw.get("plugins", []) if isinstance(raw, dict) else []
    if not isinstance(entries, list) or not all(isinstance(x, str) and x.strip() for x in entries):
        raise ValueError(f"'plugins' must be a list of non-empty strings in {config_path}")
    return [x.strip() for x in entries]


def load_profile(
    config_path: Path | str | None = None,
    *,
    profile: str | LintProfile | None = None,
    registry: RuleRegistry | None = None,
    logger: Any | None = None,
) -> LintProfile:
    """Load and validate a LintProfile from a '.lint-markdown.json' path or built-in profile name."""
    reg = registry if registry is not None else DEFAULT_REGISTRY

    if isinstance(profile, LintProfile):
        base = LintProfile(
            name=profile.name,
            enabled_rules=_validate_rule_ids(profile.enabled_rules, reg),
            historical_task_exemptions=profile.historical_task_exemptions,
            excludes=profile.excludes,
            github_owners=profile.github_owners,
        )

    elif isinstance(profile, str):
        base = get_profile(profile, reg)
    else:
        base = get_profile(DEFAULT_PROFILE.name, reg)

    if isinstance(config_path, str) and config_path.strip().lower() in PROFILES and not Path(config_path).exists():
        return get_profile(config_path, reg)

    target: Path | None = None
    if config_path is not None:
        target = resolve_config_file(Path(config_path).expanduser())
    elif profile is None:
        target = _resolve_dir_config_file(Path.cwd())

    if target is None or not target.exists():
        return base

    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON in {target}: {exc}") from exc

    if isinstance(raw, dict):
        raw = normalize_config_keys(raw, source=target, logger=logger)
    if not isinstance(raw, dict) or (set(raw.keys()) - _ALLOWED_PROFILE_KEYS):
        unknown = kebab_keys(set(raw.keys()) - _ALLOWED_PROFILE_KEYS) if isinstance(raw, dict) else []
        raise ValueError(f"Invalid profile schema in {target}: unknown keys {unknown}")

    if "profile" in raw and profile is None:
        if not isinstance(raw["profile"], str):
            raise ValueError("'profile' must be a string")
        base = get_profile(raw["profile"], reg)

    enabled = set(base.enabled_rules)
    rules_raw = raw.get("rules", raw.get("enabled_rules"))
    if rules_raw is not None:
        if isinstance(rules_raw, dict):
            enabled = set(base.enabled_rules)
            for k, v in rules_raw.items():
                rid = next(iter(_validate_rule_ids([k], reg)))
                if not isinstance(v, bool):
                    raise ValueError(f"Rule toggle for '{k}' must be a boolean")
                enabled.add(rid) if v else enabled.discard(rid)
        elif isinstance(rules_raw, list):
            enabled = set(_validate_rule_ids(rules_raw, reg))
        else:
            raise ValueError("'rules' must be a list of rule IDs or a boolean mapping")

    enable_raw = raw.get("enable", raw.get("enable_rules"))
    if enable_raw is not None:
        if not isinstance(enable_raw, list):
            raise ValueError("'enable' must be a list of rule IDs")
        enabled |= _validate_rule_ids(enable_raw, reg)

    disable_raw = raw.get("disable", raw.get("disable_rules", raw.get("disabled_rules")))
    if disable_raw is not None:
        if not isinstance(disable_raw, list):
            raise ValueError("'disable' must be a list of rule IDs")
        enabled -= _validate_rule_ids(disable_raw, reg)

    hist = raw.get("historical_task_exemptions", raw.get("historical_tasks", base.historical_task_exemptions))
    if not isinstance(hist, bool):
        raise ValueError("'historical_task_exemptions' must be a boolean")

    excl_raw = raw.get("exclude", raw.get("excludes", list(base.excludes)))
    if not isinstance(excl_raw, list) or not all(isinstance(x, str) and x.strip() for x in excl_raw):
        raise ValueError("'excludes' must be a list of non-empty strings")

    owners_raw = raw.get("github_owners", list(base.github_owners))
    if not isinstance(owners_raw, list) or not all(isinstance(x, str) and x.strip() for x in owners_raw):
        raise ValueError(f"'github-owners' must be a list of non-empty strings in {target}")

    return LintProfile(
        name=base.name,
        enabled_rules=frozenset(enabled),
        historical_task_exemptions=hist,
        excludes=tuple(x.strip() for x in excl_raw),
        github_owners=tuple(x.strip() for x in owners_raw),
    )


__all__ = [
    "ALL_RULE_IDS",
    "DEFAULT_CONFIG_FILENAME",
    "DEFAULT_PROFILE",
    "DEV_GUIDELINES_PROFILE",
    "GENERIC_RULE_IDS",
    "LEGACY_CONFIG_FILENAME",
    "LintProfile",
    "PROFILES",
    "get_profile",
    "load_profile",
    "read_plugin_entries",
    "resolve_config_file",
]
