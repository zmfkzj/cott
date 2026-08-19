# rock-paper-scissors

## Purpose
Purely determine the winner from two rock-paper-scissors moves.

## Key points
- The `RpsMove` and `RoundResult` enums model valid inputs and the closed set of user-win, computer-win, and draw outcomes.
- `user_beats_computer` returns `true` only for the three winning relationships: rock-scissors, paper-rock, and scissors-paper.
- `decide_round` handles equal moves as a draw first and reuses the helper, so the decision rules can be learned without random selection or I/O.
