import enum
from typing import Optional

import pygame

from blocks import draw_cached_images
from camera import Camera
from characters import Enemy, Player
from input.constants import Controller
from interface import Menu, PlayerMode, PlayerStats, TimeDisplay
from inventory import Inventory
from settings import (
    BLOCK_SIZE,
    GRAVITY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TERMINAL_VELOCITY,
    WORLD_SIZE,
)
from storage import PlayerStorage, WorldStorage
from world import BaseWorld, SampleWorld


class Level:
    class Status(enum.IntEnum):
        RUNNING = enum.auto()
        PAUSED = enum.auto()
        INVENTORY_OPEN = enum.auto()

    FINISHED = pygame.event.custom_type()
    RESUME = pygame.event.custom_type()
    SAVE = pygame.event.custom_type()

    EVENTS = [FINISHED, RESUME, SAVE]

    @classmethod
    def from_storage(cls, controller: Controller):
        world = WorldStorage().get_newest()
        player = PlayerStorage().get_newest()
        return cls(controller, world, player)

    def __init__(
        self,
        controller: Controller,
        world: Optional[BaseWorld] = None,
        player: Optional[Player] = None,
    ) -> None:
        draw_cached_images()
        self.status = Level.Status.RUNNING
        self.display_surface = pygame.display.get_surface()
        self.pause_menu = Menu(
            {
                "resume": self.RESUME,
                "save game": self.SAVE,
                "exit": self.FINISHED,
            }
        )
        self.pause_menu.set_controller(controller)
        self.setup(controller, world, player)

    def setup(
        self,
        controller: Controller,
        world: Optional[BaseWorld],
        player: Optional[Player],
    ):
        self.player = player or Player(
            GRAVITY,
            TERMINAL_VELOCITY,
            ((WORLD_SIZE[0] - 20) * BLOCK_SIZE // 2, WORLD_SIZE[1] * BLOCK_SIZE // 2),
        )
        self.player.set_controller(controller)
        self.world = world or SampleWorld(WORLD_SIZE, GRAVITY, TERMINAL_VELOCITY)
        self.world.set_player(self.player)
        if world:
            self.world.populate()

        enemy = Enemy(
            GRAVITY,
            TERMINAL_VELOCITY,
            ((WORLD_SIZE[0] - 100) * BLOCK_SIZE // 2, WORLD_SIZE[1] * BLOCK_SIZE // 2),
        )
        enemy.set_controller(Controller.AI)
        self.world.characters_buffer.add(enemy)

        self.camera = Camera(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            self.player,
            self.world,
            [
                PlayerStats(self.player),
                PlayerMode(self.player),
                TimeDisplay(self.world),
            ],
            self.world.characters_buffer.sprites(),
        )

    def run(self, dt: float):
        if self.status == Level.Status.RUNNING:
            self.world.update(dt)
            self.camera.update()
            self.check_player_dead()
        elif self.status == Level.Status.PAUSED:
            self.pause_menu.run(dt)
            self.handle_menu_commands()
        elif self.status == Level.Status.INVENTORY_OPEN:
            self.player.inventory.update(dt)

        self.check_status()

    def handle_menu_commands(self):
        events = pygame.event.get(self.SAVE)
        if events:
            event = events[0]
            if event.type == self.SAVE:
                self.save_game()

    def save_game(self):
        WorldStorage().store(self.world)
        PlayerStorage().store(self.player)

    def check_player_dead(self):
        for event in pygame.event.get(Player.DEAD):
            if not isinstance(event.character, Enemy):
                pygame.event.post(pygame.event.Event(self.FINISHED))
            else:
                event.character.kill()

    def check_status(self):
        if self.status == Level.Status.PAUSED:
            if pygame.event.get(self.RESUME):
                self.status = Level.Status.RUNNING
        elif self.status == Level.Status.RUNNING:
            events = pygame.event.get((Player.PAUSE, Player.OPEN_INVENTORY))
            if events:
                event = events[0]
                if event.type == Player.PAUSE:
                    self.status = Level.Status.PAUSED
                elif event.type == Player.OPEN_INVENTORY:
                    self.status = Level.Status.INVENTORY_OPEN
        elif self.status == Level.Status.INVENTORY_OPEN:
            if pygame.event.get(Inventory.CLOSE):
                self.status = Level.Status.RUNNING
