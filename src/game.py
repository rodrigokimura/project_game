import pygame

import settings
from interface import Menu
from level import Level
from player import Player


class Game:
    NEW_GAME = pygame.event.custom_type()
    LOAD_GAME = pygame.event.custom_type()
    EXIT = pygame.QUIT

    def __init__(self) -> None:
        pass

    def setup(self):
        pygame.init()
        pygame.joystick.init()
        pygame.display.set_caption(settings.TITLE)
        size = [settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT]
        flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        if settings.DEBUG:
            self.screen = pygame.display.set_mode(size)  # no fullscreen
        else:
            self.screen = pygame.display.set_mode(size, flags)
        self.clock = pygame.time.Clock()
        self.internal_events = []

    def run(self):
        self.setup()
        start_menu = {
            "new game": self.NEW_GAME,
            "load game": self.LOAD_GAME,
            "settings": self.NEW_GAME,
            "exit": self.EXIT,
        }
        self.menu = Menu(start_menu)

        self.main_loop = self.load_menu

        running = True
        while running:
            for event in pygame.event.get(exclude=self.internal_events):
                if event.type == pygame.QUIT:
                    running = False

                if event.type == Level.FINISHED:
                    self.main_loop = self.load_menu

                if event.type == self.NEW_GAME:
                    self.level = Level()
                    self.internal_events = Player.EVENTS
                    self.main_loop = self.run_level

                if event.type == self.LOAD_GAME:
                    self.level = Level.from_storage()
                    self.internal_events = Player.EVENTS
                    self.main_loop = self.run_level

            dt = self.clock.tick(100) / 1000

            self.main_loop(dt)

            # pygame.display.flip()
            pygame.display.update()

        pygame.quit()

    def load_menu(self, dt):
        self.menu.run()

    def run_level(self, dt):
        self.level.run(dt)
