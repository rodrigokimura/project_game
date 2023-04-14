import pygame

from blocks import Rock
from player import Player
from settings import BLOCK_SIZE
from world import World


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

        blocks = []
        for i in range(200):
            block = Rock()
            block.rect.center = (
                int(self.player.position.x + (i - 10) * BLOCK_SIZE),
                int(self.player.position.y + 132),
            )
            blocks.append(block)

        # second level
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(self.player.position.x + i * BLOCK_SIZE + 10 * BLOCK_SIZE),
                int(self.player.position.y + 132 - 3 * BLOCK_SIZE),
            )
            blocks.append(block)

        # third level
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(self.player.position.x + i * BLOCK_SIZE + 15 * BLOCK_SIZE),
                int(self.player.position.y + 132 - 8 * BLOCK_SIZE),
            )
            blocks.append(block)

        # slope
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(self.player.position.x + i * BLOCK_SIZE + 30 * BLOCK_SIZE),
                int(self.player.position.y + 132 - (i + 1) * BLOCK_SIZE),
            )
            blocks.append(block)

        # wall
        for i in range(10):
            block = Rock()
            block.rect.center = (
                int(self.player.position.x - 5 * BLOCK_SIZE),
                int(self.player.position.y + 132 - (i + 1) * BLOCK_SIZE),
            )
            blocks.append(block)

        self.collision_sprites.add(*blocks)
        self.all_sprites.add(*blocks)

        self.player.collidable_sprites_buffer = self.collision_sprites

    def run(self, dt):
        # self.display_surface.fill("black")
        self.display_surface.fill("gray")
        self.all_sprites.draw(self.display_surface)
        self.all_sprites.update(dt)
