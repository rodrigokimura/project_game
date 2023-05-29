from typing import Any

import pygame

from commons import Damageable
from protocols import HasRect
from settings import BLOCK_SIZE
from utils.collision import custom_collision_detection
from utils.container import Container2d


class BaseBullet(pygame.sprite.Sprite):
    def __init__(
        self,
        source: Any,
        position: pygame.math.Vector2,
        velocity: pygame.math.Vector2,
    ) -> None:
        self.size = (3, 3)
        self.source = source
        self.initial_position = position
        self.position = self.initial_position.copy()
        self.rect = pygame.rect.Rect(0, 0, *self.size)
        self.velocity = velocity
        self.max_range = 500
        self.damage = 10
        self.shatter_on_collision = True
        self.setup()
        super().__init__()

    def setup(self):
        ...

    @property
    def image(self):
        return bullet_images[self.__class__]

    def update(self, dt: float):
        self.position += self.velocity * dt
        self.rect.center = (int(self.position.x), int(self.position.y))
        if (self.position - self.initial_position).length() > self.max_range:
            self.kill()

    def check_collision(
        self,
        blocks: Container2d[HasRect],
        characters: pygame.sprite.Group,
    ):
        for block in blocks.get_surrounding(
            (int(self.position.x // BLOCK_SIZE), int(self.position.y // BLOCK_SIZE)), 1
        ):
            if block is not None:
                if block.rect.colliderect(self.rect):
                    self.kill()

        collided_sprites = pygame.sprite.spritecollide(
            self,
            characters,
            False,
            collided=custom_collision_detection,
        )
        for character in collided_sprites:
            character: Damageable
            character.take_damage(self)
            if self.shatter_on_collision:
                self.kill()


class Bullet(BaseBullet):
    ...


bullet_images: dict[type[BaseBullet], pygame.surface.Surface] = {
    Bullet: pygame.surface.Surface((3, 3)),
}


def load_bullet_images():
    img = bullet_images[Bullet]
    pygame.draw.rect(img, "red", img.get_rect(), 2)
