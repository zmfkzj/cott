import os
import sys

from cott_runtime import CottList
from real.toolong.cli import run_command_line


def main() -> int:
    return run_command_line(CottList(values=tuple(sys.argv[1:])), os.path.basename(sys.argv[0]))


if __name__ == "__main__":
    raise SystemExit(main())
