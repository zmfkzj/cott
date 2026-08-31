from sys import argv
from typing import Never

from cott_runtime import CottList
from real.yt_dlp import run


def main() -> Never:
    return run(CottList(values=tuple(argv[1:])))


if __name__ == "__main__":
    main()
