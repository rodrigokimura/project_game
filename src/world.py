from abc import ABC, abstractmethod
from typing import Any

import pygame

from settings import BLOCK_SIZE


class World(pygame.sprite.Group):
    def __init__(
        self, size: tuple[int, int], gravity: int, terminal_velocity: int
    ) -> None:
        super().__init__()
        self.size = pygame.math.Vector2(size)
        self.gravity: pygame.math.Vector2 = pygame.math.Vector2(0, gravity)
        self.terminal_velocity = terminal_velocity
        self.surface = pygame.surface.Surface(self.size * BLOCK_SIZE)


class GravitySprite(ABC, pygame.sprite.Sprite):
    def __init__(self, world: World, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.collidable_sprites_buffer = pygame.sprite.Group()
        self.world = world

        self.pos = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.acceleration = self.world.gravity
        self.terminal_velocity = self.world.terminal_velocity

    def update(self, dt, *args: Any, **kwargs: Any) -> None:
        self.fall(dt)

    def fall(self, dt: int):
        if self.should_fall():
            self.velocity.y += self.acceleration.y * dt
            if abs(self.velocity.y) > self.terminal_velocity:
                self.velocity.y = self.terminal_velocity * (
                    1 if self.velocity.y > 0 else -1
                )

    @abstractmethod
    def should_fall(self) -> None:
        pass
