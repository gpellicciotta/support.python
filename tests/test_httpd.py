"""Tests for support_python.httpd embedded static HTTP server."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import urllib.request

from support_python.httpd import EmbeddedStaticServer, StaticServerManager


class HttpdServerTests(unittest.TestCase):
    def test_static_server_routes_and_mock_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            webapp_dir = tmp_root / "webapp"
            webapp_dir.mkdir()
            demo_dir = webapp_dir / "demo"
            demo_dir.mkdir()
            (demo_dir / "view.html").write_text("<h1>Demo Page</h1>", encoding="utf-8")
            (webapp_dir / "index.html").write_text("<h1>SPA Home</h1>", encoding="utf-8")

            mount_dir = tmp_root / "custom_mount"
            mount_dir.mkdir()
            (mount_dir / "app.js").write_text("console.log('Mounted JS');", encoding="utf-8")

            changelog = tmp_root / "CHANGELOG.md"
            changelog.write_text("# Changelog v1.0.0", encoding="utf-8")

            def mock_api(path: str, query: str, handler: EmbeddedStaticServer) -> bool:
                if path == "/api/status":
                    handler.send_json_response({"status": "ready"})
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


if __name__ == "__main__":
    unittest.main()
