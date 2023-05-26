from typing import Any

try:
    from rich import print as _print
except ImportError:
    pass


def log(msg: Any):
    _print(msg)
