import subprocess
import sys


def open_link(url: str) -> bool:
    command = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.Popen(
            [command, url],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return False
    return True
