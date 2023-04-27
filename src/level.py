from typing import Optional

import pygame

from blocks import draw_cached_images
from camera import Camera
from interface import Menu, PlayerMode, PlayerStats, TimeDisplay
from player import BasePlayer, Player
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
    FINISHED = pygame.event.custom_type()
    RESUME = pygame.event.custom_type()
    SAVE = pygame.event.custom_type()

    EVENTS = [FINISHED, RESUME, SAVE]

    @classmethod
    def from_storage(cls):
        world = WorldStorage().get_newest()
        player = PlayerStorage().get_newest()
        return cls(world, player)

    def __init__(
        self, world: Optional[BaseWorld] = None, player: Optional[BasePlayer] = None
    ) -> None:
        draw_cached_images()
        self.paused = False
        self.display_surface = pygame.display.get_surface()
        self.all_sprites = pygame.sprite.Group()
        self.setup(world, player)

        pause_menu = {
            "resume": self.RESUME,
            "save game": self.SAVE,
            "exit": self.FINISHED,
        }
        self.pause_menu = Menu(pause_menu)

    def setup(self, world: Optional[BaseWorld], player: Optional[BasePlayer]):
        self.player = player or Player(
            GRAVITY,
            TERMINAL_VELOCITY,
            (WORLD_SIZE[0] * BLOCK_SIZE // 2, WORLD_SIZE[1] * BLOCK_SIZE // 2),
            self.all_sprites,
        )
        self.world = world or SampleWorld(WORLD_SIZE, GRAVITY, TERMINAL_VELOCITY)
        self.player.collidable_sprites_buffer = self.world.collision_buffer

        interface = [
            PlayerStats(self.player),
            PlayerMode(self.player),
            TimeDisplay(self.world),
        ]

        self.camera = Camera(
            (SCREEN_WIDTH, SCREEN_HEIGHT), self.player, self.world, interface
        )

    def run(self, dt: float):
        visibility_rect = self.camera.get_rect()

        if self.paused:
            self.pause_menu.run()
            self.handle_menu_commands()
        else:
            self.world.update(dt, visibility_rect, self.player)
            self.camera.update()
            self.check_player_dead()
        self.check_pause_menu()

    def handle_menu_commands(self):
        events = pygame.event.get(self.SAVE)
        if events:
            ev = events[0]
            if ev.type == self.SAVE:
                self.save_game()

    def save_game(self):
        WorldStorage().store(self.world)
        PlayerStorage().store(self.player)

    def check_player_dead(self):
        events = pygame.event.get(Player.DEAD)
        if events:
            pygame.event.post(pygame.event.Event(self.FINISHED))

    def check_pause_menu(self):
        events = pygame.event.get(Player.PAUSE)
        if events:
            self.paused = True
        events = pygame.event.get(self.RESUME)
        if events:
            self.paused = False
