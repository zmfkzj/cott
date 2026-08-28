from __future__ import annotations

from curriculum.pair_tuple import make_coordinate_pair, swap_pair

pair = make_coordinate_pair(10, 20)
print(f"Original pair: ({pair[0]}, {pair[1]})")
swapped = swap_pair(pair)
print(f"Swapped pair: ({swapped[0]}, {swapped[1]})")
