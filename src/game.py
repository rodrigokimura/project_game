import pygame

import settings
from level import Level
from player import Player


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()
        pygame.display.set_caption(settings.TITLE)
        size = [settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT]
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.level = Level()
        self.internal_events = Player.EVENTS

    def run(self):
        running = True

        while running:
            dt = self.clock.tick(100) / 1000

            for event in pygame.event.get(exclude=self.internal_events):
                if event.type == pygame.QUIT:
                    running = False
                if event.type == Level.FINISHED:
                    print("Game Over")
                    running = False

            self.level.run(dt)
            pygame.display.update()

        pygame.quit()
