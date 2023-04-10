import pygame

from player import Player


class Level:
    def __init__(self) -> None:
        self.display_surface = pygame.display.get_surface()
        self.all_sprites = pygame.sprite.Group()
        self.setup()

    def setup(self):
        joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        joystick = joysticks[0] if joysticks else None
        self.player = Player(None, joystick, self.all_sprites)

    def run(self, dt):
        self.display_surface.fill("black")
        self.all_sprites.draw(self.display_surface)
        self.all_sprites.update(dt)
