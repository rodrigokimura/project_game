from abc import ABC, ABCMeta, abstractmethod

import pygame

from settings import BLOCK_SIZE


class BaseBlock(pygame.sprite.Sprite, ABC):
    def __init__(self, coords: tuple[int, int], *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.visible = 0
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = (coords[0] * BLOCK_SIZE, coords[1] * BLOCK_SIZE)

    @property
    def image(self):
        global cached_images
        return cached_images[self.__class__]

    @property
    def mask(self):
        global cached_masks
        return cached_masks[self.__class__]


class BaseHazard(BaseBlock, metaclass=ABCMeta):
    @property
    @abstractmethod
    def damage(self) -> int:
        ...


class Rock(BaseBlock):
    ...


class Spike(BaseHazard):
    damage: int = 10


class ChangingBlock(BaseBlock, metaclass=ABCMeta):
    interval: int = 1  # in days
    counter: int = 0  # in days
    state: int = 0

    @property
    @abstractmethod
    def max_state(self) -> int:
        ...

    def update(self):
        if self.state <= self.max_state:
            self.counter += 1
            if self.counter >= self.interval and self.state < self.max_state:
                self.state += 1


class Tree(ChangingBlock):
    interval: int = 1
    counter: int = 0
    images: list[pygame.surface.Surface]
    max_state: int = 1

    @property
    def mask(self):
        return pygame.mask.Mask((0, 0))

    @property
    def image(self):
        global tree_images
        try:
            return tree_images[self.state]
        except IndexError:
            return tree_images[0]


cached_images: dict[type[BaseBlock], pygame.surface.Surface] = {
    Rock: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    Spike: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
}
cached_masks: dict[type[BaseBlock], pygame.mask.Mask] = {}
tree_images = (
    pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
)


def get_tree_image(state: int, s: pygame.surface.Surface):
    global tree_images
    if state == 0:
        pygame.draw.rect(s, "yellow", s.get_rect(), 1)
    elif state == 1:
        pygame.draw.rect(s, "orange", s.get_rect(), 2)


def load_tree_images():
    for i, s in enumerate(tree_images):
        get_tree_image(i, s)


def draw_cached_images():
    global cached_images
    global cached_masks
    global tree_images

    img = cached_images[Rock]
    pygame.draw.rect(img, "blue", img.get_rect(), 1)
    cached_masks[Rock] = pygame.mask.from_surface(img)

    img = cached_images[Spike]
    pygame.draw.rect(img, "white", img.get_rect(), 1)
    cached_masks[Spike] = pygame.mask.from_surface(img)

    load_tree_images()
