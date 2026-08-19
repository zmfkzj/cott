# archive-request

## Purpose
Validate an archive request's URL and capture selection to create a deterministic archive plan.

## Key points
- Return `EmptySelection` before parsing the URL unless HTML or media is selected. Normalize only selected HTTP and HTTPS URLs.
- Normalization lowercases only the scheme and host, preserving user info, port, path, query, and fragment. Invalid percent escapes and malformed URLs are `InvalidUrl`.
- When both captures are requested, the plan's capture order is always HTML, then media.
