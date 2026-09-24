import random

from cott_runtime import U8, U64


def sample_index(limit: U8, seed: U64) -> U8:
    return random.Random(seed).randrange(limit)
