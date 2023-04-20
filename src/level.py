import pygame

from interface import Camera, PlayerStats
from player import Player
from settings import GRAVITY, SCREEN_HEIGHT, SCREEN_WIDTH, TERMINAL_VELOCITY, WORLD_SIZE
from world import SimpleWorld


class Level:
    FINISHED = pygame.event.custom_type()
    EVENTS = [FINISHED]

    def __init__(self) -> None:
        self.display_surface = pygame.display.get_surface()
        self.all_sprites = pygame.sprite.Group()
        self.setup()

    def setup(self):
        joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        joystick = joysticks[0] if joysticks else None
        self.player = Player(
            GRAVITY, TERMINAL_VELOCITY, None, joystick, self.all_sprites
        )
        self.world = SimpleWorld(WORLD_SIZE, GRAVITY, TERMINAL_VELOCITY, self.player)
        interface = [PlayerStats(self.player)]
        self.camera = Camera(
            (SCREEN_WIDTH, SCREEN_HEIGHT), self.player, self.world, interface
        )

    def run(self, dt):
        visibility_rect = self.camera.get_rect()

        self.world.update(dt, visibility_rect)
        self.camera.update()
        self.check_player_dead()

    def check_player_dead(self):
        events = pygame.event.get(Player.DEAD)
        if events:
            pygame.event.post(pygame.event.Event(self.FINISHED))
