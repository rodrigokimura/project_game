import pygame

from settings import BLOCK_SIZE


class BaseBlock(pygame.sprite.Sprite):
    def __init__(self, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.image = pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE))
        self.rect = self.image.get_rect()
        pygame.draw.rect(self.image, "red", self.image.get_rect(), 1)


class Rock(BaseBlock):
    pass
