from pathlib import Path
from cott_runtime import CottList, CottSet
from curriculum.backup_plan_types import BackupPath, BackupPlan


def classify_backup_paths(paths: CottList[BackupPath], known_content_ids: CottSet[str]) -> BackupPlan:
    seen_content_ids: set[str] = set()
    upload_paths: list[Path] = []
    reused_content_ids: list[str] = []

    for backup_path in paths:
        content_id = backup_path.content_id
        if content_id in seen_content_ids:
            continue

        seen_content_ids.add(content_id)
        if content_id in known_content_ids:
            reused_content_ids.append(content_id)
        else:
            upload_paths.append(backup_path.path)

    return BackupPlan(
        upload_paths=CottList(values=upload_paths),
        reused_content_ids=CottList(values=reused_content_ids),
    )
