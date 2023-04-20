from abc import ABC, ABCMeta, abstractmethod

import pygame

from settings import BLOCK_SIZE


class BaseBlock(pygame.sprite.DirtySprite, ABC):
    def __init__(self, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.visible = 0
        self.image = pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)).convert_alpha()
        self.draw()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()

    @abstractmethod
    def draw(self):
        ...


class BaseHazard(BaseBlock, metaclass=ABCMeta):
    @property
    @abstractmethod
    def damage(self) -> int:
        ...


class Rock(BaseBlock):
    def draw(self):
        pygame.draw.rect(self.image, "blue", self.image.get_rect(), 1)


class Spike(BaseHazard):
    is_hazard: bool = True
    damage: int = 10

    def draw(self):
        pygame.draw.rect(self.image, "red", self.image.get_rect(), 1)
