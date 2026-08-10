from cott_runtime import I64
from curriculum.module_export_snapshot_types import ModuleSnapshot


def build_snapshot(exported_x: I64, module_x: I64) -> ModuleSnapshot:
    return ModuleSnapshot(exported_x=exported_x, module_x=module_x)
