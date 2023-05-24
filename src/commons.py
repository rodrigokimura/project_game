from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable
from uuid import UUID, uuid4


class Storable(ABC):
    id: UUID
    saved_at: datetime

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = uuid4()
        self.saved_at = datetime.now()

    def update_timestamp(self):
        self.saved_at = datetime.now()


class Loadable(ABC):
    class UnloadedObject(Exception):
        """Raises when trying to access unpickleble attrs set as None"""

    @abstractmethod
    def setup(self):
        ...

    @abstractmethod
    def unload(self):
        ...


class Timer:
    def __init__(self, timeout: float, callback: Callable | None = None) -> None:
        self.time = 0
        self.timeout = timeout
        self.is_over = False
        self.callback = callback

    def inc(self, dt: float):
        self.time += dt
        if self.time >= self.timeout:
            self.is_over = True
            if self.callback:
                self.callback()

    def reset(self):
        self.time = 0
        self.is_over = False
