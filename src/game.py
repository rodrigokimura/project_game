import pygame

import settings
from interface import Menu
from level import Level
from player import Player


class Game:
    NEW_GAME = pygame.event.custom_type()
    EXIT = pygame.QUIT

    def __init__(self) -> None:
        pass

    def setup(self):
        pygame.init()
        pygame.joystick.init()
        pygame.display.set_caption(settings.TITLE)
        size = [settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT]
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.internal_events = []

    def run(self):
        self.setup()
        start_menu = {
            "new game": self.NEW_GAME,
            "load game": self.NEW_GAME,
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
                    print("Game Over")
                    running = False

                if event.type == self.NEW_GAME:
                    self.level = Level()
                    self.internal_events = Player.EVENTS
                    self.main_loop = self.new_game

            dt = self.clock.tick(100) / 1000

            self.main_loop(dt)

            pygame.display.flip()

        pygame.quit()

    def load_menu(self, dt):
        self.menu.run()

    def new_game(self, dt):
        self.level.run(dt)
