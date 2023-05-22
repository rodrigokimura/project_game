import pygame

import settings
from input.constants import Controller
from input.controllers import JoystickMenuController, KeyboardMenuController
from interface import ControllerDetection, Menu
from level import Level
from player import Player


class Game:
    NEW_GAME = pygame.event.custom_type()
    LOAD_GAME = pygame.event.custom_type()
    EXIT = pygame.QUIT
    controller: Controller

    def run(self):
        self.setup()

        running = True
        while running:
            for event in pygame.event.get(exclude=self.internal_events):
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == Level.FINISHED:
                    self.main_loop = self.run_menu

                elif event.type == self.NEW_GAME:
                    self.level = Level(self.controller)
                    self.internal_events = Player.EVENTS
                    self.main_loop = self.run_level

                elif event.type == self.LOAD_GAME:
                    self.level = Level.from_storage(self.controller)
                    self.internal_events = Player.EVENTS
                    self.main_loop = self.run_level

                elif event.type == ControllerDetection.CONTROLLER_DETECTED:
                    self.controller = event.controller
                    if self.controller == Controller.JOYSTICK:
                        self.menu.controller = JoystickMenuController(self.menu)
                    elif self.controller == Controller.KEYBOARD:
                        self.menu.controller = KeyboardMenuController(self.menu)

                    self.main_loop = self.run_menu

            dt = self.clock.tick() / 1000

            self.main_loop(dt)

            pygame.display.update()

        pygame.quit()

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

        self.menu = Menu(
            {
                "new game": self.NEW_GAME,
                "load game": self.LOAD_GAME,
                "settings": self.NEW_GAME,
                "exit": self.EXIT,
            }
        )
        self.controller_detection_screen = ControllerDetection()

        self.main_loop = self.run_controller_detection

    def run_controller_detection(self, dt: float):
        self.controller_detection_screen.run(dt)

    def run_menu(self, dt: float):
        self.menu.run(dt)

    def run_level(self, dt: float):
        self.level.run(dt)
