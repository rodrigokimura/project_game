from abc import ABC, abstractmethod
from datetime import datetime
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
