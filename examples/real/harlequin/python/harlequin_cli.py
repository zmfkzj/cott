import sys
from typing import Never

from cott_runtime import CottList
from real.harlequin.app import (
    build_ide,
    install_app_actions,
    install_catalog_actions,
    install_editor_actions,
    install_query_actions,
    install_results_actions,
    run_ide_app,
)
from real.harlequin.main import prepare_harlequin
from real.harlequin.main_types import LaunchPlan_Exit


def main() -> Never:
    plan = prepare_harlequin(CottList(values=tuple(sys.argv[1:])))
    if isinstance(plan, LaunchPlan_Exit):
        sys.exit(plan.status)
    session = build_ide(plan.settings, plan.context, plan.keymaps)
    install_editor_actions(session)
    install_query_actions(session)
    install_catalog_actions(session)
    install_results_actions(session)
    install_app_actions(session)
    sys.exit(run_ide_app(session))


if __name__ == "__main__":
    main()
