from __future__ import annotations

import random
from abc import ABC, ABCMeta, abstractmethod

import pygame

from materials import BaseMaterial
from materials import Rock as RockMaterial
from materials import Wood as WoodMaterial
from materials import all_materials
from settings import BLOCK_SIZE
from shooting import load_bullet_images
from sprites import GravitySprite
from utils.container import Container2d

COLLECTIBLE_SIZE = BLOCK_SIZE // 2


class BaseCollectible(GravitySprite, ABC, metaclass=ABCMeta):
    @property
    def collectible_image(self):
        return collectible_images.get(
            self.__class__, pygame.surface.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE))
        )

    @property
    @abstractmethod
    def block(self) -> BaseBlock:
        ...

    def __init__(
        self,
        coords: tuple[int, int],
        gravity: int | None = None,
        terminal_velocity: int | None = None,
        blocks: Container2d[BaseBlock] | None = None,
    ) -> None:
        self.coords = coords
        self.rect = self.collectible_image.get_rect().copy()
        padding = 1
        self.rect.centerx = random.randint(
            self.coords[0] * BLOCK_SIZE + COLLECTIBLE_SIZE // 2 + padding,
            (self.coords[0] + 1) * BLOCK_SIZE - COLLECTIBLE_SIZE // 2 - padding,
        )
        self.rect.centery = random.randint(
            self.coords[1] * BLOCK_SIZE + COLLECTIBLE_SIZE // 2 + padding,
            (self.coords[1] + 1) * BLOCK_SIZE - COLLECTIBLE_SIZE // 2 - padding,
        )
        self.pulling_velocity = pygame.math.Vector2()
        self.blocks = blocks
        super().__init__(gravity or 0, terminal_velocity or 0)

    def should_fall(self):
        if self.blocks is None:
            return False
        coords = (
            self.rect.centerx // BLOCK_SIZE,
            int((self.rect.bottom + 1) // BLOCK_SIZE),
        )
        block_below = self.blocks.get_element(coords)
        if block_below is None:
            return True
        self.rect.bottom = block_below.rect.top - 1
        self.velocity.y = min(self.velocity.y, 0)
        return False

    def update(self, dt: float):
        super().update(dt)
        self.update_position(dt)

    def update_position(self, dt: float):
        self.rect.centery += int(
            (self.velocity.y + self.pulling_velocity.y) * dt * BLOCK_SIZE * 10
        )
        self.rect.centerx += int(
            (self.velocity.x + self.pulling_velocity.x) * dt * BLOCK_SIZE * 10
        )
        self.coords = (
            self.rect.centerx // BLOCK_SIZE,
            self.rect.centery // BLOCK_SIZE,
        )


class BaseBlock(BaseCollectible, ABC, metaclass=ABCMeta):
    @property
    @abstractmethod
    def material(self) -> BaseMaterial:
        ...

    @property
    @abstractmethod
    def collectibles(self) -> dict[type[BaseCollectible], int]:
        ...

    def __init__(
        self,
        coords: tuple[int, int],
        gravity: int | None = None,
        terminal_velocity: int | None = None,
        blocks: Container2d[BaseBlock] | None = None,
    ) -> None:
        super().__init__(coords, gravity, terminal_velocity, blocks)
        self.rect: pygame.rect.Rect
        self.coords = coords
        self.rect.x, self.rect.y = (coords[0] * BLOCK_SIZE, coords[1] * BLOCK_SIZE)
        self.integrity: float = self.material.resistance

    @property
    def image(self):
        return cached_images[self.__class__]

    @property
    def mask(self):
        return cached_masks[self.__class__]


class BaseHazard(BaseBlock, metaclass=ABCMeta):
    @property
    @abstractmethod
    def damage(self) -> int:
        ...


class Rock(BaseBlock):
    material: BaseMaterial = all_materials[RockMaterial]

    @property
    def collectibles(self) -> dict[type[BaseCollectible], int]:
        return {self.__class__: 4}

    @property
    def block(self) -> BaseBlock:
        return self


class Wood(BaseBlock):
    material: BaseMaterial = all_materials[WoodMaterial]

    @property
    def collectibles(self) -> dict[type[BaseCollectible], int]:
        return {self.__class__: 1}

    @property
    def block(self) -> BaseBlock:
        return self


class Spike(BaseHazard):
    material: BaseMaterial = all_materials[RockMaterial]
    damage: int = 10

    @property
    def collectibles(self) -> dict[type[BaseCollectible], int]:
        return {Rock: 4}

    @property
    def block(self) -> BaseBlock:
        return self


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

    def update(self, _: float):
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
    material: BaseMaterial = all_materials[WoodMaterial]
    interval: int = 1
    counter: int = 0
    images: tuple[pygame.surface.Surface, ...] = tree_images
    max_state: int = 6

    @property
    def collectibles(self) -> dict[type[BaseCollectible], int]:
        return {Wood: 4}

    @property
    def block(self) -> BaseBlock:
        return self

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
    def rect(self, _):
        ...


cached_images: dict[type[BaseBlock], pygame.surface.Surface] = {
    Rock: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    Spike: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
    Wood: pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE)),
}

cached_masks: dict[type[BaseBlock], pygame.mask.Mask] = {}

collectible_images: dict[type[BaseCollectible], pygame.surface.Surface] = {
    Rock: pygame.surface.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
    Spike: pygame.surface.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
    Wood: pygame.surface.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
}


def get_tree_image(state: int, surf: pygame.surface.Surface):
    if state == 0:
        pygame.draw.rect(surf, "green", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 1)
    elif state == 1:
        pygame.draw.rect(surf, "green", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2)
        pygame.draw.rect(
            surf,
            "yellow",
            (BLOCK_SIZE // 4, BLOCK_SIZE, BLOCK_SIZE // 2, BLOCK_SIZE),
            1,
        )
    elif state == 2:
        pygame.draw.rect(surf, "green", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2)
        pygame.draw.rect(
            surf,
            "yellow",
            (BLOCK_SIZE // 4, BLOCK_SIZE, BLOCK_SIZE // 2, 2 * BLOCK_SIZE),
            1,
        )
    elif state == 3:
        pygame.draw.rect(surf, "green", (0, 0, 3 * BLOCK_SIZE, 3 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            surf,
            "yellow",
            (BLOCK_SIZE, 3 * BLOCK_SIZE, BLOCK_SIZE, 2 * BLOCK_SIZE),
            1,
        )
    elif state == 4:
        pygame.draw.rect(surf, "green", (0, 0, 3 * BLOCK_SIZE, 3 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            surf,
            "yellow",
            (BLOCK_SIZE, 3 * BLOCK_SIZE, BLOCK_SIZE, 3 * BLOCK_SIZE),
            1,
        )
    elif state == 5:
        pygame.draw.rect(surf, "green", (0, 0, 3 * BLOCK_SIZE, 4 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            surf,
            "yellow",
            (BLOCK_SIZE, 4 * BLOCK_SIZE, BLOCK_SIZE, 3 * BLOCK_SIZE),
            1,
        )
    elif state == 6:
        pygame.draw.rect(surf, "green", (0, 0, 5 * BLOCK_SIZE, 5 * BLOCK_SIZE), 2)
        pygame.draw.rect(
            surf,
            "yellow",
            (2 * BLOCK_SIZE, 5 * BLOCK_SIZE, BLOCK_SIZE, 4 * BLOCK_SIZE),
            1,
        )


def load_collectible_images():
    img = collectible_images[Rock]
    pygame.draw.rect(img, "blue", img.get_rect(), 1, 2)

    img = collectible_images[Spike]
    pygame.draw.rect(img, "blue", img.get_rect(), 1, 2)

    img = collectible_images[Wood]
    pygame.draw.rect(img, "yellow", img.get_rect(), 1, 2)


def load_tree_images():
    for index, surf in enumerate(tree_images):
        get_tree_image(index, surf)


def draw_cached_images():
    img = cached_images[Rock]
    pygame.draw.rect(img, "blue", img.get_rect(), 1)
    cached_masks[Rock] = pygame.mask.from_surface(img)

    img = cached_images[Spike]
    pygame.draw.rect(img, "white", img.get_rect(), 1)
    cached_masks[Spike] = pygame.mask.from_surface(img)

    img = cached_images[Wood]
    pygame.draw.rect(img, "white", img.get_rect(), 1)
    cached_masks[Wood] = pygame.mask.from_surface(img)

    load_tree_images()
    load_collectible_images()
    load_bullet_images()


def make_block(
    cls: type[BaseBlock],
    coords: tuple[int, int],
    gravity: int | None = None,
    terminal_velocity: int | None = None,
):
    x, y = coords
    block = cls((x, y), gravity, terminal_velocity)
    # for blocks, rect must be resized for proper collision detection
    block.rect.height = BLOCK_SIZE
    block.rect.width = BLOCK_SIZE
    return block
