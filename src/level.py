import pygame

from player import Player
from world import Ground, World


class Level:
    def __init__(self) -> None:
        self.display_surface = pygame.display.get_surface()
        self.all_sprites = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group()
        self.setup()

    def setup(self):
        joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        joystick = joysticks[0] if joysticks else None
        self.world = World()
        self.player = Player(self.world, None, joystick, self.all_sprites)
        self.ground = Ground((self.player.pos.x, self.player.pos.y + 100))

        self.all_sprites.add(self.ground)
        self.collision_sprites.add(self.ground)

        self.player.collidable_sprites_buffer = self.collision_sprites

    def run(self, dt):
        self.display_surface.fill("black")
        self.all_sprites.draw(self.display_surface)
        self.all_sprites.update(dt)
