import math
from typing import Any, Literal, Optional

import pygame

from blocks import BaseBlock
from settings import BLOCK_SIZE, DEBUG
from world import GravitySprite, World


class Player(GravitySprite):
    def __init__(
        self,
        world: World,
        position: Optional[tuple[int, int]],
        joystick: Optional[pygame.joystick.JoystickType],
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(world, *groups)

        self.joystick = joystick
        if self.joystick is not None:
            self.joystick.init()

        position = position or pygame.display.get_surface().get_rect().center

        self.position = pygame.math.Vector2(*position)

        self.angle = 0
        self.size = 2 * BLOCK_SIZE

        self._draw()
        self.create_collision_mask()

        self.rect = self.image.get_rect(center=self.position)

        self.linear_velocity = 8
        self.jump_scalar_velocity = 10
        self.boost_scalar_velocity = 30

        # should be less than gravity, otherwise player will fly up
        self.glide_scalar_acceleration = 10

        self.angular_velocity = self.linear_velocity / 2 * math.pi

        self.bottom_rect = pygame.rect.Rect(
            self.position.x - 1, self.position.y + self.size / 2, 2, 1
        )

        self.max_jump_time = 0.2
        self.max_jump_count = 2
        self._jump_count = 0
        self._jump_time = 0
        self._b = False
        self._can_keep_jumping = False

    def _draw(self):
        size = self.size
        sq_size = size // 2
        self.image = pygame.surface.Surface((size, size)).convert_alpha()
        self.image.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.circle(self.image, "green", self.image.get_rect().center, size // 2)
        rect = pygame.Rect(
            (size - sq_size) // 2, (size - sq_size) // 2, sq_size, sq_size
        )
        pygame.draw.rect(self.image, "red", rect, 0)
        self.original_image = self.image.copy()

    def create_collision_mask(self):
        shell = pygame.surface.Surface((self.size, self.size)).convert_alpha()
        shell.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.circle(
            shell, "green", self.image.get_rect().center, self.size // 2, width=2
        )
        self.mask = pygame.mask.from_surface(shell)

    def update(self, dt: int, *args: Any, **kwargs: Any) -> None:
        self.input(dt)
        self.fall(dt)
        self.glide(dt)

        self.uncollide()

        self.update_angle()
        self.update_position(dt)
        self.update_image()
        self.update_rects()

        if DEBUG:
            self.draw_vectors()

    def input(self, dt: int):
        if self.joystick is not None:
            d_pad = self.joystick.get_hat(0)

            self.velocity.x = pygame.math.Vector2(d_pad).x * self.linear_velocity

            lb = self.joystick.get_button(4)
            rb = self.joystick.get_button(5)
            if rb:
                self.dash("r")
            if lb:
                self.dash("l")

            y = self.joystick.get_button(2)
            if y and self.velocity.x:
                self.boost()

            b = self.joystick.get_button(0)
            if b != self._b:
                self._b = b
                print(f"State changed to {b}")
                if b:
                    self._can_keep_jumping = True
                    print("B pressed")
                    self._jump_count += 1
                else:
                    print("B released")
                    if self._jump_count < self.max_jump_count:
                        self._jump_time = 0
            elif b:
                self.jump(dt)
        else:
            keys = pygame.key.get_pressed()

            if keys[pygame.K_LEFT]:
                self.velocity.x = -self.linear_velocity
            elif keys[pygame.K_RIGHT]:
                self.velocity.x = self.linear_velocity
            else:
                self.velocity.x = 0

    def dash(self, direction: Literal["l"] | Literal["r"]):
        # TODO: fix collision when velocity is too high
        if direction == "l":
            self.velocity.x = -self.boost_scalar_velocity
        else:
            self.velocity.x = self.boost_scalar_velocity

    def boost(self):
        self.velocity.x = self.velocity.x + (10 if self.velocity.x > 0 else -10)

    def jump(self, dt: int):
        if (
            self._jump_count < self.max_jump_count
            and self._jump_time < self.max_jump_time
        ):
            if self._can_keep_jumping:
                self.velocity.y = -self.jump_scalar_velocity
                self._jump_time += dt
            # else:
            #     self.velocity.y = 0
        else:
            self._can_keep_jumping = False

    def glide(self, dt: int):
        if self.should_fall() and self.joystick and self.joystick.get_button(0):
            if self.velocity.y > 0:
                self.velocity.y -= self.glide_scalar_acceleration * dt

    def reset_jump(self):
        self._jump_count = 0
        self._jump_time = 0

    def update_angle(self):
        if self.velocity.x:
            self.angle += (1 if self.velocity.x < 0 else -1) * self.angular_velocity

    def uncollide(self):
        collided_sprites = pygame.sprite.spritecollide(
            self,
            self.collidable_sprites_buffer,
            False,
            collided=pygame.sprite.collide_mask,
        )

        if not collided_sprites:
            return

        print(collided_sprites)

        first_collided_sprite: BaseBlock = collided_sprites[0]
        bounding_rect = first_collided_sprite.rect
        for block in collided_sprites:
            bounding_rect = bounding_rect.union(block.rect)

        collided_overlap = pygame.mask.Mask(bounding_rect.size, False)
        for block in collided_sprites:
            collided_overlap.draw(
                block.mask,
                (
                    block.rect.left - bounding_rect.left,
                    block.rect.top - bounding_rect.top,
                ),
            )
        collided_overlap = collided_overlap.overlap_mask(
            self.mask,
            (
                self.rect.left - bounding_rect.left,
                self.rect.top - bounding_rect.top,
            ),
        )

        collided_overlap.to_surface(pygame.display.get_surface())
        centroid = collided_overlap.centroid()
        centroid = pygame.math.Vector2(
            centroid[0] + bounding_rect.left, centroid[1] + bounding_rect.top
        )

        # compute normal
        normal = centroid - pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        if abs(normal.x) <= 1:
            normal.x = 0
        if abs(normal.y) <= 1:
            normal.y = 0

        # remove normal component
        if normal.length():
            if self.velocity.project(normal).angle_to(normal) == 0:
                self.velocity -= self.velocity.project(normal)

    def update_position(self, dt):
        self.position += self.velocity * dt * self.size

    def update_image(self):
        img = self.rotate()
        rect = self.image.blit(img, self.original_image.get_rect())
        self.image = img.subsurface(rect)

    def update_rects(self):
        self.rect.center = (int(self.position.x), int(self.position.y))
        self.bottom_rect.left = int(self.position.x - 1)
        self.bottom_rect.top = int(self.position.y + self.size / 2)

    def should_fall(self):
        ground = self.bottom_rect.collideobjects(
            self.collidable_sprites_buffer.sprites()
        )
        if ground is None:
            return True

        ground_rect: pygame.rect.Rect = ground.rect
        self.position.y = ground_rect.top - self.size // 2
        self._jump_count = 0
        self._jump_time = 0

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

    def draw_vectors(self):
        surf = self.world.surface
        pygame.draw.line(
            surf,
            "green",
            self.position,
            self.position + self.velocity * BLOCK_SIZE,
        )
        pygame.draw.line(
            surf,
            "yellow",
            self.position,
            self.position + self.acceleration * BLOCK_SIZE,
        )
