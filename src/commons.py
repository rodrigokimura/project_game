from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID, uuid4

from blocks import HasDamage


class Storable(ABC):
    _id: UUID
    saved_at: datetime

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._id = uuid4()
        self.saved_at = datetime.now()

    def update_timestamp(self):
        self.saved_at = datetime.now()

    @property
    def id(self):  # pylint: disable=invalid-name
        return self._id


class Loadable(ABC):
    class UnloadedObject(Exception):
        """Raises when trying to access unpickleble attrs set as None"""

    @abstractmethod
    def setup(self):
        ...

    @abstractmethod
    def unload(self):
        ...


class Damageable(ABC):
    max_health_points: int
    health_points: int

    @abstractmethod
    def take_damage(self, hazard: HasDamage):
        ...
