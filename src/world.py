from abc import ABC, abstractmethod
from itertools import product

import pygame

from blocks import Rock, Spike, Tree, draw_cached_images
from collectibles import BaseCollectible
from day_cycle import convert_to_time, get_day_part
from log import log
from player import BasePlayer, Player
from settings import BLOCK_SIZE, DAY_DURATION, DEBUG, WORLD_SIZE


class BaseWorld(ABC):
    DAY_DURATION = DAY_DURATION

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
        self.changing_blocks = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.visibility_buffer = pygame.sprite.Group()
        self.collision_buffer = pygame.sprite.Group()
        self.populate()
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
        self.collectibles.update(dt, self.all_blocks.copy())

        # perform block destruction
        events = pygame.event.get(Player.DESTROY_BLOCK)
        for _ in events:
            self.destroy_block(player, dt)

    def update_time(self, dt: int):
        self.age += dt
        self.time_of_day += dt
        if self.time_of_day >= self.DAY_DURATION:
            self.time_of_day = 0
            self.update_changing_blocks()
            if DEBUG:
                log("Updating ChangingBlock instances")

    def update_changing_blocks(self):
        self.changing_blocks.update()

    @property
    def relative_time(self):
        return self.time_of_day / self.DAY_DURATION

    @property
    def time(self):
        return convert_to_time(self.relative_time)

    @property
    def day_part(self):
        return get_day_part(self.time)

    def get_block(self, coords: tuple[int, int]):
        try:
            return self.all_blocks[coords[1]][coords[0]]
        except IndexError:
            return None

    def destroy_block(self, player: BasePlayer, dt: int):
        coords = player.get_cursor_coords()
        block = self.get_block(coords)
        if block is None:
            return
        destroyed = player.destroy(block, dt)
        if not destroyed:
            return
        self.all_blocks[coords[1]][coords[0]] = None
        log(block.collectibles)
        for collectible_class, count in block.collectibles.items():
            collectible_class: type[BaseCollectible]
            for _ in range(count):
                collectible_class(
                    coords,
                    int(self.gravity.y),
                    self.terminal_velocity,
                    self.collectibles,
                )

        del block


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

        # trees
        _y = y
        _x = x - 5
        block = Tree((_x, _y))
        self.all_blocks[_y][_x] = block
        self.changing_blocks.add(block)

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
