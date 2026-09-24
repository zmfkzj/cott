import sys
from typing import Never

from cott_runtime import CottList


def run(arguments: CottList[str]) -> Never:
    """Defect: exits successfully without parsing or executing the requested arguments."""
    sys.exit(0)
