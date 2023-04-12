import pygame

import settings
from level import Level


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()
        pygame.display.set_caption(settings.TITLE)
        size = [settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT]
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.level = Level()

    def run(self):
        running = True

        while running:
            dt = self.clock.tick(100) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.level.run(dt)
            pygame.display.update()

        pygame.quit()
