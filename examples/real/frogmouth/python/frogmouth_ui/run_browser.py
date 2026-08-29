from __future__ import annotations

import os
from pathlib import Path
import sys

from cott_runtime import CottList, Nothing, Option, Some, UNIT, Unit
from frogmouth.application import parse_initial_location, resolve_state_path
from .create_browser_app import create_browser_app


def run_browser() -> Unit:
    initial_location = parse_initial_location(CottList(values=sys.argv[1:]))
    app_data_value = os.environ.get("APPDATA")
    app_data: Option[str] = (
        Some(value=app_data_value) if app_data_value else Nothing()
    )
    xdg_data_home_value = os.environ.get("XDG_DATA_HOME")
    xdg_data_home: Option[str] = (
        Some(value=xdg_data_home_value) if xdg_data_home_value else Nothing()
    )
    state_path = resolve_state_path(
        os.name if os.name == "nt" else sys.platform,
        Path.home(),
        app_data,
        xdg_data_home,
    )

    _ = create_browser_app(
        initial_location,
        Path.cwd(),
        state_path,
    ).run()
    return UNIT

if __name__ == "__main__":
    run_browser()
