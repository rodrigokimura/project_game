from abc import ABC, abstractmethod
from itertools import product
from typing import Any

import pygame

from blocks import Rock, Spike, draw_cached_images
from day_cycle import convert_to_time, get_day_part
from player import BasePlayer
from settings import BLOCK_SIZE, WORLD_SIZE


class BaseWorld(ABC):
    DAY_DURATION = 5 * 60

    def __init__(
        self,
        size: tuple[int, int],
        gravity: int,
        terminal_velocity: int,
    ) -> None:
        super().__init__()
        self.size = pygame.math.Vector2(size)
        self.gravity: pygame.math.Vector2 = pygame.math.Vector2(0, gravity)
        self.terminal_velocity = terminal_velocity
        self.rect = pygame.rect.Rect(0, 0, *(self.size * BLOCK_SIZE))
        self.all_blocks = [[]]
        self.populate()
        self.visibility_buffer = pygame.sprite.Group()
        self.collision_buffer = pygame.sprite.Group()
        self.age = 0  # in seconds
        self.time_of_day = 0  # cycling counter

    @abstractmethod
    def populate(self):
        ...

    def update(self, dt: int, visibility_rect: pygame.rect.Rect, player: BasePlayer):
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

        xp, yp = player.rect.center
        xp, yp = xp // BLOCK_SIZE, yp // BLOCK_SIZE

        for x, y in product(range(x1 - m, x2 + m), range(y1 - m, y2 + m)):
            try:
                s = self.all_blocks[y][x]
            except IndexError:
                continue
            if s is None:
                continue
            self.visibility_buffer.add(s)
            if x in range(xp - m, xp + m) and y in range(yp - m, yp + m):
                self.collision_buffer.add(s)

        self.update_time(dt)
        player.update(dt)

    def update_time(self, dt: int):
        self.age += dt
        self.time_of_day += dt
        if self.time_of_day >= self.DAY_DURATION:
            self.time_of_day = 0

        print(self.relative_time)
        print(self.time)
        print(self.day_part)

    @property
    def relative_time(self):
        return self.time_of_day / self.DAY_DURATION

    @property
    def time(self):
        return convert_to_time(self.relative_time)

    @property
    def day_part(self):
        return get_day_part(self.time)


class World(BaseWorld):
    def populate(self):
        ...


class SimpleWorld(BaseWorld):
    def __init__(
        self,
        size: tuple[int, int],
        gravity: int,
        terminal_velocity: int,
    ) -> None:
        super().__init__(size, gravity, terminal_velocity)
        self.visibility_buffer = pygame.sprite.Group()
        self.collision_buffer = pygame.sprite.Group()
        draw_cached_images()

    def populate(self):
        blocks = []
        for y in range(int(self.size.y)):
            row = []
            for x in range(int(self.size.x)):
                block = Rock((x, y))
                if y > (self.size.y / 2):
                    row.append(block)
                else:
                    row.append(None)
            blocks.append(row)
        self.all_blocks = blocks


class SampleWorld(SimpleWorld):
    def populate(self):
        super().populate()
        x, y = WORLD_SIZE
        x, y = x // 2, y // 2

        # spikes
        _y = y + 1
        _x = x + 5
        for i in range(1, 5):
            _x = x + i
            block = Spike((_x, _y))
            self.all_blocks[_y][_x] = block

        # second level
        _y = y - 2
        for i in range(10):
            _x = x + 10 + i
            block = Rock((_x, _y))
            self.all_blocks[_y][_x] = block

        # third level
        _y = y - 6
        for i in range(10):
            _x = x + 15 + i
            block = Rock((_x, _y))
            self.all_blocks[_y][_x] = block

        # slope
        _y = y + 1
        _x = x + 30
        for i in range(10):
            _x += 1
            _y -= 1
            block = Rock((_x, _y))
            self.all_blocks[_y][_x] = block


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
        ...
