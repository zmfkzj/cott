# track-metadata

## Purpose
Normalize a music-track draft and convert it into display and sorting metadata.

## Key points
- Reject track number 0 first, then trim leading and trailing Unicode whitespace from the title, artist, and album, and check an empty title and empty artist in that order.
- Build the display value as `artist — title`; join the lowercase artist, album, and at-least-four-digit track number with NUL characters for the sort key.
