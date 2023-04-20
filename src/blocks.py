from abc import ABC, ABCMeta, abstractmethod

import pygame

from settings import BLOCK_SIZE


class BaseBlock(pygame.sprite.Sprite, ABC):
    def __init__(self, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.visible = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()

    @property
    def image(self):
        global cached_images
        return cached_images[self.__class__]


class BaseHazard(BaseBlock, metaclass=ABCMeta):
    @property
    @abstractmethod
    def damage(self) -> int:
        ...


class Rock(BaseBlock):
    ...


class Spike(BaseHazard):
    is_hazard: bool = True
    damage: int = 10


cached_images: dict[type[BaseBlock], pygame.surface.Surface] = {
    Rock: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    Spike: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
}


def draw_cached_images():
    global cached_images
    img = cached_images[Rock]
    pygame.draw.rect(img, "blue", img.get_rect(), 1)
    img = cached_images[Spike]
    pygame.draw.rect(img, "white", img.get_rect(), 1)
