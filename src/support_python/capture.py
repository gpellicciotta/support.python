"""Unified view capture engine, static server, and visual UI tour runner.

Provides headless Chrome/Chromium automation, embedded static HTTP serving with SPA routing
and mock API dispatching, viewport presets, image SHA-256 integrity validation, and automated
markdown tour report generation.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Sequence

from .cli import APP_AUTHOR, build_action_parser, print_help, print_version
from .httpd import EmbeddedStaticServer, StaticServerManager
from .logging import CliLogger

DEFAULT_DESKTOP_VIEWPORT: str = "1200x900"
"""Standard desktop viewport dimensions (width x height in pixels)."""

DEFAULT_MOBILE_VIEWPORT: str = "390x844"
"""Standard mobile viewport dimensions corresponding to modern smartphone screen sizes."""

DEFAULT_DELAY_SECONDS: float = 0.5
"""Default settle delay in seconds before taking screenshot."""

DEFAULT_TIMEOUT_SECONDS: float = 30.0
"""Default timeout in seconds for headless browser process execution."""

MINIMUM_SCREENSHOT_BYTES: int = 5000
"""Minimum expected byte size for a non-blank screenshot image file."""

STANDARD_CAPTURE_EXIT_CODES: Sequence[tuple[int, str]] = [
    (0, "Success"),
    (1, "Capture failed, integrity error, or invalid argument"),
]
"""Standard process exit code definitions for capture CLI operations."""


def parse_viewport(viewport: str) -> tuple[int, int]:
    """Parse viewport dimensions string into (width, height) integers.

    Supports 'WIDTHxHEIGHT' or 'WIDTH,HEIGHT' formatting (e.g. ``'1200x900'``).

    Args:
        viewport: Viewport string representation.

    Returns:
        Tuple of ``(width, height)`` as positive integers.

    Raises:
        ValueError: If format is invalid or dimensions are not positive integers.
    """
    cleaned = viewport.strip()
    delimiter = "x" if "x" in cleaned.lower() else ("," if "," in cleaned else None)
    if not delimiter:
        raise ValueError(f"Invalid viewport format: '{viewport}'. Expected WIDTHxHEIGHT or WIDTH,HEIGHT.")

    parts = cleaned.lower().split(delimiter, 1) if delimiter == "x" else cleaned.split(delimiter, 1)
    try:
        w = int(parts[0].strip())
        h = int(parts[1].strip())
        if w <= 0 or h <= 0:
            raise ValueError(f"Viewport dimensions must be positive integers: {viewport}")
        return w, h
    except ValueError as exc:
        raise ValueError(f"Invalid viewport format: '{viewport}'. Expected WIDTHxHEIGHT or WIDTH,HEIGHT.") from exc


def resolve_chrome_path(custom_path: Optional[str | Path] = None) -> str:
    """Find a valid Chrome, Chromium, or Edge executable across supported platforms.

    Searches explicit custom paths, environment variables (``CHROME_BIN``,
    ``GOOGLE_CHROME_BIN``, ``PUPPETEER_EXECUTABLE_PATH``), default OS installation
    directories (Windows Program Files, macOS Applications), and system PATH binaries.

    Args:
        custom_path: Optional explicit executable path to validate and resolve.

    Returns:
        Resolved string path to the browser binary executable.

    Raises:
        RuntimeError: If the browser executable is not found on the system.
    """
    if custom_path:
        p = Path(custom_path)
        if p.exists() and p.is_file():
            return str(p.resolve())
        raise RuntimeError(f"Specified Chrome executable not found at: {custom_path}")

    for env_var in ("CHROME_BIN", "GOOGLE_CHROME_BIN", "PUPPETEER_EXECUTABLE_PATH"):
        env_val = os.environ.get(env_var)
        if env_val and Path(env_val).exists() and Path(env_val).is_file():
            return str(Path(env_val).resolve())

    if os.name == "nt":
        prog_files = os.environ.get("ProgramFiles") or r"C:\Program Files"
        prog_files_x86 = os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)"
        local_app_data = os.environ.get("LOCALAPPDATA") or ""

        candidates = [
            Path(prog_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(prog_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
            (Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe") if local_app_data else None,
            Path(prog_files) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(prog_files_x86) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ]
        for c in candidates:
            if c and c.exists() and c.is_file():
                return str(c.resolve())

    elif sys.platform == "darwin":
        mac_candidates = [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ]
        for c in mac_candidates:
            if c.exists() and c.is_file():
                return str(c.resolve())

    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return str(Path(found).resolve())

    raise RuntimeError("Chrome or Chromium executable not found on system. Install Chrome or pass --chrome-path.")


@dataclass
class PresetConfig:
    """Declarative configuration for a view preset.

    Attributes:
        name: Unique preset identifier (e.g. ``"sign-in"``).
        path: Relative URL path within webapp (e.g. ``"/sign-in.html"``).
        default_output: Default filename or destination path for captured screenshot.
        desktop_viewport: Viewport size for desktop captures. Defaults to :data:`DEFAULT_DESKTOP_VIEWPORT`.
        mobile_viewport: Viewport size for mobile captures. Defaults to :data:`DEFAULT_MOBILE_VIEWPORT`.
        viewport: Legacy override viewport string.
        title: Human-readable display title for tour documentation.
        description: Explanatory summary describing the view purpose and UI components.
    """

    name: str
    path: str
    default_output: Optional[str] = None
    desktop_viewport: str = DEFAULT_DESKTOP_VIEWPORT
    mobile_viewport: str = DEFAULT_MOBILE_VIEWPORT
    viewport: Optional[str] = None
    title: Optional[str] = None
    description: str = ""

    @property
    def effective_desktop_viewport(self) -> str:
        """Return effective desktop viewport dimensions string."""
        return self.viewport or self.desktop_viewport or DEFAULT_DESKTOP_VIEWPORT

    @property
    def effective_mobile_viewport(self) -> str:
        """Return effective mobile viewport dimensions string."""
        return self.mobile_viewport or DEFAULT_MOBILE_VIEWPORT

    @property
    def effective_title(self) -> str:
        """Return human-readable display title, falling back to transformed name."""
        if self.title:
            return self.title
        return self.name.replace("-", " ").replace("_", " ").title()


ViewPreset = PresetConfig


@dataclass
class TourStep:
    """Individual item within a visual UI tour.

    Attributes:
        file_prefix: Ordered filename prefix (e.g. ``"01-home-desktop"``).
        preset_key: Corresponding preset key in application presets registry.
        device_mode: Target device category (``"desktop"`` or ``"mobile"``).
        title: Descriptive step heading for report markdown.
        description: Contextual overview of the visual state captured.
    """

    file_prefix: str
    preset_key: str
    device_mode: str
    title: str
    description: str


@dataclass
class CaptureResult:
    """Outcome of a screenshot capture operation.

    Attributes:
        success: True if the screenshot was captured, non-empty, and written to disk.
        path: Path where the screenshot image was saved.
        viewport: Dimensions string used for capture.
        url: URL loaded in the browser.
        size_bytes: Size of captured image in bytes.
        sha256: Hexadecimal SHA-256 integrity checksum of the image.
        error: Error message string if capture failed, or None.
    """

    success: bool
    path: Path
    viewport: str
    url: str
    size_bytes: int = 0
    sha256: str = ""
    error: Optional[str] = None

    def __bool__(self) -> bool:
        """Return True if screenshot capture succeeded."""
        return self.success


@dataclass
class CaptureAppConfig:
    """Application-level capture suite configuration.

    Attributes:
        app_name: User-facing name of the application.
        cli_name: CLI executable script name. Defaults to ``"capture-view"``.
        version: Application semantic version string.
        presets: Mapping of preset keys to :class:`PresetConfig` instances.
        tour_steps: Optional explicit sequence of tour steps.
        webapp_dir: Directory containing frontend web application files.
        repo_root: Root repository path.
        changelog_path: Path to CHANGELOG.md file for embedded docs server.
        clients_js_dir: Path to directory mounted under ``/clients/js/src/``.
        route_mounts: Additional URI path prefixes mapped to filesystem directories.
        mock_api_handler: Optional callback handling mock API requests in embedded server.
        default_img_dir: Destination directory for single-view screenshots.
        tour_dir: Destination directory for tour reports and screenshots.
        target_environment: Description of target environment URL. Defaults to ``"http://127.0.0.1"``.
        author: Copyright author attribution string. Defaults to :data:`APP_AUTHOR`.
        resolve_mode_path: Optional custom hook function resolving mode-specific URLs.
    """

    app_name: str
    cli_name: str = "capture-view"
    version: Optional[str] = None
    presets: dict[str, PresetConfig] = field(default_factory=dict)
    tour_steps: Optional[list[TourStep | tuple]] = None
    webapp_dir: Optional[Path] = None
    repo_root: Optional[Path] = None
    changelog_path: Optional[Path] = None
    clients_js_dir: Optional[Path] = None
    route_mounts: Optional[dict[str, Path]] = None
    mock_api_handler: Optional[Callable[[str, str, EmbeddedStaticServer], Optional[bool]]] = None
    default_img_dir: Optional[Path] = None
    tour_dir: Optional[Path] = None
    target_environment: str = "http://127.0.0.1"
    author: str = APP_AUTHOR
    resolve_mode_path: Optional[Callable[[str, str, str], str]] = None


class ViewCaptureEngine:
    """Automates headless browser capture of web views across configurable viewports.

    Manages browser process execution, temporary user profile lifecycle, virtual time budgets
    for JavaScript hydration and rendering, and image checksum computation.
    """

    def __init__(
        self,
        logger: Optional[CliLogger] = None,
        chrome_path: Optional[str | Path] = None,
    ) -> None:
        """Initialize the view capture engine.

        Args:
            logger: Optional CLI logger instance.
            chrome_path: Optional explicit filesystem path to browser executable.
        """
        self.logger = logger
        self.chrome_path = chrome_path

    def _log_info(self, msg: str) -> None:
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)

    def _log_warn(self, msg: str) -> None:
        if self.logger:
            self.logger.warning(msg)
        else:
            sys.stderr.write(f"WARNING: {msg}\n")

    def _log_error(self, msg: str) -> None:
        if self.logger:
            self.logger.error(msg)
        else:
            sys.stderr.write(f"ERROR: {msg}\n")

    def _log_debug(self, msg: str) -> None:
        if self.logger:
            self.logger.debug(msg)

    def capture_screenshot(
        self,
        url: str,
        output_path: Path | str,
        viewport: str = DEFAULT_DESKTOP_VIEWPORT,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> CaptureResult:
        """Capture a screenshot of a given URL using headless Chrome.

        Launches a headless browser instance with an isolated temporary profile directory,
        waits for the virtual time budget to allow frontend scripts to render, captures the
        viewport to a PNG image file, and computes SHA-256 image checksums.

        Args:
            url: Fully-qualified HTTP(S) or local URL to capture.
            output_path: Destination path for the captured screenshot PNG.
            viewport: Viewport dimension string (e.g. ``"1200x900"``).
            delay_seconds: Settle delay in seconds before triggering screenshot.
            timeout_seconds: Process execution timeout in seconds. Defaults to 30.0.

        Returns:
            CaptureResult containing execution status, file path, size, and SHA-256 checksum.
        """
        target_path = Path(output_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            exe = resolve_chrome_path(self.chrome_path)
        except RuntimeError as exc:
            self._log_error(str(exc))
            return CaptureResult(
                success=False,
                path=target_path,
                viewport=viewport,
                url=url,
                error=str(exc),
            )

        try:
            width, height = parse_viewport(viewport)
        except ValueError as exc:
            self._log_error(str(exc))
            return CaptureResult(
                success=False,
                path=target_path,
                viewport=viewport,
                url=url,
                error=str(exc),
            )

        budget_ms = max(int(delay_seconds * 1000), 3000)

        # Use TemporaryDirectory with ignore_cleanup_errors if supported
        td_kwargs: dict[str, Any] = {"prefix": "chrome-capture-"}
        if sys.version_info >= (3, 10):
            td_kwargs["ignore_cleanup_errors"] = True

        with tempfile.TemporaryDirectory(**td_kwargs) as tmp_dir:
            cmd = [
                exe,
                "--headless=new",
                "--disable-gpu",
                f"--window-size={width},{height}",
                f"--virtual-time-budget={budget_ms}",
                "--run-all-compositor-stages-before-draw",
                f"--user-data-dir={tmp_dir}",
                f"--screenshot={target_path}",
                url,
            ]

            self._log_debug(f"Executing: {' '.join(cmd)}")
            self._log_info(f"Capturing screenshot ({width}x{height}) -> {target_path.name} ...")

            try:
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout_seconds,
                )
                if res.returncode != 0:
                    err = f"Chrome exited with code {res.returncode}: {res.stderr}"
                    self._log_error(err)
                    return CaptureResult(
                        success=False,
                        path=target_path,
                        viewport=viewport,
                        url=url,
                        error=err,
                    )
            except subprocess.TimeoutExpired:
                err = f"Chrome capture timed out after {timeout_seconds} seconds"
                self._log_error(err)
                return CaptureResult(
                    success=False,
                    path=target_path,
                    viewport=viewport,
                    url=url,
                    error=err,
                )
            except Exception as exc:
                err = f"Failed to execute Chrome capture: {exc}"
                self._log_error(err)
                return CaptureResult(
                    success=False,
                    path=target_path,
                    viewport=viewport,
                    url=url,
                    error=err,
                )

        if not target_path.exists() or target_path.stat().st_size == 0:
            err = f"Screenshot file was not created or empty at {target_path}"
            self._log_error(err)
            return CaptureResult(
                success=False,
                path=target_path,
                viewport=viewport,
                url=url,
                error=err,
            )

        file_bytes = target_path.read_bytes()
        file_size = len(file_bytes)
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        self._log_info(f"Screenshot saved successfully: {target_path} ({file_size:,} bytes)")

        return CaptureResult(
            success=True,
            path=target_path,
            viewport=viewport,
            url=url,
            size_bytes=file_size,
            sha256=sha256_hash,
        )


ViewCaptureManager = ViewCaptureEngine


def run_tour(
    config: CaptureAppConfig,
    logger: Optional[CliLogger] = None,
    chrome_path: Optional[str | Path] = None,
    delay: float = 0.6,
    port: int = 0,
) -> bool:
    """Execute a visual UI tour across registered views, validating integrity and writing tour reports.

    Starts an embedded static server if necessary, iterates over registered tour steps across
    desktop and mobile viewports, captures screenshots, validates minimum file size thresholds,
    detects duplicate frames via SHA-256 digests, and generates an updated markdown tour report
    with links to captured assets.

    Args:
        config: Application capture suite configuration.
        logger: Optional CLI logger instance.
        chrome_path: Optional explicit browser executable path.
        delay: Settle delay in seconds before taking each screenshot. Defaults to 0.6.
        port: TCP port for embedded static server (0 for ephemeral port). Defaults to 0.

    Returns:
        True if all tour screenshots were successfully captured and validated, False otherwise.
    """
    repo_root = config.repo_root or Path.cwd()
    tour_dir = config.tour_dir or (repo_root / "docs" / "tour")
    tour_screenshots_dir = tour_dir / "screenshots"
    tour_history_dir = tour_dir / "history"

    version_str = config.version or "0.0.0"
    now_iso = datetime.now().isoformat()
    today_stamp = datetime.now().strftime("%Y-%m-%d")
    archive_dir_name = f"{today_stamp}-v{version_str}"
    archive_dir = tour_history_dir / archive_dir_name
    archive_screenshots_dir = archive_dir / "screenshots"

    tour_screenshots_dir.mkdir(parents=True, exist_ok=True)
    archive_screenshots_dir.mkdir(parents=True, exist_ok=True)

    capture_mgr = ViewCaptureEngine(logger=logger, chrome_path=chrome_path)

    steps: list[TourStep] = []
    if config.tour_steps:
        for item in config.tour_steps:
            if isinstance(item, TourStep):
                steps.append(item)
            elif isinstance(item, (list, tuple)) and len(item) == 5:
                steps.append(TourStep(*item))
    else:
        for idx, (p_name, p_cfg) in enumerate(sorted(config.presets.items()), 1):
            idx_str = f"{idx:02d}"
            steps.append(
                TourStep(
                    file_prefix=f"{idx_str}-{p_name}-desktop",
                    preset_key=p_name,
                    device_mode="desktop",
                    title=f"{p_cfg.effective_title} - Desktop",
                    description=p_cfg.description,
                )
            )
            steps.append(
                TourStep(
                    file_prefix=f"{idx_str}-{p_name}-mobile",
                    preset_key=p_name,
                    device_mode="mobile",
                    title=f"{p_cfg.effective_title} - Mobile",
                    description=p_cfg.description,
                )
            )

    mounts = dict(config.route_mounts or {})
    if config.clients_js_dir:
        mounts["/clients/js/src/"] = config.clients_js_dir

    server_mgr = StaticServerManager(
        webapp_dir=config.webapp_dir,
        route_mounts=mounts,
        changelog_path=config.changelog_path or (repo_root / "CHANGELOG.md"),
        mock_api_handler=config.mock_api_handler,
        port=port,
        logger=logger,
    )

    try:
        server_port = server_mgr.start()
        if logger:
            logger.info(f"Executing Visual UI Tour ({len(steps)} screenshots total)...")

        captured_records: list[dict[str, Any]] = []
        step_hashes: dict[str, str] = {}

        for step in steps:
            p_cfg = config.presets.get(step.preset_key)
            if not p_cfg:
                if logger:
                    logger.error(f"Unknown preset in tour steps: {step.preset_key}")
                return False

            vp = p_cfg.effective_desktop_viewport if step.device_mode == "desktop" else p_cfg.effective_mobile_viewport
            filename = f"{step.file_prefix}.png"
            dest_file = tour_screenshots_dir / filename
            archive_file = archive_screenshots_dir / filename

            full_url = f"http://127.0.0.1:{server_port}{p_cfg.path}"
            result = capture_mgr.capture_screenshot(
                url=full_url,
                output_path=dest_file,
                viewport=vp,
                delay_seconds=delay,
            )
            if not result:
                if logger:
                    logger.error(f"Tour capture failed on {step.file_prefix}: {result.error}")
                return False

            shutil.copy2(dest_file, archive_file)

            file_bytes = dest_file.read_bytes()
            if len(file_bytes) < MINIMUM_SCREENSHOT_BYTES:
                if logger:
                    logger.error(f"Screenshot {filename} is suspiciously small ({len(file_bytes)} bytes)!")
                return False

            sha256_hash = hashlib.sha256(file_bytes).hexdigest()
            if sha256_hash in step_hashes:
                prev_name = step_hashes[sha256_hash]
                if logger:
                    logger.warning(f"Duplicate frame detected: {filename} identical to {prev_name} ({sha256_hash[:12]}...)")
            step_hashes[sha256_hash] = filename

            captured_records.append(
                {
                    "prefix": step.file_prefix,
                    "filename": filename,
                    "preset": step.preset_key,
                    "device": step.device_mode,
                    "viewport": vp,
                    "title": step.title,
                    "description": step.description,
                    "size_kb": len(file_bytes) / 1024.0,
                    "sha256": sha256_hash,
                }
            )

        if logger:
            logger.info(f"Generating Visual UI Tour Report ({tour_dir / 'ui-tour-report.md'})...")

        report_lines = [
            f"# {config.app_name} - Visual Tour & UI Inspection Report",
            "",
            f"**Target Environment**: `{config.target_environment}`",
            f"**Version**: `v{version_str}`",
            f"**Date**: `{now_iso}`",
            "",
            f"This document provides a visual walkthrough of the **{config.app_name}** application.",
            "It showcases all registered views across both **Desktop** and **Mobile** viewports.",
            "",
            "## Verification & Integrity Summary",
            "",
            "| # | View | Mode | Viewport | File | Size | SHA-256 Checksum |",
            "|---|------|------|----------|------|------|------------------|",
        ]

        for idx, rec in enumerate(captured_records, 1):
            mode_badge = "Desktop" if rec["device"] == "desktop" else "Mobile"
            report_lines.append(
                f"| {idx} | {rec['title']} | {mode_badge} | `{rec['viewport']}` | `{rec['filename']}` | {rec['size_kb']:.1f} KB | `{rec['sha256'][:16]}...` |"
            )

        report_lines.extend(
            [
                "",
                "## Visual UI Tour Walkthrough",
                "",
            ]
        )

        preset_groups: dict[str, list[dict[str, Any]]] = {}
        for rec in captured_records:
            preset_groups.setdefault(rec["preset"], []).append(rec)

        for preset_key, records in preset_groups.items():
            cfg = config.presets[preset_key]
            report_lines.append(f"### {cfg.effective_title}")
            report_lines.append("")
            if cfg.description:
                report_lines.append(f"- **Description**: {cfg.description}")
            report_lines.append(f"- **Harness Path**: `{cfg.path}`")
            report_lines.append("")

            for r in records:
                mode_label = "Desktop View" if r["device"] == "desktop" else "Mobile View"
                report_lines.append(f"#### {mode_label} (`{r['viewport']}`)")
                report_lines.append("")
                report_lines.append(f"![{r['title']}](screenshots/{r['filename']})")
                report_lines.append("")

            report_lines.append("---")
            report_lines.append("")

        report_path = tour_dir / "ui-tour-report.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")
        shutil.copy2(report_path, archive_dir / "ui-tour-report.md")

        if logger:
            logger.info(f"Visual UI Tour successfully generated: {report_path}")
        return True

    finally:
        server_mgr.shutdown()


def run_capture(
    config: CaptureAppConfig,
    target: Optional[str] = None,
    url: Optional[str] = None,
    output: Optional[str] = None,
    viewport: Optional[str] = None,
    mobile: bool = False,
    desktop: bool = False,
    mode: Optional[str] = None,
    delay: float = DEFAULT_DELAY_SECONDS,
    all_presets: bool = False,
    port: int = 0,
    no_server: bool = False,
    chrome_path: Optional[str | Path] = None,
    logger: Optional[CliLogger] = None,
) -> bool:
    """Orchestrate server startup and capture one or all requested views.

    Resolves target presets or explicit URLs, starts an embedded static HTTP server when
    capturing local webapp assets, runs headless Chrome captures, and saves PNG screenshots.

    Args:
        config: Application capture suite configuration.
        target: Optional preset identifier or relative web path.
        url: Optional explicit URL or path override.
        output: Optional destination file path for the screenshot PNG.
        viewport: Viewport dimension string (e.g. ``"1200x900"``).
        mobile: If True, forces mobile viewport (:data:`DEFAULT_MOBILE_VIEWPORT`).
        desktop: If True, forces desktop viewport (:data:`DEFAULT_DESKTOP_VIEWPORT`).
        mode: Preset variant mode (e.g. ``"error"``, ``"empty"``).
        delay: Settle delay in seconds before screenshot capture. Defaults to :data:`DEFAULT_DELAY_SECONDS`.
        all_presets: If True, captures all registered presets sequentially.
        port: TCP port for embedded server. Defaults to 0 (ephemeral).
        no_server: If True, disables starting the embedded HTTP server.
        chrome_path: Optional explicit browser executable path.
        logger: Optional CLI logger instance.

    Returns:
        True if all requested view captures succeeded, False otherwise.
    """
    capture_mgr = ViewCaptureEngine(logger=logger, chrome_path=chrome_path)
    default_img_dir = config.default_img_dir or ((config.repo_root or Path.cwd()) / "docs" / "img")

    selected_viewport = viewport
    if mobile:
        selected_viewport = DEFAULT_MOBILE_VIEWPORT
    elif desktop:
        selected_viewport = DEFAULT_DESKTOP_VIEWPORT

    items_to_capture: list[tuple[str, Path, str, float]] = []

    def _apply_mode(base_path: str, p_key: Optional[str], mode_val: Optional[str]) -> str:
        if not mode_val:
            return base_path
        if config.resolve_mode_path and p_key:
            return config.resolve_mode_path(p_key, base_path, mode_val)
        sep = "&" if "?" in base_path else "?"
        return f"{base_path}{sep}mode={mode_val}"

    if all_presets:
        for p_name, p_cfg in config.presets.items():
            vp = selected_viewport or p_cfg.effective_desktop_viewport
            out_name = Path(p_cfg.default_output).name if p_cfg.default_output else f"{p_name}.png"
            out = default_img_dir / out_name
            items_to_capture.append((p_cfg.path, out, vp, delay))
    else:
        preset_key = target.lower() if target and target.lower() in config.presets else None
        if preset_key:
            cfg = config.presets[preset_key]
            rel_path = _apply_mode(cfg.path, preset_key, mode)
            out_name = Path(cfg.default_output).name if cfg.default_output else f"{preset_key}.png"
            out_path = Path(output) if output else default_img_dir / out_name
            vp = selected_viewport or cfg.effective_desktop_viewport
            items_to_capture.append((rel_path, out_path, vp, delay))
        else:
            raw_path = url or target or "/index.html"
            stem = Path(raw_path.split("?")[0]).stem or "view-capture"
            out_path = Path(output) if output else default_img_dir / f"{stem}.png"
            vp = selected_viewport or DEFAULT_DESKTOP_VIEWPORT
            items_to_capture.append((raw_path, out_path, vp, delay))

    server_mgr: Optional[StaticServerManager] = None
    server_port = port

    try:
        if not no_server:
            needs_server = any(not (item[0].startswith("http://") or item[0].startswith("https://")) for item in items_to_capture)
            if needs_server:
                repo_root = config.repo_root or Path.cwd()
                mounts = dict(config.route_mounts or {})
                if config.clients_js_dir:
                    mounts["/clients/js/src/"] = config.clients_js_dir

                server_mgr = StaticServerManager(
                    webapp_dir=config.webapp_dir,
                    route_mounts=mounts,
                    changelog_path=config.changelog_path or (repo_root / "CHANGELOG.md"),
                    mock_api_handler=config.mock_api_handler,
                    port=port,
                    logger=logger,
                )
                server_port = server_mgr.start()

        results: list[bool] = []
        for path_or_url, out_file, vp, d in items_to_capture:
            if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
                full_url = path_or_url
            else:
                formatted_path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
                full_url = f"http://127.0.0.1:{server_port}{formatted_path}"

            res = capture_mgr.capture_screenshot(
                url=full_url,
                output_path=out_file,
                viewport=vp,
                delay_seconds=d,
            )
            results.append(res.success)

        return all(results) and len(results) > 0

    finally:
        if server_mgr:
            server_mgr.shutdown()


def print_presets_list(config: CaptureAppConfig) -> None:
    """Print a formatted table of registered view presets to stdout.

    Args:
        config: Application capture suite configuration containing presets.
    """
    print(f"\nRegistered View Presets ({len(config.presets)} total):\n")
    print(f"  {'Preset':<24} {'Desktop':<12} {'Mobile':<12} {'Default Path':<45}")
    print(f"  {'-' * 22:<24} {'-' * 10:<12} {'-' * 10:<12} {'-' * 43:<45}")
    for name, cfg in sorted(config.presets.items()):
        print(f"  {name:<24} {cfg.effective_desktop_viewport:<12} {cfg.effective_mobile_viewport:<12} {cfg.path:<45}")
        print(f"    Title:       {cfg.effective_title}")
        if cfg.description:
            print(f"    Description: {cfg.description}")
        if cfg.default_output:
            print(f"    Output:      {cfg.default_output}")
        print()


def build_capture_parser(config: CaptureAppConfig) -> argparse.ArgumentParser:
    """Build the standard CLI argument parser for view capture applications.

    Args:
        config: Application capture suite configuration.

    Returns:
        Configured ArgumentParser with capture, tour, and list actions and options.
    """
    actions = ["capture", "tour", "list", "version", "help"]
    description = (
        f"{config.app_name}\n"
        "============================================================\n"
        "Unified visual view capture and UI screenshot automation CLI.\n\n"
        "Actions:\n"
        "  capture [TARGET]       Capture a screenshot for a view preset or path (default)\n"
        "  tour                   Run full desktop and mobile visual tour and generate report\n"
        "  list                   List all registered view presets and their viewports\n"
        "  version                Show project version and exit\n"
        "  help                   Show this help message and exit"
    )

    parser = build_action_parser(
        prog=config.cli_name,
        description=description,
        actions=actions,
        default_action="capture",
    )

    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Preset name (e.g. sign-in, account) or relative URL path",
    )
    parser.add_argument("--url", "--path", "-p", dest="url", help="URL or webapp relative path to capture")
    parser.add_argument("--output", "-o", help="Destination file path for the captured screenshot PNG")
    parser.add_argument("--viewport", "--size", help="Viewport size formatted as WIDTHxHEIGHT (e.g. 1200x900)")
    parser.add_argument("--mobile", action="store_true", help="Capture with standard mobile viewport (390x844)")
    parser.add_argument("--desktop", action="store_true", help="Capture with standard desktop viewport (1200x900)")
    parser.add_argument("--mode", help="Preset variant mode (e.g. error, before, after, empty)")
    parser.add_argument("--all", action="store_true", help="Capture all registered presets sequentially")
    parser.add_argument("--tour", action="store_true", help="Run full visual UI tour and generate docs/tour/ui-tour-report.md")
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"Delay in seconds before taking screenshot (default: {DEFAULT_DELAY_SECONDS})",
    )
    parser.add_argument("--chrome-path", help="Explicit path to Chrome executable")
    parser.add_argument("--port", type=int, default=0, help="Port for embedded static server (default: 0)")
    parser.add_argument("--no-server", action="store_true", help="Do not start embedded server")
    parser.add_argument("--log-file", help="Path to operational log file")

    return parser


def run_capture_cli(
    config: CaptureAppConfig,
    argv: Optional[Sequence[str]] = None,
) -> int:
    """Entry point for executing the view capture CLI with a given configuration.

    Parses command-line arguments, configures logging, routes subcommands (capture, tour,
    list, version, help), and exits with standard exit codes.

    Args:
        config: Application capture suite configuration.
        argv: Command-line arguments sequence. Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code (0 on success, 1 on failure).
    """
    version = config.version or "0.0.0"
    actions = ["capture", "tour", "list", "version", "help"]

    parser = build_capture_parser(config)
    args = parser.parse_args(argv)

    if args.version or args.action == "version":
        print_version(config.cli_name, version, author=config.author)
        return 0

    if args.help or args.action == "help":
        print_help(
            prog=config.cli_name,
            version=version,
            description=f"{config.app_name}\nUnified visual view capture and UI screenshot automation CLI.",
            parser=parser,
            exit_codes=STANDARD_CAPTURE_EXIT_CODES,
            author=config.author,
        )
        return 0

    if args.action == "list":
        print_version(config.cli_name, version, author=config.author)
        print_presets_list(config)
        return 0

    logger = CliLogger(
        log_path=args.log_file,
        verbose=args.verbose,
        debug=args.debug,
        origin=config.cli_name,
    )

    if args.action == "tour" or args.tour:
        ok = run_tour(
            config=config,
            logger=logger,
            chrome_path=args.chrome_path,
            delay=args.delay,
            port=args.port,
        )
        return 0 if ok else 1

    effective_target = args.target
    if args.action not in actions and effective_target is None:
        effective_target = args.action

    ok = run_capture(
        config=config,
        target=effective_target,
        url=args.url,
        output=args.output,
        viewport=args.viewport,
        mobile=args.mobile,
        desktop=args.desktop,
        mode=args.mode,
        delay=args.delay,
        all_presets=args.all,
        port=args.port,
        no_server=args.no_server,
        chrome_path=args.chrome_path,
        logger=logger,
    )

    return 0 if ok else 1


__all__ = [
    "DEFAULT_DELAY_SECONDS",
    "DEFAULT_DESKTOP_VIEWPORT",
    "DEFAULT_MOBILE_VIEWPORT",
    "DEFAULT_TIMEOUT_SECONDS",
    "MINIMUM_SCREENSHOT_BYTES",
    "STANDARD_CAPTURE_EXIT_CODES",
    "CaptureAppConfig",
    "CaptureResult",
    "EmbeddedStaticServer",
    "PresetConfig",
    "StaticServerManager",
    "TourStep",
    "ViewCaptureEngine",
    "ViewCaptureManager",
    "ViewPreset",
    "parse_viewport",
    "resolve_chrome_path",
    "run_capture",
    "run_capture_cli",
    "run_tour",
]
