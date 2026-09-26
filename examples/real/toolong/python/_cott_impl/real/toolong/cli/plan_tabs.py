from pathlib import Path

from cott_runtime import CottList
from real.toolong.cli import sort_paths
from real.toolong.model_types import TabPlan


def plan_tabs(files: CottList[str], merge: bool) -> CottList[TabPlan]:
    ordered: CottList[str] = sort_paths(files)
    if merge and len(ordered) > 1:
        paths: list[Path] = [Path(file) for file in ordered]
        title: str = " + ".join([path.name for path in paths])
        return CottList(values=[TabPlan(title=title, paths=CottList(values=paths), merged=True)])
    return CottList(values=[TabPlan(title=file, paths=CottList(values=[Path(file)]), merged=False) for file in ordered])
