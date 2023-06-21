from __future__ import annotations

from collections.abc import Callable

import pygame
import pygame.freetype

from background import Background, Mountains
from blocks import BaseBlock, BaseCollectible, Rock, Spike, Tree, make_block
from characters import BaseCharacter, Player
from colors import InterfaceColor
from commons import Loadable, Storable
from day_cycle import convert_to_time, get_day_part
from draw import BorderOptions, FillBorderColors, draw_bordered_rect
from lighting import ShadowCaster
from log import log
from particle.emitters import Manager
from settings import BLOCK_SIZE, DAY_DURATION, DEBUG, MENU_FONT, WORLD_SIZE
from shooting import BaseBullet
from utils.container import Container2d


class Loader:
    LOADED = pygame.event.custom_type()

    def __init__(self, world: World, shadow_caster: ShadowCaster) -> None:
        self.world = world
        self._font = pygame.freetype.Font(MENU_FONT, 50)
        self._font.antialiased = False
        self._font.pad = True
        self.display = pygame.display.get_surface()

        self._step_progress = 0
        self._steps = [
            ("Indexing surface outer layer", self._step_1),
            ("Generating opacity info", self._step_2),
        ]
        self.shadow_caster = shadow_caster

    def load(self):
        self.shadow_caster.setup()
        self._draw_static()
        self._load_world()
        self._finish()

    def _draw_static(self):
        self.display.fill(InterfaceColor.MENU_BACKGROUND)
        pygame.display.update()

    def _load_world(self):
        for _, step in enumerate(self._steps):
            _, step = step
            self._step_progress = 0
            step()

    def _step_1(self):
        self.shadow_caster._detect_outer_layer(
            lambda x: self._update_progress_and_message(x, 0, self._steps[0][0])
        )

    def _step_2(self):
        self.shadow_caster._generate_opacity_info(
            lambda x: self._update_progress_and_message(x, 1, self._steps[1][0])
        )

    def _update_progress_and_message(
        self, step_progress: float, step_index: int, message: str
    ):
        progress_per_step = 1 / len(self._steps)
        progress = step_progress * progress_per_step + (step_index * progress_per_step)
        rect = self._font.render_to(
            self.display,
            (0, 0),
            message,
            InterfaceColor.PRIMARY_FONT,
            InterfaceColor.MENU_BACKGROUND,
        )
        pygame.display.update(rect)

        text = f"Progress: {progress:.0%}"
        rect = self._font.render_to(
            self.display,
            (0, 50),
            text,
            InterfaceColor.PRIMARY_FONT,
            InterfaceColor.MENU_BACKGROUND,
        )
        pygame.display.update(rect)
        progress_bar_rect = pygame.rect.Rect((0, 120), (1000, 20))
        progress_bar_fill_rect = pygame.rect.Rect(
            (0, 120), (progress_bar_rect.width * progress, 20)
        )
        draw_bordered_rect(
            self.display,
            progress_bar_rect,
            FillBorderColors(InterfaceColor.MENU_BACKGROUND, InterfaceColor.BORDER),
            BorderOptions(1, 0),
        )
        draw_bordered_rect(
            self.display,
            progress_bar_fill_rect,
            FillBorderColors(InterfaceColor.HEALTH_POINTS, InterfaceColor.BORDER),
            BorderOptions(1, 0),
        )
        pygame.display.update(progress_bar_rect)

    def _finish(self):
        event = pygame.event.Event(self.LOADED)
        pygame.event.post(event)


class World(Storable, Loadable):
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
        self.age = 0  # in seconds
        self.time_of_day = 0  # cycling counter
        self.player: Player | None = None
        self.event_handlers: dict[int, Callable[[pygame.event.Event, float], None]] = {
            Player.DESTROY_BLOCK: self._handle_block_destruction,
            Player.PLACE_BLOCK: self._handle_block_placement,
            Player.SHOOT: self._handle_shooting,
        }
        self._background: Background | None = None
        self.particle_manager = Manager()
        self._global_light = ...
        self.setup()

    def set_player(self, player: Player):
        self.player = player
        self.players.add(player)
        # Emitter(self.player.position, None, 5, self.particle_manager)

    def setup(self):
        self.blocks: Container2d[BaseBlock] = Container2d(WORLD_SIZE)
        self.changing_blocks = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.collision_buffer = pygame.sprite.Group()
        self.characters_buffer: pygame.sprite.Group[
            BaseCharacter  # type: ignore
        ] = pygame.sprite.Group()
        self.bullets: pygame.sprite.Group[
            BaseBullet  # type: ignore
        ] = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self._background = Mountains()
        populate_world(self)

    def unload(self):
        self.blocks.empty()
        self.changing_blocks.empty()
        self.collectibles.empty()
        self.collision_buffer.empty()
        self.characters_buffer.empty()
        self.players.empty()
        self.bullets.empty()
        self.player = None

    def update(self, dt: float):
        self._update_time(dt)
        self._update_sprites(dt)
        self._handle_events(dt)
        self.particle_manager.update(dt)

    def _update_time(self, dt: float):
        self.age += dt
        self.time_of_day += dt
        if self.time_of_day >= self.DAY_DURATION:
            self.time_of_day = 0
            self.changing_blocks.update(dt)
            if DEBUG:
                log("Updating ChangingBlock instances")

    def _update_sprites(self, dt: float):
        if self.player is None:
            raise self.UnloadedObject

        self.players.update(dt)
        self.characters_buffer.update(dt)

        self.player.pull_collectibles(self.collectibles)
        self.collectibles.update(dt)
        self.bullets.update(dt)

    def _handle_events(self, dt: float):
        for event in pygame.event.get(list(self.event_handlers.keys())):
            try:
                self.event_handlers[event.type](event, dt)
            except KeyError as err:
                raise NotImplementedError("Missing event handler") from err

    @property
    def relative_time(self):
        return self.time_of_day / self.DAY_DURATION

    @property
    def time(self):
        return convert_to_time(self.relative_time)

    @property
    def day_part(self):
        return get_day_part(self.time)

    @property
    def background(self):
        if self._background is None:
            raise self.UnloadedObject
        return self._background

    def get_block(self, coords: tuple[int, int]):
        return self.blocks.get_element(coords)

    def _handle_block_destruction(self, event: pygame.event.Event, dt: float):
        if self.player is None:
            raise self.UnloadedObject

        coords = event.coords
        block = self.get_block(coords)
        if block is None:
            return
        block.integrity -= event.power * dt
        if block.integrity <= 0:
            self.blocks.set_element(coords, None)
            for collectible_class, count in block.collectibles.items():
                collectible_class: type[BaseCollectible]
                for _ in range(count):
                    collectible = collectible_class(
                        coords,
                        gravity=int(self.gravity.y),
                        terminal_velocity=self.terminal_velocity,
                        blocks=self.blocks,
                    )
                    self.collectibles.add(collectible)

    def _handle_block_placement(self, event: pygame.event.Event, _: float):
        if self.player is None:
            raise self.UnloadedObject
        if not isinstance(event.block, BaseBlock):
            return
        self.blocks.set_element(self.player.get_cursor_coords(), event.block)

    def _handle_shooting(self, event: pygame.event.Event, _: float):
        bullet: BaseBullet = event.bullet
        bullet.add_world_context(
            self.blocks, self.characters_buffer, self.particle_manager  # type: ignore
        )
        self.bullets.add(bullet)


def populate_world(world: World):
    for y in range(int(world.size.y)):
        for x in range(int(world.size.x)):
            if y > (world.size.y / 2):
                block = make_block(Rock, (x, y))
                world.blocks.set_element((x, y), block)
    x, y = WORLD_SIZE
    x, y = x // 2, y // 2

    # cave
    _y = y + 1
    for i in range(5):
        _x = x - i - 20
        world.blocks.set_element((_x, _y), None)
    _y = y + 2
    for i in range(4):
        _x = x - i - 21
        world.blocks.set_element((_x, _y), None)
    _y = y + 3
    for i in range(3):
        _x = x - i - 22
        world.blocks.set_element((_x, _y), None)
    _y = y + 4
    for i in range(5):
        _x = x - i - 22
        world.blocks.set_element((_x, _y), None)
    _y = y + 5
    for i in range(6):
        _x = x - i - 22
        world.blocks.set_element((_x, _y), None)
    _y = y + 6
    for i in range(10):
        _x = x - i - 23
        world.blocks.set_element((_x, _y), None)
    _y = y + 7
    for i in range(10):
        _x = x - i - 23
        world.blocks.set_element((_x, _y), None)
    _y = y + 8
    for i in range(10):
        _x = x - i - 25
        world.blocks.set_element((_x, _y), None)

    # trees
    _y = y
    _x = x - 5
    block = make_block(Tree, (_x, _y))
    world.blocks.set_element((_x, _y), block)
    world.changing_blocks.add(block)

    # spikes
    _y = y + 1
    _x = x + 5
    for i in range(1, 5):
        _x = x + i
        block = make_block(Spike, (_x, _y))
        world.blocks.set_element((_x, _y), block)

    # second level
    _y = y - 2
    for i in range(10):
        _x = x + 10 + i
        block = make_block(Rock, (_x, _y))
        world.blocks.set_element((_x, _y), block)

    # third level
    _y = y - 6
    for i in range(10):
        _x = x + 15 + i
        block = make_block(Rock, (_x, _y))
        world.blocks.set_element((_x, _y), block)

    # slope
    _y = y + 1
    _x = x + 30
    for i in range(10):
        _x += 1
        _y -= 1
        block = make_block(Rock, (_x, _y))
        world.blocks.set_element((_x, _y), block)
