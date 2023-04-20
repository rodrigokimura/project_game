from abc import ABC, abstractmethod
from itertools import product
from typing import Any

import pygame

from blocks import Rock, Spike
from player import BasePlayer
from settings import BLOCK_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH


class BaseWorld(ABC):
    def __init__(
        self,
        size: tuple[int, int],
        gravity: int,
        terminal_velocity: int,
        player: BasePlayer,
    ) -> None:
        super().__init__()
        self.size = pygame.math.Vector2(size)
        self.gravity: pygame.math.Vector2 = pygame.math.Vector2(0, gravity)
        self.terminal_velocity = terminal_velocity
        # self.surface = pygame.surface.Surface(self.size * BLOCK_SIZE)
        self.rect = pygame.rect.Rect(0, 0, *(self.size * BLOCK_SIZE))
        self.player = player
        self.all_sprites = [[]]
        self.populate()
        self.visibility_buffer = pygame.sprite.Group()
        self.collision_buffer = pygame.sprite.Group()

    @abstractmethod
    def populate(self):
        ...

    def update(self, dt: int, visibility_rect: pygame.rect.Rect):
        # self.surface.fill("black")
        self.visibility_buffer.empty()
        self.collision_buffer.empty()
        m = 3

        x1, y1 = visibility_rect.topleft
        x2, y2 = visibility_rect.bottomright
        x1, y1, x2, y2 = (
            x1 // BLOCK_SIZE,
            y1 // BLOCK_SIZE,
            x2 // BLOCK_SIZE,
            y2 // BLOCK_SIZE,
        )

        xp, yp = self.player.rect.center
        xp, yp = xp // BLOCK_SIZE, yp // BLOCK_SIZE

        for x, y in product(range(x1 - m, x2 + m), range(y1 - m, y2 + m)):
            try:
                s = self.all_sprites[y][x]
            except IndexError:
                continue
            if s is None:
                continue
            self.visibility_buffer.add(s)
            if x in range(xp - m, xp + m) and y in range(yp - m, yp + m):
                self.collision_buffer.add(s)

        self.player.update(dt)

        # self.visibility_buffer.draw(self.surface)
        # self.surface.blit(self.player.image, self.player.rect)


class World(BaseWorld):
    def populate(self):
        pass


class SampleWorld(BaseWorld):
    def populate(self):
        reference = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        blocks = []

        # first level
        for i in range(190):
            block = Rock()
            block.rect.center = (
                int(reference.x + (i - 10) * BLOCK_SIZE),
                int(reference.y + 132),
            )
            blocks.append(block)

        # spikes
        for i in range(2):
            block = Spike()
            block.rect.center = (
                int(reference.x + (i - 10) * BLOCK_SIZE),
                int(reference.y + 132 - BLOCK_SIZE),
            )
            blocks.append(block)

        # second level
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(reference.x + i * BLOCK_SIZE + 10 * BLOCK_SIZE),
                int(reference.y + 132 - 3 * BLOCK_SIZE),
            )
            blocks.append(block)

        # third level
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(reference.x + i * BLOCK_SIZE + 15 * BLOCK_SIZE),
                int(reference.y + 132 - 8 * BLOCK_SIZE),
            )
            blocks.append(block)

        # slope
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(reference.x + i * BLOCK_SIZE + 30 * BLOCK_SIZE),
                int(reference.y + 132 - (i + 1) * BLOCK_SIZE),
            )
            blocks.append(block)

        # wall
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(reference.x - 5 * BLOCK_SIZE),
                int(reference.y + 132 - (i + 1) * BLOCK_SIZE),
            )
            blocks.append(block)

        # self.all_sprites.add(*blocks)


class SimpleWorld(BaseWorld):
    def __init__(
        self,
        size: tuple[int, int],
        gravity: int,
        terminal_velocity: int,
        player: BasePlayer,
    ) -> None:
        super().__init__(size, gravity, terminal_velocity, player)
        self.rect_buffer = pygame.rect.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.visibility_buffer = pygame.sprite.Group()
        self.collision_buffer = pygame.sprite.Group()
        self.player.collidable_sprites_buffer = self.collision_buffer

    def populate(self):
        blocks = []
        for y in range(int(self.size.y)):
            row = []
            for x in range(int(self.size.x)):
                block = Rock()
                block.rect.x = x * BLOCK_SIZE
                block.rect.y = y * BLOCK_SIZE
                if y > (self.size.y / 2):
                    row.append(block)
                else:
                    row.append(None)
            blocks.append(row)
        self.all_sprites = blocks


class GravitySprite(ABC, pygame.sprite.Sprite):
    def __init__(
        self, gravity: int, terminal_velocity: int, *groups: pygame.sprite.Group
    ) -> None:
        super().__init__(*groups)
        self.collidable_sprites_buffer = pygame.sprite.Group()

        self.pos = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.acceleration = pygame.math.Vector2(0, gravity)
        self.terminal_velocity = terminal_velocity

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
