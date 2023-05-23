from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from inspect import isabstract


@dataclass
class BaseMaterial(ABC, metaclass=ABCMeta):
    @property
    @abstractmethod
    def resistance(self) -> float:
        ...


@dataclass
class Wood(BaseMaterial):
    resistance: float = 5.0


@dataclass
class Rock(BaseMaterial):
    resistance: float = 10.0


all_materials: dict[type[BaseMaterial], BaseMaterial] = {
    m: m() for m in BaseMaterial.__subclasses__() if not isabstract(m)  # type: ignore
}
