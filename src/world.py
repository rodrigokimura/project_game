from abc import ABC, abstractmethod
from typing import Any, Optional

import pygame


class World(pygame.sprite.Group):
    gravity: int = 10


class GravitySprite(ABC, pygame.sprite.Sprite):
    def __init__(self, world: World, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.collidable_sprites_buffer = pygame.sprite.Group()
        self.world = world
        self.gravity = self.world.gravity
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2()

    def update(self, dt, *args: Any, **kwargs: Any) -> None:
        self.fall(dt)

    def fall(self, dt: int):
        if self.should_fall():
            self.direction.y += self.gravity * dt
            self.pos.y += int(self.direction.y)

    @abstractmethod
    def should_fall(self) -> None:
        pass


class Ground(pygame.sprite.Sprite):
    def __init__(
        self, pos: Optional[tuple[float, float]], *groups: pygame.sprite.Group
    ) -> None:
        super().__init__(*groups)
        pos = pos or pygame.display.get_surface().get_rect().center
        self.pos = pygame.Vector2(*pos)
        self.image = pygame.surface.Surface((1000, 32))
        self.image.fill("red")
        self.rect = self.image.get_rect(center=self.pos)
