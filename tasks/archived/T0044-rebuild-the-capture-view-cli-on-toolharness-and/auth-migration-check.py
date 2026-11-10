"""Run auth's real capture config through run_capture_cli without modifying auth (read-only shim)."""

import sys
from pathlib import Path

auth_script = Path(sys.argv[1]).resolve()
source = auth_script.read_text(encoding="utf-8")
source = source.replace("        build_capture_parser,\n", "").replace(
    "from support_python.cli import APP_AUTHOR, print_help, print_version", "from support_python.cli import APP_AUTHOR"
)
namespace = {"__file__": str(auth_script), "__name__": "auth_capture_view"}
exec(compile(source, str(auth_script), "exec"), namespace)

from support_python.capture import run_capture_cli  # noqa: E402

sys.exit(run_capture_cli(namespace["build_config"](), sys.argv[2:]))
