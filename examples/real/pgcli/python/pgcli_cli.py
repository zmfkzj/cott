from __future__ import annotations

import sys

from cott_runtime import CottList
from real.pgcli import run


if __name__ == "__main__":
    run(CottList(values=tuple(sys.argv[1:])))
