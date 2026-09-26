from cott_runtime import CottList

from real.harlequin.cli_types import HARLEQUIN_VERSION


def harlequin_version_text(adapter_names: CottList[str]) -> str:
    lines = [f"harlequin, version {HARLEQUIN_VERSION}\n\nInstalled Adapters:\n"]
    for name in sorted(adapter_names):
        lines.append(f"  - {name}, version {HARLEQUIN_VERSION}\n")
    return "".join(lines)
