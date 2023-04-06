from abc import ABC, abstractmethod

from geometry import Vector2D


class Player(ABC):
    @abstractmethod
    def move(self, direction: Vector2D):
        ...
