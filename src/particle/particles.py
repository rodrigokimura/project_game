from random import randint

import pygame

from colors import Color


class Particle(pygame.sprite.Sprite):
    def __init__(
        self,
        start_position: pygame.math.Vector2,
        color: Color,
        size: tuple[int, int],
        speed: int,
        max_travel: int,
    ) -> None:
        super().__init__()
        self._start_position = start_position

        self.image = pygame.surface.Surface(size).convert_alpha()
        self.rect = self.image.get_rect().move(start_position)
        self.image.fill(color)
        self._max_travel = max_travel
        self.velocity = pygame.math.Vector2.from_polar((speed, randint(0, 360)))

    def update(self, dt: float):
        if self.velocity is None:
            return
        self.rect.move_ip(self.velocity * dt)
        travel = (pygame.math.Vector2(self.rect.center) - self._start_position).length()
        if travel >= self._max_travel:
            self.kill()
