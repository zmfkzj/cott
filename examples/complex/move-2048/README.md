# move-2048

## Purpose
Apply a move in one direction to a 4×4 2048 board and calculate the score increase and whether it changed.

## Key points
- The board must contain 16 row-major cells; return a size error before tile errors, and permit only 0 or powers of two within `U16` range as tiles.
- Order each directional row or column in the move direction, compact it, merge equal tiles only once, then pad it with 0 and restore it. Overflow of a merged tile or accumulated score is `ScoreOverflow`.
