# tic-tac-toe

## Purpose
Safely apply one move to a 3×3 tic-tac-toe board and determine the game state.

## Key points
- The `Cell`, `Player`, and `Outcome` enums and the `MoveResult` struct explicitly carry the board, next turn, and outcome.
- The Python implementation validates the nine-cell board length first, then the position range, then X/O counts and win consistency.
- It distinguishes position range, turn, ended-game, and occupied-cell errors in the specified priority as `Result` errors, and returns a newly constructed board on success.
