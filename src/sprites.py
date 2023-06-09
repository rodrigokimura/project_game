from abc import ABC, abstractmethod

import pygame


class GravitySprite(ABC, pygame.sprite.Sprite):
    def __init__(
        self, gravity: int, terminal_velocity: int, *groups: pygame.sprite.Group
    ) -> None:
        super().__init__(*groups)
        self.collidable_sprites_buffer = pygame.sprite.Group()

        self.pos = pygame.math.Vector2()
        self.rect = pygame.rect.Rect(0, 0, 0, 0)
        self.velocity = pygame.math.Vector2()
        self.acceleration = pygame.math.Vector2(0, gravity)
        self.terminal_velocity = terminal_velocity

    def update(self, dt: float) -> None:
        self.fall(dt)

    def fall(self, dt: float):
        if self.should_fall():
            self.velocity.y += self.acceleration.y * dt
            if abs(self.velocity.y) > self.terminal_velocity:
                self.velocity.y = self.terminal_velocity * (
                    1 if self.velocity.y > 0 else -1
                )

    @abstractmethod
    def should_fall(self) -> bool:
        ...
