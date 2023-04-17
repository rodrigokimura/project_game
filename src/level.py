import pygame

from blocks import Rock
from player import Player
from settings import BLOCK_SIZE, GRAVITY, SCREEN_HEIGHT, SCREEN_WIDTH, WORLD_SIZE
from world import World


class Camera:
    def __init__(self, size: tuple[int, int], player: Player, world: World) -> None:
        self.width, self.height = size
        self.player = player
        self.world = world

    def get_rect(self):
        rect = pygame.rect.Rect(0, 0, self.width, self.height)
        rect.center = self.player.rect.center

        top = self.player.rect.centery - self.height / 2
        if top <= 0:
            rect.top = 0

        bottom = self.player.rect.centery + self.height / 2
        if bottom >= self.world.surface.get_rect().height:
            rect.bottom = self.world.surface.get_rect().height

        left = self.player.rect.centerx - self.width / 2
        if left < 0:
            rect.left = 0

        right = self.player.rect.centerx + self.width / 2
        if right >= self.world.surface.get_rect().width:
            rect.right = self.world.surface.get_rect().width

        return rect


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
        self.world = World(WORLD_SIZE, GRAVITY)
        self.player = Player(self.world, None, joystick, self.all_sprites)
        self.camera = Camera((SCREEN_WIDTH, SCREEN_HEIGHT), self.player, self.world)

        blocks = []
        for i in range(190):
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
        self.world.surface.fill("black")

        self.all_sprites.draw(self.world.surface)
        self.all_sprites.update(dt)

        self.display_surface.blit(self.world.surface, (0, 0), self.camera.get_rect())
