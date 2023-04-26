import random
from abc import ABC, ABCMeta
from typing import Any

import pygame

from log import log
from settings import BLOCK_SIZE
from sprites import GravitySprite

COLLECTIBLE_SIZE = BLOCK_SIZE // 2


class BaseCollectible(GravitySprite, ABC, metaclass=ABCMeta):
    @property
    def image(self):
        global collectible_images
        return collectible_images[self.__class__]

    def __init__(
        self,
        coords: tuple[int, int],
        gravity: int,
        terminal_velocity: int,
        *groups: pygame.sprite.Group
    ) -> None:
        self.coords = coords
        self.rect = self.image.get_rect().copy()
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
        super().__init__(gravity, terminal_velocity, *groups)

    def should_fall(self, all_blocks):
        block_below = all_blocks[int((self.rect.bottom + 1) // BLOCK_SIZE)][
            self.rect.centerx // BLOCK_SIZE
        ]
        if block_below is None:
            return True
        self.rect.bottom = block_below.rect.top - 1
        if self.velocity.y > 0:
            self.velocity.y = 0
        return False

    def update(
        self,
        dt: int,
        all_blocks: list[list[pygame.sprite.Sprite]],
        *args: Any,
        **kwargs: Any
    ) -> None:
        self.fall(dt, all_blocks)
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


class Rock(BaseCollectible):
    ...


class Wood(BaseCollectible):
    ...


collectible_images: dict[type[BaseCollectible], pygame.surface.Surface] = {
    Rock: pygame.surface.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
    Wood: pygame.surface.Surface((COLLECTIBLE_SIZE, COLLECTIBLE_SIZE)),
}


def load_collectible_images():
    global collectible_images
    img = collectible_images[Rock]
    pygame.draw.rect(img, "blue", img.get_rect(), 1, 2)
    img = collectible_images[Wood]
    pygame.draw.rect(img, "yellow", img.get_rect(), 1, 2)
