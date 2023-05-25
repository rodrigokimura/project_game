from typing import Callable


class Timer:
    def __init__(self, timeout: float, callback: Callable | None = None) -> None:
        self.time = 0
        self.timeout = timeout
        self.is_set = False
        self.callback = callback

    def start(self):
        self.is_set = True

    def stop(self):
        self.is_set = False

    def inc(self, dt: float):
        if not self.is_set:
            return

        self.time += dt
        if self.time >= self.timeout:
            if self.callback:
                self.callback()

    def reset(self):
        self.time = 0
        self.is_set = False
