from sys import argv
from typing import Never

from cott_runtime import CottList
from real.harlequin.hsql import run_hsql


def main() -> Never:
    return run_hsql(CottList(values=tuple(argv[1:])))


if __name__ == "__main__":
    main()
