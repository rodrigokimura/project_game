import math
from typing import Any, Optional

import pygame


class Player(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: Optional[tuple[int, int]],
        joystick: Optional[pygame.joystick.JoystickType],
        *groups: pygame.sprite.Group
    ) -> None:
        super().__init__(*groups)

        self.joystick = joystick
        if self.joystick is not None:
            self.joystick.init()

        self.pos = pos or pygame.display.get_surface().get_rect().center
        self.angle = 0
        self.size = 32

        self._draw()

        self.rect = self.image.get_rect(center=self.pos)
        self.direction = pygame.Vector2()
        self.speed = 200
        self.angular_speed = self.speed / self.size / 2 * math.pi

    def _draw(self):
        size = self.size
        sq_size = size // 2
        self.image = pygame.surface.Surface((size, size))
        pygame.draw.circle(
            self.image, "green", self.image.get_rect().center, size // 2, width=1
        )
        rect = pygame.Rect(
            (size - sq_size) // 2, (size - sq_size) // 2, sq_size, sq_size
        )
        pygame.draw.rect(self.image, "red", rect, 0)
        self.original_image = self.image.copy()

    def input(self, dt):
        if self.joystick is not None:
            d_pad = self.joystick.get_hat(0)
            self.direction = pygame.Vector2(d_pad)
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                self.direction.y = -1
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
            else:
                self.direction.y = 0

            if keys[pygame.K_LEFT]:
                self.direction.x = -1
            elif keys[pygame.K_RIGHT]:
                self.direction.x = 1
            else:
                self.direction.x = 0

        self.move(dt)

    def move(self, dt):
        if self.direction != (0, 0):
            self.direction = self.direction.normalize()
            self.pos += self.direction * self.speed * dt
            self.rect.center = self.pos
            if self.direction.x:
                self.angle += (1 if self.direction.x < 0 else -1) * self.angular_speed

    def update(self, dt, *args: Any, **kwargs: Any) -> None:
        self.input(dt)

        img = self.rotate()
        rect = self.image.blit(
            img,
            self.original_image.get_rect(),
        )
        self.image = img.subsurface(rect)
        return super().update(*args, **kwargs)

    def rotate(self):
        img = pygame.Surface(self.original_image.get_size())
        img = pygame.transform.rotate(self.original_image, self.angle)
        new_x, new_y = img.get_size()
        new_x = new_x - self.original_image.get_size()[0]
        new_y = new_y - self.original_image.get_size()[1]

        img.scroll(
            -int(new_x / 2),
            -int(new_y / 2),
        )
        return img
