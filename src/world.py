from abc import ABC, abstractmethod
from itertools import product

import pygame

from blocks import (
    BaseBlock,
    BaseCollectible,
    Rock,
    Spike,
    Tree,
    draw_cached_images,
    make_block,
)
from characters import BaseCharacter, Player
from commons import Loadable, Storable
from day_cycle import convert_to_time, get_day_part
from log import log
from settings import BLOCK_SIZE, DAY_DURATION, DEBUG, WORLD_SIZE
from utils.container import Container2d


class BaseWorld(Storable, Loadable, ABC):
    DAY_DURATION = DAY_DURATION

    def __init__(
        self,
        size: tuple[int, int],
        gravity: int,
        terminal_velocity: int,
    ) -> None:
        super().__init__()
        self.size = pygame.math.Vector2(size)
        self.gravity = pygame.math.Vector2(0, gravity)
        self.terminal_velocity = terminal_velocity
        self.rect = pygame.rect.Rect(0, 0, *(self.size * BLOCK_SIZE))

        self.setup()
        self.age = 0  # in seconds
        self.time_of_day = 0  # cycling counter

    @abstractmethod
    def populate(self):
        ...

    def setup(self):
        self.blocks = Container2d(WORLD_SIZE)
        self.changing_blocks = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.visibility_buffer = pygame.sprite.Group()
        self.collision_buffer = pygame.sprite.Group()
        self.characters_buffer = pygame.sprite.Group()

        self.populate()

    def unload(self):
        self.blocks.empty()
        self.changing_blocks.empty()
        self.collectibles.empty()
        self.visibility_buffer.empty()
        self.collision_buffer.empty()
        self.characters_buffer.empty()

    def update(
        self,
        dt: float,
        visibility_rect: pygame.rect.Rect,
        player: BaseCharacter,
    ):
        self.visibility_buffer.empty()
        margin = 3

        x_1, y_1 = visibility_rect.topleft
        x_2, y_2 = visibility_rect.bottomright
        x_1, y_1, x_2, y_2 = (
            x_1 // BLOCK_SIZE,
            y_1 // BLOCK_SIZE,
            x_2 // BLOCK_SIZE,
            y_2 // BLOCK_SIZE,
        )

        for x, y in product(
            range(x_1 - margin, x_2 + margin), range(y_1 - margin, y_2 + margin)
        ):
            block = self.blocks.get_element((x, y))
            if block is not None:
                self.visibility_buffer.add(block)

        self.update_time(dt)

        player.update(dt, self.blocks, self.characters_buffer.sprites())

        self.characters_buffer.update(dt, self.blocks, [player])

        # update collectibles
        player.pull_collectibles(self.collectibles)
        self.collectibles.update(dt, self.blocks)

        # perform block destruction
        events = pygame.event.get(Player.DESTROY_BLOCK)
        for _ in events:
            self.destroy_block(player, dt)

        # perform block placement
        events = pygame.event.get(Player.PLACE_BLOCK)
        for event in events:
            if isinstance(event.block, BaseBlock):
                self.place_block(player, event.block, dt)

    def update_time(self, dt: float):
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
        return self.blocks.get_element(coords)

    def destroy_block(self, player: BaseCharacter, dt: float):
        coords = player.get_cursor_coords()
        block = self.get_block(coords)
        if block is None:
            return
        destroyed = player.perform_block_destruction(block, dt)
        if not destroyed:
            return
        self.blocks.set_element(coords, None)
        for collectible_class, count in block.collectibles.items():
            collectible_class: type[BaseCollectible]
            for _ in range(count):
                collectible = collectible_class(
                    coords,
                    gravity=int(self.gravity.y),
                    terminal_velocity=self.terminal_velocity,
                )
                self.collectibles.add(collectible)

    def place_block(self, player: BaseCharacter, block: BaseBlock, _: float):
        coords = player.get_cursor_coords()
        self.blocks.set_element(coords, block)


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
        for y in range(int(self.size.y)):
            for x in range(int(self.size.x)):
                if y > (self.size.y / 2):
                    block = make_block(Rock, (x, y))
                    self.blocks.set_element((x, y), block)


class SampleWorld(SimpleWorld):
    def populate(self):
        super().populate()
        x, y = WORLD_SIZE
        x, y = x // 2, y // 2

        # trees
        _y = y
        _x = x - 5
        block = make_block(Tree, (_x, _y))
        self.blocks.set_element((_x, _y), block)
        self.changing_blocks.add(block)

        # spikes
        _y = y + 1
        _x = x + 5
        for i in range(1, 5):
            _x = x + i
            block = make_block(Spike, (_x, _y))
            self.blocks.set_element((_x, _y), block)

        # second level
        _y = y - 2
        for i in range(10):
            _x = x + 10 + i
            block = make_block(Rock, (_x, _y))
            self.blocks.set_element((_x, _y), block)

        # third level
        _y = y - 6
        for i in range(10):
            _x = x + 15 + i
            block = make_block(Rock, (_x, _y))
            self.blocks.set_element((_x, _y), block)

        # slope
        _y = y + 1
        _x = x + 30
        for i in range(10):
            _x += 1
            _y -= 1
            block = make_block(Rock, (_x, _y))
            self.blocks.set_element((_x, _y), block)
