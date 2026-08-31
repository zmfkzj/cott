from pathlib import Path
import sys

from cott_runtime import Nothing, Option, Some
from frogmouth_ui.create_browser_app import create_browser_app


def run_browser() -> int:
    initial: Option[str] = Some(value=sys.argv[1]) if len(sys.argv) > 1 else Nothing()
    app = create_browser_app(initial, Path.cwd())
    app.run()
    return app.return_code or 0


if __name__ == "__main__":
    raise SystemExit(run_browser())
