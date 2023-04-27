from abc import ABC, ABCMeta, abstractmethod
from inspect import isabstract


class BaseMaterial(ABC, metaclass=ABCMeta):
    @property
    @abstractmethod
    def resistance(self) -> float:
        ...


class Wood(BaseMaterial):
    resistance: float = 5.0


class Rock(BaseMaterial):
    resistance: float = 10.0


all_materials: dict[type[BaseMaterial], BaseMaterial] = {
    m: m() for m in BaseMaterial.__subclasses__() if not isabstract(m)  # type: ignore
}
