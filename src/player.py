import enum
import math
from abc import ABC
from typing import Any, Literal, Optional

import pygame

from blocks import BaseBlock, BaseHazard
from collectibles import BaseCollectible
from inventory import BaseInventory, Inventory
from log import log
from settings import BLOCK_SIZE, DEBUG
from sprites import GravitySprite
from utils import CyclingIntEnum


def custom_collision_detection(sprite_left: Any, sprite_right: Any):
    return pygame.sprite.collide_mask(sprite_left, sprite_right) is not None


class Mode(CyclingIntEnum):
    EXPLORATION = enum.auto()
    CONSTRUCTION = enum.auto()
    COMBAT = enum.auto()


class StandingBase(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.rect.Rect, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.rect = rect
        self.mask = pygame.mask.Mask(self.rect.size, True)


class BasePlayer(ABC, pygame.sprite.Sprite):
    collidable_sprites_buffer: pygame.sprite.Group
    rect: pygame.rect.Rect
    image: pygame.surface.Surface
    max_health_points: int
    health_points: int
    cursor_image: pygame.surface.Surface
    cursor_position: pygame.math.Vector2
    mode: Mode = Mode.EXPLORATION
    destruction_power: int = 5

    collectible_pull_radius: int = 5  # in block size units
    collectible_grab_radius: int = 2  # in block size units
    inventory: BaseInventory

    @property
    def hp_percentage(self):
        return self.health_points / self.max_health_points

    def next_mode(self):
        self.mode = Mode(self.mode + 1)

    def get_cursor_coords(self):
        cursor_position = self.rect.move(self.cursor_position.x, self.cursor_position.y)
        return (
            cursor_position.x // BLOCK_SIZE + 1,
            cursor_position.y // BLOCK_SIZE + 1,
        )

    def destroy(self, block: BaseBlock, dt: int):
        block.integrity -= self.destruction_power * dt
        return block.integrity <= 0

    def pull_collectibles(self, collectibles_group: pygame.sprite.Group):
        # TODO: avoid passing all collectibles
        for collectible in collectibles_group.sprites():
            collectible: BaseCollectible
            collectible_position = pygame.math.Vector2(collectible.rect.center)
            player_position = pygame.math.Vector2(self.rect.center)
            diff = player_position - collectible_position
            if not diff:
                return

            distance = diff.magnitude() / BLOCK_SIZE
            if distance < self.collectible_pull_radius:
                collectible.pulling_velocity = diff.normalize()
            else:
                collectible.pulling_velocity.update(0)
            if distance < self.collectible_grab_radius:
                self.grab_collectible(collectible, collectibles_group)

    def grab_collectible(
        self, collectible: BaseCollectible, group: pygame.sprite.Group
    ):
        if DEBUG:
            log(f"Grabbing collectible: {collectible}")
        collectible.remove(group)
        self.inventory.add(collectible)
        print(self.inventory)
        del collectible


class Player(BasePlayer, GravitySprite):
    IMMUNITY_OVER = pygame.event.custom_type()
    DEAD = pygame.event.custom_type()
    PAUSE = pygame.event.custom_type()
    DESTROY_BLOCK = pygame.event.custom_type()
    EVENTS = [IMMUNITY_OVER, DEAD, PAUSE, DESTROY_BLOCK]

    def __init__(
        self,
        gravity: int,
        terminal_velocity: int,
        position: Optional[tuple[int, int]],
        joystick: Optional[pygame.joystick.JoystickType],
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(gravity, terminal_velocity, *groups)
        self.inventory = Inventory()
        self.max_health_points = 100
        self.health_points = self.max_health_points

        self.joystick = joystick
        if self.joystick is not None:
            self.joystick.init()

        position = position or pygame.display.get_surface().get_rect().center

        self.position = pygame.math.Vector2(*position)

        self.angle = 0
        self.size = 2 * BLOCK_SIZE

        self.cursor_position = pygame.math.Vector2(0, 0)
        self.cursor_range = 5

        self._draw()
        self.create_collision_mask()

        self.rect = self.image.get_rect(center=self.position)

        self.linear_velocity = 8
        self.jump_scalar_velocity = 10
        self.boost_scalar_velocity = 30

        # should be less than gravity, otherwise player will fly up
        self.glide_scalar_acceleration = 10

        self.bottom_sprite = StandingBase(
            pygame.rect.Rect(self.position.x - 1, self.position.y + self.size / 2, 2, 1)
        )

        # for jumping mechanics
        self.max_jump_time = 0.2
        self.max_jump_count = 2
        self._jump_count = 0
        self._jump_time = 0
        self._b = False
        self._can_keep_jumping = False

        self.max_immunity_time = 0.5
        self._is_immune = False

        # change modes
        self._can_change_mode = True

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

        # draw cursor image
        self.cursor_image = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()
        rect = self.cursor_image.get_rect()
        rect.center = self.image.get_rect().center
        self.cursor_image.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.circle(
            self.cursor_image,
            "orange",
            self.cursor_image.get_rect().center,
            BLOCK_SIZE // 4,
            1,
        )

    def create_collision_mask(self):
        shell = pygame.surface.Surface((self.size, self.size)).convert_alpha()
        shell.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.circle(
            shell, "green", self.image.get_rect().center, self.size // 2, width=2
        )
        self.mask = pygame.mask.from_surface(shell)

    def update(self, dt: int, *args: Any, **kwargs: Any) -> None:
        self.check_immunity()
        self.input(dt)
        self.fall(dt)
        self.glide(dt)

        self.uncollide()

        self.update_angle(dt)
        self.update_image()
        self.update_position(dt)
        self.update_rects()

    def check_immunity(self):
        immunity_events = pygame.event.get(self.IMMUNITY_OVER, pump=False)
        if immunity_events:
            self._is_immune = False
            pygame.time.set_timer(self.IMMUNITY_OVER, 0)

    def input(self, dt: int):
        if self.joystick is not None:
            left_stick_x = self.joystick.get_axis(0)
            left_stick_x = round(left_stick_x, 1)
            self.velocity.x = pygame.math.Vector2(left_stick_x).x * self.linear_velocity

            lb = self.joystick.get_button(4)
            rb = self.joystick.get_button(5)

            # to avoid continuous trigger, we need a control bool
            lt = self.joystick.get_button(6)
            if lt and self._can_change_mode:
                self._can_change_mode = False
                self.next_mode()
            elif lt == 0:
                self._can_change_mode = True

            # block destruction
            rt = self.joystick.get_button(7)
            if rt and self.mode in (Mode.EXPLORATION, Mode.CONSTRUCTION):
                pygame.event.post(pygame.event.Event(self.DESTROY_BLOCK))

            if rb:
                self.dash("r")
            if lb:
                self.dash("l")

            y = self.joystick.get_button(0)
            if y and self.velocity.x:
                self.boost()

            b = self.joystick.get_button(1)
            if b != self._b:
                self._b = b
                if b:
                    self._can_keep_jumping = True
                    self._jump_count += 1
                else:
                    if self._jump_count < self.max_jump_count:
                        self._jump_time = 0
            elif b:
                self.jump(dt)

            # cursor movement
            right_stick_x = self.joystick.get_axis(2)
            right_stick_y = self.joystick.get_axis(3)
            right_stick = pygame.math.Vector2(right_stick_x, right_stick_y)
            self.cursor_position = right_stick * self.cursor_range * BLOCK_SIZE

            # pause menu
            start = self.joystick.get_button(9)
            if start:
                pygame.event.post(pygame.event.Event(self.PAUSE))
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
        else:
            self._can_keep_jumping = False

    def glide(self, dt: int):
        if self.should_fall() and self.joystick and self.joystick.get_button(0):
            if self.velocity.y > 0:
                self.velocity.y -= self.glide_scalar_acceleration * dt

    def reset_jump(self):
        self._jump_count = 0
        self._jump_time = 0

    def update_angle(self, dt: int):
        if self.velocity.x:
            self.angle += -self.velocity.x * self.size * dt * math.pi

    def uncollide(self):
        collided_sprites = pygame.sprite.spritecollide(
            self,
            self.collidable_sprites_buffer,
            False,
            collided=custom_collision_detection,
        )

        if not collided_sprites:
            return

        first_hazard = next(
            iter(s for s in collided_sprites if isinstance(s, BaseHazard)), None
        )
        if first_hazard:
            self.take_tamage(first_hazard)

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

    def update_image(self):
        img = self.rotate()
        rect = self.image.blit(img, self.original_image.get_rect())
        self.image = img.subsurface(rect)

    def update_position(self, dt):
        self.position += self.velocity * dt * self.size

    def update_rects(self):
        self.rect.center = (int(self.position.x), int(self.position.y))
        self.bottom_sprite.rect.topleft = (
            int(self.position.x - 1),
            int(self.position.y + self.size / 2),
        )

    def should_fall(self):
        ground = pygame.sprite.spritecollide(
            self.bottom_sprite,
            self.collidable_sprites_buffer,
            False,
            collided=custom_collision_detection,
        )
        if not ground:
            return True
        ground = ground[0]
        if isinstance(ground, BaseHazard):
            self.take_tamage(ground)

        ground_rect: pygame.rect.Rect = ground.rect
        self.position.y = ground_rect.top - self.size // 2
        self._jump_count = 0
        self._jump_time = 0

        return False

    def take_tamage(self, hazard: BaseHazard):
        # TODO: knockback
        if not self._is_immune:
            self._is_immune = True
            pygame.time.set_timer(
                self.IMMUNITY_OVER, int(self.max_immunity_time * 1000)
            )

            self.health_points -= hazard.damage
            self.health_points = max(self.health_points, 0)
            if self.health_points == 0:
                pygame.event.post(pygame.event.Event(self.DEAD))

    def rotate(self):
        img = pygame.Surface(self.original_image.get_size())
        img = pygame.transform.rotate(self.original_image, self.angle)
        new_x, new_y = img.get_size()
        new_x = new_x - self.original_image.get_size()[0]
        new_y = new_y - self.original_image.get_size()[1]
        img.scroll(-int(new_x / 2), -int(new_y / 2))
        return img
