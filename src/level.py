import pygame

from interface import Camera, Menu, PlayerStats
from player import Player
from settings import (
    BLOCK_SIZE,
    GRAVITY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TERMINAL_VELOCITY,
    WORLD_SIZE,
)
from world import SampleWorld


class Level:
    FINISHED = pygame.event.custom_type()
    RESUME = pygame.event.custom_type()
    EVENTS = [FINISHED, RESUME]

    def __init__(self) -> None:
        self.paused = False
        self.display_surface = pygame.display.get_surface()
        self.all_sprites = pygame.sprite.Group()
        self.setup()

        pause_menu = {
            "resume": self.RESUME,
            # "save game": self.FINISHED,
            # "load game": self.FINISHED,
            "exit": self.FINISHED,
        }
        self.pause_menu = Menu(pause_menu)

    def setup(self):
        joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        joystick = joysticks[0] if joysticks else None
        self.player = Player(
            GRAVITY,
            TERMINAL_VELOCITY,
            (WORLD_SIZE[0] * BLOCK_SIZE // 2, WORLD_SIZE[1] * BLOCK_SIZE // 2),
            joystick,
            self.all_sprites,
        )
        self.world = SampleWorld(WORLD_SIZE, GRAVITY, TERMINAL_VELOCITY, self.player)

        interface = [PlayerStats(self.player)]
        self.camera = Camera(
            (SCREEN_WIDTH, SCREEN_HEIGHT), self.player, self.world, interface
        )

    def run(self, dt):
        visibility_rect = self.camera.get_rect()

        if self.paused:
            self.pause_menu.run()
        else:
            self.world.update(dt, visibility_rect)
            self.camera.update()
            self.check_player_dead()
        self.check_pause_menu()

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
