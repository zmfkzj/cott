# numbers-to-words

## Purpose
Convert I64 integers to regular English cardinal notation.

## Key points
- `spell_under_thousand` handles only 0–999 and separates small-unit conversion by inserting `and` when a hundred has a remainder.
- `spell_cardinal` walks thousand groups in descending order and attaches only the needed scales from `thousand` through `quintillion`.
- The Python implementation safely handles the absolute value of the smallest negative I64; zero is `Zero`, and negatives use the `(negative) ` prefix.
