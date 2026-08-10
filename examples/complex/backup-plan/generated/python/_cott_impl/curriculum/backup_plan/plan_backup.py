from pathlib import Path

from cott_runtime import Err, Ok, Result
from curriculum.backup_plan import classify_backup_paths
from curriculum.backup_plan_types import BackupPlan, BackupPlanError, BackupPlanError_BlankContentId, BackupPlanError_DuplicatePath, BackupPlanError_EmptyPath, BackupPlanRequest


def plan_backup(request: BackupPlanRequest) -> Result[BackupPlan, BackupPlanError]:
    seen_paths: set[Path] = set()
    empty_path: Path = Path()

    for backup_path in request.paths:
        path = backup_path.path
        if path == empty_path:
            return Err(error=BackupPlanError_EmptyPath())

        content_id = backup_path.content_id
        if not content_id.strip():
            return Err(error=BackupPlanError_BlankContentId())

        if path in seen_paths:
            return Err(error=BackupPlanError_DuplicatePath())
        seen_paths.add(path)

    return Ok(value=classify_backup_paths(request.paths, request.known_content_ids))
