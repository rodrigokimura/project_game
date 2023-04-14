import math
from typing import Any, Optional

import pygame

from settings import BLOCK_SIZE, DEBUG
from world import GravitySprite, World


class Player(GravitySprite):
    def __init__(
        self,
        world: World,
        pos: Optional[tuple[int, int]],
        joystick: Optional[pygame.joystick.JoystickType],
        *groups: pygame.sprite.Group
    ) -> None:
        super().__init__(world, *groups)

        self.joystick = joystick
        if self.joystick is not None:
            self.joystick.init()

        pos = pos or pygame.display.get_surface().get_rect().center
        self.pos = pygame.math.Vector2(*pos)
        self.angle = 0
        self.size = 2 * BLOCK_SIZE

        self._draw()

        self.rect = self.image.get_rect(center=self.pos)
        self.speed = 200
        self.angular_speed = self.speed / self.size / 2 * math.pi
        self.bottom_rect = pygame.rect.Rect(
            self.pos.x - 1, self.pos.y + self.size / 2, 2, 1
        )

        self.jump_increment = 400

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

    def update(self, dt, *args: Any, **kwargs: Any) -> None:
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.bottom_rect.left = int(self.pos.x - 1)
        self.bottom_rect.top = int(self.pos.y + self.size / 2)

        self.input(dt)
        self.move(dt)
        self.check_collisions()

        super().update(dt, *args, **kwargs)

        img = self.rotate()
        rect = self.image.blit(img, self.original_image.get_rect())
        self.image = img.subsurface(rect)

        if DEBUG:
            disp = pygame.display.get_surface()
            pygame.draw.line(
                disp,
                "green",
                self.pos,
                self.pos + self.direction * self.size,
            )

    def input(self, dt: int):
        if self.joystick is not None:
            d_pad = self.joystick.get_hat(0)
            self.direction.x = pygame.math.Vector2(d_pad).x
        else:
            keys = pygame.key.get_pressed()

            if keys[pygame.K_LEFT]:
                self.direction.x = -1
            elif keys[pygame.K_RIGHT]:
                self.direction.x = 1
            else:
                self.direction.x = 0
        if self.pressing_jump_button():
            self.jump(dt)

    def pressing_jump_button(self):
        if self.joystick is not None:
            return self.joystick.get_button(0)
        keys = pygame.key.get_pressed()
        return keys[pygame.K_SPACE]

    def jump(self, dt: int):
        self.direction.y = -self.jump_increment * dt

    def move(self, dt: int):
        if self.direction.x:
            self.pos.x += self.direction.x * self.speed * dt
            self.angle += (1 if self.direction.x < 0 else -1) * self.angular_speed

    def check_collisions(self):
        collided_sprites = self.rect.collideobjectsall(
            self.collidable_sprites_buffer.sprites()
        )
        if not collided_sprites:
            return

        if self.direction.y:
            if self.direction.y < 0:
                collided_sprites.sort(key=lambda s: s.rect.y)
                collided = collided_sprites[0]
                self.rect.top = collided.rect.bottom
            elif self.direction.y > 0:
                collided_sprites.sort(key=lambda s: s.rect.y, reverse=True)
                collided = collided_sprites[0]
                self.rect.bottom = collided.rect.top
            self.pos.y = self.rect.centery

        if self.direction.x:
            if self.direction.x < 0:
                collided_sprites.sort(key=lambda s: s.rect.x)
                collided = collided_sprites[0]
                self.rect.left = collided.rect.right
            elif self.direction.x > 0:
                collided_sprites.sort(key=lambda s: s.rect.x, reverse=True)
                collided = collided_sprites[0]
                self.rect.right = collided.rect.left
            self.pos.x = self.rect.centerx

    def should_fall(self):
        if self.pressing_jump_button():
            return True

        ground = self.bottom_rect.collideobjects(
            self.collidable_sprites_buffer.sprites()
        )
        if ground is None:
            return True

        ground_rect: pygame.rect.Rect = ground.rect
        self.pos.y = ground_rect.top - self.size // 2

        self.direction.y = 0
        return False

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
