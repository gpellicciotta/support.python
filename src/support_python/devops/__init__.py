"""DevOps and local developer environment orchestration utilities.

Provides subprocess step runners and streaming helpers in :mod:`support_python.devops.steps`
and reusable managers for Docker, MySQL, Cloud SQL proxy, Java application server processes,
email template testing, and endpoint verification in :mod:`support_python.devops.services`,
plus version-file, CHANGELOG.md, release-notes, and GitHub-origin helpers, the typed
:func:`confirm_typed` prompt, and the dry-runnable :class:`ReleasePipeline` in
:mod:`support_python.devops.release`. :class:`Project`, :class:`PythonProject`,
:class:`GradleProject`, and :class:`NodeProject` in :mod:`support_python.devops.projects` adapt a
repository's build, and :class:`DevopsCli` in :mod:`support_python.devops.cli` exposes them as the
standard ``devops`` actions. :class:`DeployStep`, :class:`DeployContext`, and :class:`DeployPipeline` in
:mod:`support_python.devops.deploy` back its optional ``deploy`` action, and :class:`ServiceActions` in
:mod:`support_python.devops.service_actions` backs its opt-in ``docker``, ``db``, ``server``, ``mail``, and
``client`` action groups.
"""

from __future__ import annotations

from .cli import DevopsCli
from .deploy import DeployContext, DeployPipeline, DeployStep
from .projects import GradleProject, NodeProject, Project, PythonProject
from .release import (
    VERSION_FILES,
    ReleasePipeline,
    VersionFile,
    capture_command,
    changelog_top_version,
    confirm_typed,
    extract_release_notes,
    find_version_file,
    freeze_changelog,
    next_dev_version,
    open_dev_changelog,
    parse_github_repo,
    read_version,
    release_version,
    write_version,
)
from .service_actions import ServiceActions
from .services import (
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMailManager,
    LocalMySqlManager,
    LocalServerManager,
    LocalVerifier,
    resolve_cloud_sql_proxy_bin,
)
from .steps import (
    EXIT_COMMAND_NOT_FOUND,
    resolve_executable,
    run_step,
    run_step_command,
    stream_subprocess,
)

__all__ = [
    "EXIT_COMMAND_NOT_FOUND",
    "resolve_executable",
    "stream_subprocess",
    "run_step_command",
    "run_step",
    "resolve_cloud_sql_proxy_bin",
    "CloudSqlProxyManager",
    "LocalDockerManager",
    "LocalMySqlManager",
    "LocalServerManager",
    "LocalMailManager",
    "LocalVerifier",
    "VersionFile",
    "VERSION_FILES",
    "find_version_file",
    "read_version",
    "write_version",
    "release_version",
    "next_dev_version",
    "changelog_top_version",
    "extract_release_notes",
    "freeze_changelog",
    "open_dev_changelog",
    "parse_github_repo",
    "confirm_typed",
    "capture_command",
    "ReleasePipeline",
    "Project",
    "PythonProject",
    "GradleProject",
    "NodeProject",
    "DevopsCli",
    "DeployStep",
    "DeployContext",
    "DeployPipeline",
    "ServiceActions",
]
