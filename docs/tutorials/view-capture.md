# View Capture

These modules capture web application views as screenshots and serve static files while doing so:
- [capture.py](../../src/support_python/capture.py): browser screenshot automation (`ViewCaptureEngine`) and visual UI tour orchestration (`run_tour`, `run_capture_cli`).
- [httpd.py](../../src/support_python/httpd.py): embedded static web serving (`EmbeddedStaticServer`, `StaticServerManager`).

## Capture CLI
`run_capture_cli` runs a `ToolHarness` CLI, built by `support_python.capture.build_capture_harness`.
Its actions are `capture` (the default action), `tour`, `list`, `version`, and `help`.
Webapps declare their view presets, then drive screenshot capture and Markdown tour reports (`ui-tour-report.md`) with minimal boilerplate:

```python
from pathlib import Path
import sys
from support_python import CaptureAppConfig, PresetConfig, run_capture_cli

config = CaptureAppConfig(
    app_name="Example Auth",
    cli_name="capture-view",
    version="1.0.0",
    presets={
        "sign-in": PresetConfig(
            name="sign-in",
            path="/demo/sign-in-view-harness.html",
            default_output="docs/img/sign-in-view.png",
            desktop_viewport="1000x700",
            mobile_viewport="390x844",
            title="Sign In View",
            description="Centralized sign-in card supporting credentials and social logins.",
        ),
    },
    webapp_dir=Path(__file__).resolve().parent.parent / "webapp",
)

if __name__ == "__main__":
    sys.exit(run_capture_cli(config))
```
