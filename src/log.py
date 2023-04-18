from typing import Any

try:
    from rich import print
except ImportError:
    pass


def log(msg: Any):
    print(msg)
