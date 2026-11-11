"""Shared configuration support: key normalization, the settings resolver, and the ``config`` command group."""

from __future__ import annotations

import copy
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Literal, Mapping, Optional, Sequence

from support_python.durations import parse_duration_to_seconds
from support_python.env import user_config_path
from support_python.files import atomic_write_text

if TYPE_CHECKING:
    import argparse

    from support_python.cli import ToolHarness
    from support_python.logging import CliLogger


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


# Settings declaration, resolution, and the ``config`` command group.
#
# The precedence and file locations follow the dev-guidelines Configuration Guidelines:
# command line, environment, project file, user file, system file, defaults.

#: Value types a :class:`Setting` can declare.
SETTING_TYPES = ("string", "integer", "float", "boolean", "duration", "list", "dict")

#: Configuration file tiers, highest precedence first.
TIERS = ("project", "user", "system")

_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
_TRUE_WORDS = frozenset({"true", "1", "yes", "on"})
_FALSE_WORDS = frozenset({"false", "0", "no", "off"})
_SECRET_MASK = "***"


@dataclass(frozen=True)
class Setting:
    """Declaration of one setting.

    Attributes:
        name: Lowercase kebab-case name; underscores are accepted and converted to dashes.
        type: One of :data:`SETTING_TYPES`. Durations resolve to seconds as a float.
        default: Value used when no source provides one.
        description: One-sentence description shown by ``config list --verbose`` and ``config names --verbose``.
        secret: Print the value as ``***`` in ``config list`` and ``config get``.
        aliases: Other file keys that mean this setting; the setting's own key wins when a file has both.
        normalize: Converts a raw file, environment, or command-line value before it is parsed; raises ``ValueError``
            for a value it rejects. ``config set`` does not apply it.
    """

    name: str
    type: str = "string"
    default: Any = None
    description: str = ""
    secret: bool = False
    aliases: tuple[str, ...] = ()
    normalize: Optional[Callable[[Any], Any]] = None

    def __post_init__(self) -> None:
        name = self.name.replace("_", "-")
        if not _NAME_PATTERN.match(name):
            raise ValueError(f"Invalid setting name {self.name!r}: use lowercase letters, digits, dashes, and dots.")
        if self.type not in SETTING_TYPES:
            raise ValueError(f"Invalid type {self.type!r} for setting {name!r}: use one of {', '.join(SETTING_TYPES)}.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "aliases", tuple(alias.replace("_", "-") for alias in self.aliases))


class SettingsSchema:
    """The settings of one tool plus where its configuration files live.

    Args:
        tool: Tool name; names the project file ``.{tool}.json`` and the user and system directories.
        settings: The declared settings, with unique names.
        env_prefix: Environment variable prefix; defaults to the upper-cased tool name. A trailing underscore is optional.
        tiers: File tiers the tool supports, from ``project``, ``user``, and ``system``.
        project_dir: Folder of the project file; defaults to the current directory at lookup time.
        project_file: Project file name; defaults to ``.{tool}.json``.
        system_path: System file path; defaults to ``%PROGRAMDATA%/{tool}/config.json`` or ``/etc/{tool}/config.json``.
        environ: Environment variables to read; defaults to :data:`os.environ`.
        platform: Platform identifier in :data:`sys.platform` form; defaults to :data:`sys.platform`.

    Raises:
        ValueError: A setting name repeats, or a tier is unknown.
    """

    def __init__(
        self,
        tool: str,
        settings: Sequence[Setting],
        *,
        env_prefix: Optional[str] = None,
        tiers: Sequence[str] = TIERS,
        project_dir: Optional[Path | str] = None,
        project_file: Optional[str] = None,
        system_path: Optional[Path | str] = None,
        environ: Optional[Mapping[str, str]] = None,
        platform: Optional[str] = None,
    ) -> None:
        self.tool = tool
        self.settings: dict[str, Setting] = {}
        for setting in settings:
            if setting.name in self.settings:
                raise ValueError(f"Duplicate setting name {setting.name!r}.")
            self.settings[setting.name] = setting
        unknown = [tier for tier in tiers if tier not in TIERS]
        if unknown:
            raise ValueError(f"Unknown tiers {unknown}: use {', '.join(TIERS)}.")
        self.tiers = tuple(tier for tier in TIERS if tier in tiers)
        prefix = env_prefix if env_prefix is not None else tool.upper().replace("-", "_")
        self.env_prefix = prefix.rstrip("_")
        self.project_dir = Path(project_dir) if project_dir is not None else None
        self.project_file = project_file if project_file is not None else f".{tool}.json"
        self.system_path = Path(system_path) if system_path is not None else None
        self.environ: Mapping[str, str] = os.environ if environ is None else environ
        self.platform = platform if platform is not None else sys.platform

    def get(self, name: str) -> Optional[Setting]:
        """Return the setting called ``name`` (either spelling), or ``None``."""
        return self.settings.get(name.replace("_", "-"))

    def env_var(self, name: str) -> str:
        """Return the environment variable of a setting: prefix plus the upper-cased name, dashes and dots as underscores."""
        key = name.replace("_", "-").upper().replace("-", "_").replace(".", "_")
        return f"{self.env_prefix}_{key}" if self.env_prefix else key

    def path(self, tier: str) -> Path:
        """Return the file path of ``tier``, which may not exist.

        Raises:
            ValueError: ``tier`` is not one of :data:`TIERS`.
        """
        if tier == "project":
            return (self.project_dir if self.project_dir is not None else Path.cwd()) / self.project_file
        if tier == "user":
            return user_config_path(self.tool, environ=self.environ, platform=self.platform)
        if tier == "system":
            if self.system_path is not None:
                return self.system_path
            if self.platform.startswith("win"):
                return Path(self.environ.get("PROGRAMDATA") or "C:/ProgramData") / self.tool / "config.json"
            return Path("/etc") / self.tool / "config.json"
        raise ValueError(f"Unknown tier {tier!r}: use {', '.join(TIERS)}.")


@dataclass(frozen=True)
class ResolvedSetting:
    """A setting with its effective value and the source that provided it (``cli``, ``env``, a tier, or ``default``)."""

    setting: Setting
    value: Any
    source: str

    @property
    def name(self) -> str:
        """The setting name."""
        return self.setting.name


def parse_setting_value(setting: Setting, raw: Any) -> Any:
    """Convert ``raw`` to the type of ``setting``.

    Text, from the command line, environment, or ``config set``, is parsed: booleans accept true/false/yes/no/on/off/1/0,
    durations accept ``30s``, ``1h30m`` and the like, lists accept a JSON array or comma-separated items, and
    dictionaries accept a JSON object. Other values, from JSON files, must already have the right type.

    Raises:
        ValueError: The value does not fit the type.
    """
    kind = setting.type
    if isinstance(raw, str):
        text = raw.strip()
        if kind == "string":
            return raw
        if kind == "integer":
            try:
                return int(text)
            except ValueError:
                raise ValueError(f"expected an integer, got {raw!r}") from None
        if kind == "float":
            try:
                return float(text)
            except ValueError:
                raise ValueError(f"expected a number, got {raw!r}") from None
        if kind == "boolean":
            if text.lower() in _TRUE_WORDS:
                return True
            if text.lower() in _FALSE_WORDS:
                return False
            raise ValueError(f"expected true or false, got {raw!r}")
        if kind == "duration":
            seconds = parse_duration_to_seconds(text)
            if seconds is None:
                raise ValueError(f"expected a duration such as 30s or 1h30m, got {raw!r}")
            return seconds
        if kind == "list":
            if text.startswith("["):
                try:
                    return parse_setting_value(setting, json.loads(text))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"expected a JSON array or comma-separated items: {exc}") from None
            return [part.strip() for part in text.split(",") if part.strip()]
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"expected a JSON object: {exc}") from None
        return parse_setting_value(setting, decoded)
    is_number = isinstance(raw, (int, float)) and not isinstance(raw, bool)
    if kind == "string" and isinstance(raw, str):
        return raw
    if kind == "integer" and isinstance(raw, int) and not isinstance(raw, bool):
        return raw
    if kind == "float" and is_number:
        return float(raw)
    if kind == "boolean" and isinstance(raw, bool):
        return raw
    if kind == "duration" and is_number and raw >= 0:
        return float(raw)
    if kind == "list" and isinstance(raw, list) and all(isinstance(item, str) for item in raw):
        return list(raw)
    if kind == "dict" and isinstance(raw, dict):
        return dict(raw)
    raise ValueError(f"expected a {kind}, got {json.dumps(raw)}")


def _reason(setting: Setting, exc: ValueError) -> str:
    """Return the error text for a bad value, without the value itself when the setting is secret."""
    return f"expected a {setting.type}" if setting.secret else str(exc)


def resolve_settings(
    schema: SettingsSchema,
    *,
    cli: Optional[Mapping[str, Any]] = None,
    config_path: Optional[Path | str] = None,
    logger: Any | None = None,
) -> dict[str, ResolvedSetting]:
    """Resolve every setting of ``schema`` by the guideline precedence.

    Order: ``cli``, environment, project file, user file, system file, defaults. The first valid value wins, except
    dictionaries, which merge key by key across all sources, with the highest source's keys winning. An invalid value
    or an unreadable file warns once and falls through to the next source; unknown keys are ignored and listed at debug
    level.

    Args:
        schema: The declared settings.
        cli: Values given on the command line, by setting name; ``None`` means not given.
        config_path: A ``--config`` file that replaces automatic discovery of the files.
        logger: Receives warnings and debug messages; defaults to a new :class:`~support_python.logging.CliLogger`.

    Returns:
        The resolved settings by name, in declaration order.
    """
    if logger is None:
        from support_python.logging import CliLogger

        logger = CliLogger()
    warned: set[str] = set()

    def warn(message: str) -> None:
        if message not in warned:
            warned.add(message)
            logger.warn(message)

    cli_values = {str(key).replace("_", "-"): value for key, value in (cli or {}).items() if value is not None}
    files: list[tuple[str, Path, dict[str, Any]]] = []
    candidates = [("project", Path(config_path))] if config_path is not None else [(t, schema.path(t)) for t in schema.tiers]
    for tier, path in candidates:
        data = _load_config_file(path, schema, logger, warn)
        if data is not None:
            files.append((tier, path, data))

    if config_path is not None and not Path(config_path).is_file():
        warn(f"Configuration file {config_path} does not exist.")
    resolved: dict[str, ResolvedSetting] = {}
    for name, setting in schema.settings.items():
        sources: list[tuple[str, str, Any]] = []
        if name in cli_values:
            sources.append(("cli", f"command-line option --{name}", cli_values[name]))
        env_name = schema.env_var(name)
        if schema.environ.get(env_name):
            sources.append(("env", f"environment variable {env_name}", schema.environ[env_name]))
        for tier, path, data in files:
            if name in data:
                sources.append((tier, str(path), data[name]))
        valid: list[tuple[str, Any]] = []
        for source, label, raw in sources:
            try:
                valid.append((source, parse_setting_value(setting, raw if setting.normalize is None else setting.normalize(raw))))
            except ValueError as exc:
                warn(f"Invalid value for setting '{name}' from {label}: {_reason(setting, exc)}; using the next source.")
            if valid and setting.type != "dict":
                break
        default = copy.deepcopy(setting.default)
        if setting.type == "dict" and valid:
            merged = default if isinstance(default, dict) else {}
            for _, value in reversed(valid):
                merged.update(value)
            resolved[name] = ResolvedSetting(setting, merged, valid[0][0])
        elif valid:
            resolved[name] = ResolvedSetting(setting, valid[0][1], valid[0][0])
        else:
            resolved[name] = ResolvedSetting(setting, default, "default")
    return resolved


def _load_config_file(path: Path, schema: SettingsSchema, logger: Any, warn: Callable[[str], None]) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        warn(f"Ignoring configuration file {path}: {exc}")
        return None
    if not isinstance(data, dict):
        warn(f"Ignoring configuration file {path}: expected a JSON object.")
        return None
    data = normalize_config_keys(data, style="kebab", source=path, logger=logger)
    for setting in schema.settings.values():
        for alias in setting.aliases:
            if alias in data:
                value = data.pop(alias)
                data.setdefault(setting.name, value)
    unknown = sorted(key for key in data if schema.get(key) is None)
    if unknown:
        logger.debug(f"Ignoring unknown keys in {path}: {', '.join(unknown)}")
    return data


#: Launches an editor command line and returns its exit code.
EditorLauncher = Callable[[list[str]], int]

_CONFIG_ACTIONS = {
    "path": "print the configuration file path",
    "list": "print every setting with its value and source",
    "names": "print every setting name",
    "get": "print one setting's value",
    "set": "validate and write a setting to a file",
    "delete": "remove a setting from a file",
    "edit": "open a configuration file in an editor",
}


def _launch(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def _show(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


def _entry(item: ResolvedSetting) -> dict[str, Any]:
    setting = item.setting
    mask = setting.secret
    return {
        "name": setting.name,
        "value": _SECRET_MASK if mask and item.value is not None else item.value,
        "source": item.source,
        "type": setting.type,
        "default": _SECRET_MASK if mask and setting.default is not None else setting.default,
        "description": setting.description,
        "secret": setting.secret,
    }


def _details(entry: dict[str, Any]) -> list[str]:
    return [f"    type: {entry['type']}", f"    default: {_show(entry['default'])}", f"    description: {entry['description']}"]


def add_config_actions(harness: "ToolHarness", schema: SettingsSchema, *, launcher: Optional[EditorLauncher] = None) -> None:
    """Register the standard ``config`` command group of the Configuration Guidelines on ``harness``.

    Usage: ``tool config [list|names|path|get|set|delete|edit] [name] [value]``; ``list`` is the default. Put options
    after the positional words. ``--config PATH`` replaces file discovery, and ``get --source`` prints the full card,
    unless the harness already has a global option of that name; ``get --verbose`` always prints the card.

    Args:
        harness: The tool harness to extend.
        schema: The tool's declared settings.
        launcher: Runs the editor command of ``config edit``; defaults to :func:`subprocess.run`. Mainly for tests.
    """
    run_editor = launcher or _launch

    def configure_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("subaction", nargs="?", default="list", choices=list(_CONFIG_ACTIONS))
        parser.add_argument("name", nargs="?", help="setting name for get, set, and delete")
        parser.add_argument("value", nargs="?", help="new value for set")
        parser.add_argument("--all", action="store_true", help="path: print the path of every file")
        if not any("--source" in flags for flags, _ in harness._global_args):
            parser.add_argument("--source", action="store_true", help="get: print the full setting card")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--user", action="store_true", help="select the user file")
        group.add_argument("--system", action="store_true", help="select the system file")
        if not any("--config" in flags for flags, _ in harness._global_args):
            parser.add_argument("--config", metavar="PATH", help="use this file instead of discovering the files")
        harness.add_format_option(parser)

    def handler(args: argparse.Namespace, logger: CliLogger) -> int:
        sub, name = args.subaction, args.name
        wants_name = sub in ("get", "set", "delete")
        if (name is not None) != wants_name or (args.value is not None) != (sub == "set"):
            needs = {"get": "a name", "delete": "a name", "set": "a name and a value"}.get(sub, "no arguments")
            logger.error(f"`config {sub}` takes {needs}.")
            return 2
        config_path = Path(args.config) if getattr(args, "config", None) else None
        as_json = args.format == "json"
        setting: Optional[Setting] = None
        if wants_name:
            setting = schema.get(name)
            if setting is None:
                known = ", ".join(schema.settings) or "none"
                logger.error(f"Unknown setting '{name}'. Known settings: {known}.")
                return 2
        if sub == "names":
            entries = [_entry(ResolvedSetting(item, item.default, "default")) for item in schema.settings.values()]
            if as_json:
                logger.emit_json({"names": [{k: e[k] for k in ("name", "type", "default", "description")} for e in entries]})
            else:
                for entry in entries:
                    logger.emit(entry["name"])
                    if args.verbose:
                        for line in _details(entry):
                            logger.emit(line)
            return 0
        if sub == "list" or sub == "get":
            resolved = resolve_settings(schema, config_path=config_path, logger=logger)
            if sub == "list":
                entries = [_entry(item) for item in resolved.values()]
                if as_json:
                    logger.emit_json({"settings": entries})
                    return 0
                for entry in entries:
                    logger.emit(f"{entry['name']} = {_show(entry['value']) or '(unset)'} ({entry['source']})")
                    if args.verbose:
                        for line in _details(entry):
                            logger.emit(line)
                return 0
            entry = _entry(resolved[setting.name])  # type: ignore[union-attr]
            if as_json:
                logger.emit_json(entry)
            elif getattr(args, "source", False) or args.verbose:
                for key in ("name", "value", "source", "type", "default", "description"):
                    logger.emit(f"{key}: {_show(entry[key])}")
            else:
                logger.emit(_show(entry["value"]))
            return 0

        if config_path is not None and (args.user or args.system):
            logger.error("--config cannot be combined with --user or --system.")
            return 2
        tier = "user" if args.user else "system" if args.system else ("project" if "project" in schema.tiers else "user")
        if tier not in schema.tiers and config_path is None:
            logger.error(f"{schema.tool} does not use a {tier} configuration file.")
            return 2
        path = config_path if config_path is not None else schema.path(tier)
        if sub == "path":
            paths = {t: str(schema.path(t)) for t in schema.tiers}
            if config_path is not None:
                paths = {"config": str(config_path)}
            if as_json:
                logger.emit_json(paths if args.all else {"path": str(path)})
            elif args.all:
                for key, value in paths.items():
                    logger.emit(f"{key}: {value}")
            else:
                logger.emit(str(path))
            return 0
        if sub == "edit":
            return _edit(path, schema, run_editor, logger)
        return _change_file(sub, path, setting, args.value, logger)  # type: ignore[arg-type]

    harness.add_action(
        "config",
        "inspect and change configuration settings",
        handler,
        detail="Sub-actions:\n"
        + "\n".join(f"  {key:<8}{text}" for key, text in _CONFIG_ACTIONS.items())
        + "\nWithout a sub-action, `config` runs `config list`. Files: project by default, --user, or --system.",
        usage_suffix="{" + "|".join(_CONFIG_ACTIONS) + "} [name] [value] [options]",
        configure_parser=configure_parser,
    )
    example = f"{harness.name} config get {next(iter(schema.settings), 'name')} --source"
    if example not in harness.examples:
        harness.examples.append(example)


def _read_object(path: Path, logger: CliLogger) -> Optional[dict[str, Any]]:
    """Read a configuration file for rewriting; a missing file is empty, an unreadable one logs an error and gives None."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.error(f"Cannot read {path}: {exc}")
        return None
    if not isinstance(data, dict):
        logger.error(f"Cannot update {path}: expected a JSON object.")
        return None
    return data


def _change_file(sub: str, path: Path, setting: Setting, raw: Optional[str], logger: CliLogger) -> int:
    name = setting.name
    stored: Any = None
    if sub == "set":
        try:
            parsed = parse_setting_value(setting, raw)
        except ValueError as exc:
            logger.error(f"Invalid value for setting '{name}': {_reason(setting, exc)}.")
            return 2
        stored = raw if setting.type == "duration" else parsed
    data = _read_object(path, logger)
    if data is None:
        return 1
    present = [key for key in data if key.replace("_", "-") == name]
    if sub == "delete" and not present:
        logger.info(f"Setting '{name}' is not set in {path}.")
        return 0
    for key in present:
        del data[key]
    if sub == "set":
        data[name] = stored
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")
    logger.info(f"{'Set' if sub == 'set' else 'Deleted'} '{name}' in {path}.")
    return 0


def _edit(path: Path, schema: SettingsSchema, run_editor: EditorLauncher, logger: CliLogger) -> int:
    editor = schema.environ.get("VISUAL") or schema.environ.get("EDITOR")
    if editor:
        windows = schema.platform.startswith("win")
        command = [part.strip('"') for part in shlex.split(editor, posix=not windows)]
    else:
        command = (
            ["notepad"]
            if schema.platform.startswith("win")
            else ["open", "-W", "-t"]
            if schema.platform == "darwin"
            else ["xdg-open"]
        )
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, "{}\n")
    code = run_editor([*command, str(path)])
    if code != 0:
        logger.error(f"Editor {command[0]} exited with code {code}.")
        return 1
    return 0
