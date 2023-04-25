from abc import ABC, ABCMeta, abstractmethod

import pygame

from materials import BaseMaterial
from materials import Rock as RockMaterial
from materials import Wood, all_materials
from settings import BLOCK_SIZE


class BaseBlock(pygame.sprite.Sprite, ABC, metaclass=ABCMeta):
    @property
    @abstractmethod
    def material(self) -> BaseMaterial:
        ...

    def __init__(self, coords: tuple[int, int], *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.coords = coords
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = (coords[0] * BLOCK_SIZE, coords[1] * BLOCK_SIZE)
        self.integrity: float = self.material.resistance

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
    material: BaseMaterial = all_materials[RockMaterial]


class Spike(BaseHazard):
    material: BaseMaterial = all_materials[RockMaterial]
    damage: int = 10


class ChangingBlock(BaseBlock, metaclass=ABCMeta):
    interval: int = 1  # in days
    counter: int = 0  # in days
    state: int = 0

    @property
    @abstractmethod
    def images(self) -> tuple[pygame.surface.Surface, ...]:
        ...

    @property
    def image(self):
        try:
            return self.images[self.state]
        except IndexError:
            return self.images[0]

    @property
    @abstractmethod
    def max_state(self) -> int:
        ...

    def update(self):
        if self.state <= self.max_state:
            self.counter += 1
            if self.counter >= self.interval and self.state < self.max_state:
                self.state += 1


tree_images = (
    pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    pygame.surface.Surface((BLOCK_SIZE, 2 * BLOCK_SIZE)),
    pygame.surface.Surface((BLOCK_SIZE, 3 * BLOCK_SIZE)),
    pygame.surface.Surface((3 * BLOCK_SIZE, 5 * BLOCK_SIZE)),
    pygame.surface.Surface((3 * BLOCK_SIZE, 6 * BLOCK_SIZE)),
    pygame.surface.Surface((3 * BLOCK_SIZE, 7 * BLOCK_SIZE)),
    pygame.surface.Surface((5 * BLOCK_SIZE, 9 * BLOCK_SIZE)),
)


class Tree(ChangingBlock):
    material: BaseMaterial = all_materials[Wood]
    interval: int = 1
    counter: int = 0
    images: tuple[pygame.surface.Surface, ...] = tree_images
    max_state: int = 6

    @property
    def mask(self):
        return pygame.mask.Mask((0, 0))

    @property
    def rect(self):
        rect = self.image.get_rect()
        rect.x, rect.y = (self.coords[0] * BLOCK_SIZE, self.coords[1] * BLOCK_SIZE)
        if self.state == 0:
            pass
        elif self.state == 1:
            rect.y -= BLOCK_SIZE
        elif self.state == 2:
            rect.y -= 2 * BLOCK_SIZE
        elif self.state == 3:
            rect.x -= 1 * BLOCK_SIZE
            rect.y -= 4 * BLOCK_SIZE
        elif self.state == 4:
            rect.x -= 1 * BLOCK_SIZE
            rect.y -= 5 * BLOCK_SIZE
        elif self.state == 5:
            rect.x -= 1 * BLOCK_SIZE
            rect.y -= 6 * BLOCK_SIZE
        elif self.state == 6:
            rect.x -= 2 * BLOCK_SIZE
            rect.y -= 8 * BLOCK_SIZE
        return rect

    @rect.setter
    def rect(self, value):
        pass


cached_images: dict[type[BaseBlock], pygame.surface.Surface] = {
    Rock: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    Spike: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
}
cached_masks: dict[type[BaseBlock], pygame.mask.Mask] = {}


def get_tree_image(state: int, s: pygame.surface.Surface):
    global tree_images
    if state == 0:
        pygame.draw.rect(s, "green", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 1)
    elif state == 1:
        pygame.draw.rect(s, "green", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2)
        pygame.draw.rect(
            s, "yellow", (BLOCK_SIZE // 4, BLOCK_SIZE, BLOCK_SIZE // 2, BLOCK_SIZE), 1
        )
    elif state == 2:
        pygame.draw.rect(s, "green", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2)
        pygame.draw.rect(
            s,
            "yellow",
            (BLOCK_SIZE // 4, BLOCK_SIZE, BLOCK_SIZE // 2, 2 * BLOCK_SIZE),
            1,
        )
    elif state == 3:
        pygame.draw.rect(s, "green", (0, 0, 3 * BLOCK_SIZE, 3 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            s,
            "yellow",
            (BLOCK_SIZE, 3 * BLOCK_SIZE, BLOCK_SIZE, 2 * BLOCK_SIZE),
            1,
        )
    elif state == 4:
        pygame.draw.rect(s, "green", (0, 0, 3 * BLOCK_SIZE, 3 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            s,
            "yellow",
            (BLOCK_SIZE, 3 * BLOCK_SIZE, BLOCK_SIZE, 3 * BLOCK_SIZE),
            1,
        )
    elif state == 5:
        pygame.draw.rect(s, "green", (0, 0, 3 * BLOCK_SIZE, 4 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            s,
            "yellow",
            (BLOCK_SIZE, 4 * BLOCK_SIZE, BLOCK_SIZE, 3 * BLOCK_SIZE),
            1,
        )
    elif state == 6:
        pygame.draw.rect(s, "green", (0, 0, 5 * BLOCK_SIZE, 5 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            s,
            "yellow",
            (2 * BLOCK_SIZE, 5 * BLOCK_SIZE, BLOCK_SIZE, 4 * BLOCK_SIZE),
            1,
        )


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
