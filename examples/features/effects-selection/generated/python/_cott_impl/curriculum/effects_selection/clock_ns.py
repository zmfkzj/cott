from __future__ import annotations

from cott_runtime import U64, _cott_fixture_now


def clock_ns() -> U64:
    return _cott_fixture_now() * 1_000_000
