# backup-plan

## Purpose
Validate backup paths and classify them as known-content reuse or new uploads.

## Key points
- In input order, validate an empty path, blank content ID, and duplicate path; duplicate detection uses every previously valid path.
- Process only the first occurrence of each content ID: put known IDs in the reuse list and paths for unknown IDs in the upload list, both in input order.
