from typing import Callable

import moderngl as mgl
import pygame
import pygame._sdl2.controller

import settings
from characters import Player
from input.constants import Controller
from interface import ControllerDetection, Menu
from level import Level
from utils.open_gl import set_gl_attrs

# pylint: disable=no-member


class Game:
    NEW_GAME = pygame.event.custom_type()
    LOAD_GAME = pygame.event.custom_type()
    EXIT = pygame.QUIT

    controller: Controller
    main_loop: Callable
    level: Level
    internal_events: list[int]
    clock: pygame.time.Clock
    controller_detection: ControllerDetection
    menu: Menu

    def run(self):
        print(f"Pygame version: {pygame.version.ver}")
        self.setup()

        running = True
        while running:
            for event in pygame.event.get(exclude=self.internal_events):
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == Level.FINISHED:
                    self.main_loop = self.run_menu

                elif event.type == self.NEW_GAME:
                    self.level = Level(self.ctx, self.controller)
                    self.internal_events = Player.EVENTS
                    self.main_loop = self.run_level

                elif event.type == self.LOAD_GAME:
                    self.level = Level.from_storage(self.ctx, self.controller)
                    self.internal_events = Player.EVENTS
                    self.main_loop = self.run_level

                elif event.type == ControllerDetection.CONTROLLER_DETECTED:
                    self.controller = event.controller
                    self.menu.set_controller(self.controller)

                    self.main_loop = self.run_menu

            dt = self.clock.tick() / 1000
            pygame.display.set_caption(f"{self.clock.get_fps():.0f}")

            self.main_loop(dt)

            pygame.display.flip()

        pygame.quit()

    def setup(self):
        pygame.init()
        pygame._sdl2.controller.init()  # pylint: disable=protected-access
        set_gl_attrs()

        pygame.display.set_caption(settings.TITLE)
        size = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        flags = pygame.DOUBLEBUF | pygame.OPENGL

        # if not settings.DEBUG:
        #     flags |= pygame.FULLSCREEN

        pygame.display.set_mode(size, flags, vsync=1)

        self.ctx = mgl.create_context()
        self.ctx.gc_mode = "auto"

        self.clock = pygame.time.Clock()
        self.internal_events = []

        self.menu = Menu(
            {
                "new game": self.NEW_GAME,
                "load game": self.LOAD_GAME,
                "settings": self.NEW_GAME,
                "exit": self.EXIT,
            },
            self.ctx,
        )
        self.controller_detection = ControllerDetection(self.ctx)

        self.main_loop = self.run_controller_detection

    def run_controller_detection(self, dt: float):
        self.controller_detection.run(dt)

    def run_menu(self, dt: float):
        self.menu.run(dt)

    def run_level(self, dt: float):
        self.level.run(dt)
