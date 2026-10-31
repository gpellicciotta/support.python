from __future__ import annotations

import hashlib
import io
import subprocess
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

from support_python import (
    CaptureAppConfig,
    CaptureResult,
    EmbeddedStaticServer,
    PresetConfig,
    StaticServerManager,
    TourStep,
    ViewCaptureEngine,
    ViewCaptureManager,
    ViewPreset,
    parse_viewport,
    resolve_chrome_path,
    run_capture,
    run_capture_cli,
    run_tour,
)
from support_python.capture import MINIMUM_SCREENSHOT_BYTES, build_capture_parser


class ViewportTests(unittest.TestCase):
    def test_parse_viewport_valid_formats(self) -> None:
        self.assertEqual(parse_viewport("1200x900"), (1200, 900))
        self.assertEqual(parse_viewport("390,844"), (390, 844))
        self.assertEqual(parse_viewport("  1024X768  "), (1024, 768))

    def test_parse_viewport_invalid_formats(self) -> None:
        for invalid in ["abc", "100", "100x", "x100", "-100x200", "0x500", "100x0"]:
            with self.assertRaises(ValueError):
                parse_viewport(invalid)


class PresetConfigTests(unittest.TestCase):
    def test_tour_step_dataclass(self) -> None:
        step = TourStep("01-sign-in", "sign-in", "desktop", "Sign In - Desktop", "Sign in view")
        self.assertEqual(step.file_prefix, "01-sign-in")
        self.assertEqual(step.preset_key, "sign-in")
        self.assertEqual(step.device_mode, "desktop")
        self.assertEqual(step.title, "Sign In - Desktop")
        self.assertEqual(step.description, "Sign in view")

    def test_preset_defaults_and_properties(self) -> None:
        preset = PresetConfig(
            name="sign-in",
            path="/demo/sign-in.html",
            default_output="docs/img/sign-in.png",
        )
        self.assertEqual(preset.effective_desktop_viewport, "1200x900")
        self.assertEqual(preset.effective_mobile_viewport, "390x844")
        self.assertEqual(preset.effective_title, "Sign In")

    def test_preset_single_viewport_override(self) -> None:
        preset = PresetConfig(
            name="admin",
            path="/demo/admin.html",
            viewport="1000x950",
            title="Custom Admin Title",
            description="Admin description",
        )
        self.assertEqual(preset.effective_desktop_viewport, "1000x950")
        self.assertEqual(preset.effective_mobile_viewport, "390x844")
        self.assertEqual(preset.effective_title, "Custom Admin Title")
        self.assertIs(ViewPreset, PresetConfig)


class ChromeDiscoveryTests(unittest.TestCase):
    def test_custom_path_existing(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f_path = Path(f.name)
        try:
            resolved = resolve_chrome_path(f_path)
            self.assertEqual(resolved, str(f_path.resolve()))
        finally:
            f_path.unlink(missing_ok=True)

    def test_custom_path_missing_raises(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            resolve_chrome_path("non-existent-chrome-path-xyz")
        self.assertIn("not found", str(ctx.exception))

    @patch.dict(
        "os.environ",
        {
            "CHROME_BIN": "",
            "GOOGLE_CHROME_BIN": "",
            "PUPPETEER_EXECUTABLE_PATH": "",
            "ProgramFiles": r"C:\EmptyPathTest",
            "ProgramFiles(x86)": r"C:\EmptyPathTest",
            "LOCALAPPDATA": r"C:\EmptyPathTest",
        },
    )
    @patch("shutil.which", return_value=r"C:\bin\google-chrome.exe")
    def test_shutil_which_discovery(self, mock_which: MagicMock) -> None:
        resolved = resolve_chrome_path()
        self.assertEqual(resolved, str(Path(r"C:\bin\google-chrome.exe").resolve()))

    @patch.dict(
        "os.environ",
        {
            "CHROME_BIN": "",
            "GOOGLE_CHROME_BIN": "",
            "PUPPETEER_EXECUTABLE_PATH": "",
            "ProgramFiles": r"C:\EmptyPathTest",
            "ProgramFiles(x86)": r"C:\EmptyPathTest",
            "LOCALAPPDATA": r"C:\EmptyPathTest",
        },
    )
    @patch("shutil.which", return_value=None)
    def test_chrome_not_found_raises(self, mock_which: MagicMock) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            resolve_chrome_path()
        self.assertIn("Chrome or Chromium executable not found", str(ctx.exception))


class ViewCaptureEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ViewCaptureEngine()

    def test_capture_result_bool_evaluation(self) -> None:
        res_ok = CaptureResult(success=True, path=Path("ok.png"), viewport="1200x900", url="http://test")
        res_err = CaptureResult(success=False, path=Path("err.png"), viewport="1200x900", url="http://test", error="fail")
        self.assertTrue(res_ok)
        self.assertFalse(res_err)
        self.assertIs(ViewCaptureManager, ViewCaptureEngine)

    def test_invalid_viewport_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "out.png"
            res = self.engine.capture_screenshot("http://example.test", out, viewport="invalid")
            self.assertFalse(res)
            self.assertIn("Invalid viewport format", res.error or "")

    @patch("support_python.capture.resolve_chrome_path", return_value="/mock/chrome")
    @patch("subprocess.run")
    def test_successful_capture_creates_result_with_sha256(self, mock_run: MagicMock, mock_resolve: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "shot.png"

            def fake_chrome(cmd: list[str], **kwargs: object) -> MagicMock:
                out.write_bytes(b"dummy screenshot content bytes 123456789")
                return MagicMock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = fake_chrome

            res = self.engine.capture_screenshot("http://example.test", out, viewport="1000x800", delay_seconds=1.0)
            self.assertTrue(res)
            self.assertEqual(res.path, out.resolve())
            self.assertEqual(res.viewport, "1000x800")
            self.assertEqual(res.size_bytes, len(b"dummy screenshot content bytes 123456789"))
            self.assertEqual(res.sha256, hashlib.sha256(b"dummy screenshot content bytes 123456789").hexdigest())

            cmd = mock_run.call_args[0][0]
            self.assertIn("--headless=new", cmd)
            self.assertIn("--disable-gpu", cmd)
            self.assertIn("--window-size=1000,800", cmd)
            self.assertIn(f"--screenshot={out.resolve()}", cmd)

    @patch("support_python.capture.resolve_chrome_path", return_value="/mock/chrome")
    @patch("subprocess.run")
    def test_subprocess_timeout_returns_failure(self, mock_run: MagicMock, mock_resolve: MagicMock) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["chrome"], timeout=30)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "shot.png"
            res = self.engine.capture_screenshot("http://example.test", out)
            self.assertFalse(res)
            self.assertIn("timed out", res.error or "")

    @patch("support_python.capture.resolve_chrome_path", return_value="/mock/chrome")
    @patch("subprocess.run")
    def test_subprocess_nonzero_exit_returns_failure(self, mock_run: MagicMock, mock_resolve: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="Fatal Chrome GPU Error")
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "shot.png"
            res = self.engine.capture_screenshot("http://example.test", out)
            self.assertFalse(res)
            self.assertIn("Fatal Chrome GPU Error", res.error or "")


class StaticServerTests(unittest.TestCase):
    def test_embedded_server_serves_static_spa_and_mounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_webapp, tempfile.TemporaryDirectory() as tmp_mount:
            webapp_dir = Path(tmp_webapp)
            mount_dir = Path(tmp_mount)

            index_html = webapp_dir / "index.html"
            index_html.write_text("<!DOCTYPE html><html><body>SPA Home</body></html>", encoding="utf-8")

            demo_file = webapp_dir / "demo" / "view.html"
            demo_file.parent.mkdir(parents=True, exist_ok=True)
            demo_file.write_text("<html><body>Demo Page</body></html>", encoding="utf-8")

            mounted_js = mount_dir / "app.js"
            mounted_js.write_text("console.log('Mounted JS');", encoding="utf-8")

            changelog = webapp_dir / "CHANGELOG.md"
            changelog.write_text("# Changelog v1.0.0", encoding="utf-8")

            def mock_api(path: str, query: str, handler: EmbeddedStaticServer) -> bool:
                if path == "/api/status":
                    handler.send_json_response({"status": "ready", "count": 42})
                    return True
                return False

            server_mgr = StaticServerManager(
                webapp_dir=webapp_dir,
                route_mounts={"/clients/js/src/": mount_dir},
                changelog_path=changelog,
                mock_api_handler=mock_api,
                port=0,
            )

            with server_mgr:
                port = server_mgr.port
                self.assertGreater(port, 0)
                base = f"http://127.0.0.1:{port}"

                # 1. Direct file
                with urllib.request.urlopen(f"{base}/demo/view.html") as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn(b"Demo Page", resp.read())

                # 2. SPA fallback
                with urllib.request.urlopen(f"{base}/applications/my-app") as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn(b"SPA Home", resp.read())

                # 3. Mounted route
                with urllib.request.urlopen(f"{base}/clients/js/src/app.js") as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn(b"Mounted JS", resp.read())

                # 4. CHANGELOG.md
                with urllib.request.urlopen(f"{base}/CHANGELOG.md") as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn(b"# Changelog v1.0.0", resp.read())

                # 5. Mock API
                with urllib.request.urlopen(f"{base}/api/status") as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(resp.headers.get("Content-Type"), "application/json; charset=utf-8")
                    self.assertIn(b'"status": "ready"', resp.read())

                # 6. OPTIONS CORS
                req = urllib.request.Request(f"{base}/api/status", method="OPTIONS")
                with urllib.request.urlopen(req) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")


class VisualTourTests(unittest.TestCase):
    @patch.object(ViewCaptureEngine, "capture_screenshot")
    def test_run_tour_generates_report_and_archives(self, mock_capture: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmp_root:
            repo_root = Path(tmp_root)
            webapp_dir = repo_root / "webapp"
            webapp_dir.mkdir(parents=True, exist_ok=True)
            (webapp_dir / "index.html").write_text("<html></html>", encoding="utf-8")

            tour_dir = repo_root / "docs" / "tour"

            presets = {
                "sign-in": PresetConfig(
                    name="sign-in",
                    path="/demo/sign-in.html",
                    title="Sign In View",
                    description="Authentication landing view",
                ),
            }

            def fake_capture(url: str, output_path: Path | str, **kwargs: object) -> CaptureResult:
                out = Path(output_path)
                # Ensure bytes exceed MINIMUM_SCREENSHOT_BYTES so integrity check passes
                out.write_bytes(b"A" * (MINIMUM_SCREENSHOT_BYTES + 100))
                return CaptureResult(success=True, path=out, viewport="1200x900", url=url)

            mock_capture.side_effect = fake_capture

            config = CaptureAppConfig(
                app_name="Test App Capture",
                version="1.2.3",
                presets=presets,
                repo_root=repo_root,
                webapp_dir=webapp_dir,
                tour_dir=tour_dir,
            )

            ok = run_tour(config)
            self.assertTrue(ok)

            report_file = tour_dir / "ui-tour-report.md"
            self.assertTrue(report_file.exists())
            report_text = report_file.read_text(encoding="utf-8")
            self.assertIn("Test App Capture - Visual Tour & UI Inspection Report", report_text)
            self.assertIn("Sign In View", report_text)
            self.assertIn("Authentication landing view", report_text)
            self.assertIn("Desktop View", report_text)
            self.assertIn("Mobile View", report_text)

            screenshots_dir = tour_dir / "screenshots"
            self.assertTrue((screenshots_dir / "01-sign-in-desktop.png").exists())
            self.assertTrue((screenshots_dir / "01-sign-in-mobile.png").exists())

            history_dir = tour_dir / "history"
            archives = list(history_dir.glob("*-v1.2.3"))
            self.assertEqual(len(archives), 1)
            self.assertTrue((archives[0] / "ui-tour-report.md").exists())
            self.assertTrue((archives[0] / "screenshots" / "01-sign-in-desktop.png").exists())

    @patch.object(ViewCaptureEngine, "capture_screenshot")
    def test_run_tour_fails_on_suspiciously_small_screenshot(self, mock_capture: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmp_root:
            repo_root = Path(tmp_root)
            presets = {"test": PresetConfig(name="test", path="/test.html")}

            def fake_small_capture(url: str, output_path: Path | str, **kwargs: object) -> CaptureResult:
                out = Path(output_path)
                out.write_bytes(b"small")
                return CaptureResult(success=True, path=out, viewport="1200x900", url=url)

            mock_capture.side_effect = fake_small_capture

            config = CaptureAppConfig(
                app_name="Test Small",
                presets=presets,
                repo_root=repo_root,
            )

            ok = run_tour(config)
            self.assertFalse(ok)


class CaptureCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.presets = {
            "account": PresetConfig(
                name="account",
                path="/demo/account.html",
                default_output="docs/img/account.png",
                viewport="1000x950",
                description="User account management harness",
            ),
        }
        self.config = CaptureAppConfig(
            app_name="Test CLI App",
            cli_name="test-capture",
            version="2.0.0",
            presets=self.presets,
        )

    def test_parser_generation(self) -> None:
        parser = build_capture_parser(self.config)
        self.assertEqual(parser.prog, "test-capture")

    def test_cli_version_action(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = run_capture_cli(self.config, ["version"])
        self.assertEqual(code, 0)
        self.assertIn("test-capture v2.0.0", stdout.getvalue())

    def test_cli_help_action(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = run_capture_cli(self.config, ["help"])
        self.assertEqual(code, 0)
        self.assertIn("test-capture v2.0.0", stdout.getvalue())
        self.assertIn("Unified visual view capture", stdout.getvalue())

    def test_cli_list_action(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = run_capture_cli(self.config, ["list"])
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("account", output)
        self.assertIn("User account management harness", output)

    @patch("support_python.capture.run_capture", return_value=True)
    def test_cli_capture_action_dispatch(self, mock_run_capture: MagicMock) -> None:
        code = run_capture_cli(self.config, ["capture", "account", "--mobile", "--no-server"])
        self.assertEqual(code, 0)
        mock_run_capture.assert_called_once()
        kwargs = mock_run_capture.call_args.kwargs
        self.assertEqual(kwargs["target"], "account")
        self.assertTrue(kwargs["mobile"])
        self.assertTrue(kwargs["no_server"])

    @patch("support_python.capture.run_tour", return_value=True)
    def test_cli_tour_action_dispatch(self, mock_run_tour: MagicMock) -> None:
        code = run_capture_cli(self.config, ["tour"])
        self.assertEqual(code, 0)
        mock_run_tour.assert_called_once()


class RunCaptureOrchestrationTests(unittest.TestCase):
    @patch.object(ViewCaptureEngine, "capture_screenshot")
    def test_run_capture_all_presets(self, mock_capture: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmp_root:
            repo_root = Path(tmp_root)
            presets = {
                "view-a": PresetConfig(name="view-a", path="http://example.test/a"),
                "view-b": PresetConfig(name="view-b", path="http://example.test/b"),
            }
            config = CaptureAppConfig(
                app_name="Test Capture",
                presets=presets,
                repo_root=repo_root,
                default_img_dir=repo_root / "img",
            )
            mock_capture.return_value = CaptureResult(success=True, path=Path("out.png"), viewport="1200x900", url="url")

            ok = run_capture(config, all_presets=True, no_server=True)
            self.assertTrue(ok)
            self.assertEqual(mock_capture.call_count, 2)

    @patch.object(ViewCaptureEngine, "capture_screenshot")
    def test_run_capture_mode_resolution(self, mock_capture: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmp_root:
            repo_root = Path(tmp_root)
            presets = {
                "sign-in": PresetConfig(name="sign-in", path="http://example.test/sign-in"),
            }

            def custom_mode(preset_key: str, path: str, mode: str) -> str:
                return f"{path}?custom_mode={mode}"

            config = CaptureAppConfig(
                app_name="Test Mode",
                presets=presets,
                repo_root=repo_root,
                resolve_mode_path=custom_mode,
            )
            mock_capture.return_value = CaptureResult(success=True, path=Path("out.png"), viewport="1200x900", url="url")

            ok = run_capture(config, target="sign-in", mode="error", no_server=True)
            self.assertTrue(ok)
            called_url = mock_capture.call_args.kwargs["url"]
            self.assertEqual(called_url, "http://example.test/sign-in?custom_mode=error")
