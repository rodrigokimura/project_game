from __future__ import annotations

import enum
import math
from abc import ABC, abstractmethod
from itertools import product
from typing import Optional

import pygame

from blocks import BaseBlock, BaseCollectible, BaseHazard, make_block
from commons import Damageable, Loadable, Storable
from input.constants import Controller
from input.controllers import (
    AiPlayerController,
    BaseController,
    JoystickPlayerController,
    KeyboardPlayerController,
    PlayerControllable,
    PlayerController,
)
from inventory import BaseInventory, Inventory
from log import log
from protocols import HasDamage
from settings import BLOCK_SIZE, DEBUG
from sprites import GravitySprite
from utils.collision import custom_collision_detection
from utils.container import Container2d
from utils.enum import CyclingIntEnum
from utils.timer import Timer


class Mode(CyclingIntEnum):
    EXPLORATION = enum.auto()
    CONSTRUCTION = enum.auto()
    COMBAT = enum.auto()


class StandingBase(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.rect.Rect, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.rect = rect
        self.mask = pygame.mask.Mask(self.rect.size, True)


class BaseCharacter(
    Storable, Loadable, Damageable, PlayerControllable, GravitySprite, ABC
):
    DEAD = pygame.event.custom_type()
    PAUSE = pygame.event.custom_type()
    OPEN_INVENTORY = pygame.event.custom_type()
    DESTROY_BLOCK = pygame.event.custom_type()
    PLACE_BLOCK = pygame.event.custom_type()
    SHOOT = pygame.event.custom_type()

    EVENTS = [DEAD, PAUSE, DESTROY_BLOCK, PLACE_BLOCK, OPEN_INVENTORY, SHOOT]

    rect: pygame.rect.Rect
    size: pygame.math.Vector2
    position: pygame.math.Vector2

    max_health_points: int
    health_points: int

    # unpickleble attrs
    # must be set to None before pickling
    mask: pygame.mask.Mask | None
    image: pygame.surface.Surface | None
    original_image: pygame.surface.Surface | None
    cursor_image: pygame.surface.Surface | None
    bottom_sprite: StandingBase | None
    controller: BaseController | None

    cursor_position: pygame.math.Vector2
    mode: Mode = Mode.EXPLORATION
    destruction_power: int = 5

    collectible_pull_radius: int = 5  # in block size units
    collectible_grab_radius: int = 2  # in block size units
    inventory: BaseInventory

    linear_velocity = 16
    jump_scalar_velocity = 20
    dash_scalar_velocity = 60

    cursor_position = pygame.math.Vector2(0, 0)
    cursor_range = 10

    # should be less than gravity, otherwise player will fly up
    glide_scalar_acceleration = 10

    def __init__(
        self,
        gravity: int,
        terminal_velocity: int,
        position: tuple[int, int] | None,
        blocks: Container2d[BaseBlock],
    ) -> None:
        super().__init__(gravity, terminal_velocity)
        self.blocks = blocks
        position = position or pygame.display.get_surface().get_rect().center
        self.position = pygame.math.Vector2(*position)
        self.collision_buffer = pygame.sprite.Group()
        self.enemies_buffer = pygame.sprite.Group()

    @property
    def hp_percentage(self):
        return self.health_points / self.max_health_points

    def move(self, _: float, amount: float):
        self.velocity.x = amount * self.linear_velocity

    def move_cursor(self, _: float, x: float, y: float):
        right_stick = pygame.math.Vector2(x, y)
        if right_stick:
            right_stick.clamp_magnitude_ip(1)
        self.cursor_position = right_stick * self.cursor_range * BLOCK_SIZE

    def next_mode(self, _: float):
        self.mode = Mode(self.mode + 1)

    def destroy_block(self, _: float):
        if self.mode in (Mode.EXPLORATION, Mode.CONSTRUCTION):
            event = pygame.event.Event(self.DESTROY_BLOCK)
            event.power = self.destruction_power
            event.coords = self.get_cursor_coords()
            pygame.event.post(event)

    def place_block(self, _: float):
        if self.mode == Mode.CONSTRUCTION and (cls := self.inventory.pop()):
            event = pygame.event.Event(self.PLACE_BLOCK)
            event.block = make_block(cls, self.get_cursor_coords())  # type: ignore
            pygame.event.post(event)

    def shoot(self, _: float):
        if self.mode == Mode.COMBAT:
            event = pygame.event.Event(self.SHOOT)
            event.source = self
            event.position = self.position
            event.velocity = self.cursor_position * 1
            pygame.event.post(event)

    def pause(self, _: float):
        pygame.event.post(pygame.event.Event(self.PAUSE))

    def dash_left(self, _: float):
        if self.mode != Mode.CONSTRUCTION:
            self.velocity.x = -self.dash_scalar_velocity

    def dash_right(self, _: float):
        if self.mode != Mode.CONSTRUCTION:
            self.velocity.x = self.dash_scalar_velocity

    def boost(self, _: float):
        self.velocity.x *= 2

    def jump(self, _: float):
        self.velocity.y = -self.jump_scalar_velocity

    def glide(self, dt: float):
        if self.velocity.y > 0:
            self.velocity.y -= self.glide_scalar_acceleration * dt

    def open_inventory(self, _: float):
        pygame.event.post(pygame.event.Event(self.OPEN_INVENTORY))

    def process_control_requests(self, dt: float):
        if self.controller is None:
            raise Loadable.UnloadedObject
        self.controller.control(dt)

    def get_cursor_coords(self):
        cursor_position = self.rect.move(self.cursor_position.x, self.cursor_position.y)
        return (
            cursor_position.x // BLOCK_SIZE + 1,
            cursor_position.y // BLOCK_SIZE + 1,
        )

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
        self.inventory.add(collectible.__class__)
        del collectible

    def update_position(self, dt: float):
        self.position += self.velocity * dt * BLOCK_SIZE
        if self.bottom_sprite is None:
            raise Loadable.UnloadedObject

        self.rect.center = (int(self.position.x), int(self.position.y))
        self.bottom_sprite.rect.topleft = (
            int(self.position.x - 1),
            int(self.position.y + self.size.y / 2),
        )

    def update_collision_buffer(self):
        margin = 3
        ref_x, ref_y = self.rect.center
        ref_x, ref_y = ref_x // BLOCK_SIZE, ref_y // BLOCK_SIZE
        self.collision_buffer.empty()
        for x, y in product(
            range(ref_x - margin, ref_x + margin), range(ref_y - margin, ref_y + margin)
        ):
            block = self.blocks.get_element((x, y))
            if block is not None:
                self.collision_buffer.add(block)

        if self.enemies_buffer:
            self.collision_buffer.add(self.enemies_buffer.sprites())

    def update(self, dt: float):
        super().update(dt)
        self.update_collision_buffer()
        self.process_control_requests(dt)
        self.handle_collision()

    @abstractmethod
    def set_controller(self, controller_id: Controller):
        ...

    @abstractmethod
    def handle_collision(self):
        ...


class Player(BaseCharacter):
    controller: PlayerController | None

    def __init__(
        self,
        gravity: int,
        terminal_velocity: int,
        position: Optional[tuple[int, int]],
        blocks: Container2d[BaseBlock],
    ) -> None:
        super().__init__(gravity, terminal_velocity, position, blocks)
        self.inventory = Inventory()
        self.max_health_points = 100
        self.health_points = self.max_health_points

        self.size = pygame.math.Vector2(2 * BLOCK_SIZE)
        self.angle = 0
        self.rect = pygame.rect.Rect(self.position, self.size)

        # for jumping mechanics
        self.max_jump_time = 0.2
        self.max_jump_count = 2

        self.setup()

        self._is_immune = False
        self.immunity_timer = Timer(0.5, self.reset_immunity)

    def setup(self):
        # load unpickleble attributes
        self.bottom_sprite = StandingBase(
            pygame.rect.Rect(
                self.position.x - 1, self.position.y + self.size.y / 2, 2, 1
            )
        )
        self._draw()
        self._create_collision_mask()
        self.inventory.setup()

    def set_controller(self, controller_id: Controller):
        self.inventory.set_controller(controller_id)
        if controller_id == Controller.JOYSTICK:
            self.controller = JoystickPlayerController(
                self, self.max_jump_count, self.max_jump_time
            )
        elif controller_id == Controller.KEYBOARD:
            self.controller = KeyboardPlayerController(
                self, self.max_jump_count, self.max_jump_time
            )

    def unload(self):
        self.bottom_sprite = None
        self.original_image = None
        self.cursor_image = None
        self.image = None
        self.mask = None
        self.controller = None
        self.collision_buffer.empty()
        self.enemies_buffer.empty()
        self.inventory.unload()

    def _draw(self):
        size = self.size.x
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

    def _create_collision_mask(self):
        shell = pygame.surface.Surface(self.size).convert_alpha()
        shell.fill(pygame.Color(0, 0, 0, 0))
        if self.image is None:
            raise Loadable.UnloadedObject
        pygame.draw.circle(
            shell, "green", self.image.get_rect().center, self.size.x // 2, width=2
        )
        self.mask = pygame.mask.from_surface(shell)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.update_position(dt)
        self.update_angle(dt)
        self.update_image()
        self.immunity_timer.inc(dt)

    def reset_jump(self):
        if self.controller is None:
            raise Loadable.UnloadedObject
        self.controller.reset_jump()

    def handle_collision(self):
        collided_sprites = pygame.sprite.spritecollide(
            self,
            self.collision_buffer,
            False,
            collided=custom_collision_detection,
        )

        if not collided_sprites:
            return

        for sprite in collided_sprites:
            if isinstance(sprite, (BaseHazard, Enemy)):
                self.take_damage(sprite)

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
        if self.mask is None:
            raise Loadable.UnloadedObject
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

    def update_angle(self, dt: float):
        if self.velocity.x:
            self.angle += -self.velocity.x * self.size.x * dt * math.pi

    def update_image(self):
        img = self.rotate()
        if img is None or self.image is None or self.original_image is None:
            raise Loadable.UnloadedObject

        rect = self.image.blit(img, self.original_image.get_rect())
        self.image = img.subsurface(rect)

    def should_fall(self):
        if self.bottom_sprite is None:
            raise Loadable.UnloadedObject

        ground = pygame.sprite.spritecollide(
            self.bottom_sprite,
            self.collision_buffer,
            False,
            collided=custom_collision_detection,
        )
        if not ground:
            return True
        ground = ground[0]
        if isinstance(ground, (BaseHazard, Enemy)):
            self.take_damage(ground)

        ground_rect: pygame.rect.Rect = ground.rect
        self.position.y = ground_rect.top - self.size.y // 2
        self.reset_jump()
        return False

    def take_damage(self, hazard: HasDamage):
        # TODO: knockback
        self.immunity_timer.start()
        if not self._is_immune:
            self._is_immune = True
            self.health_points -= hazard.damage
            self.health_points = max(self.health_points, 0)
            if self.health_points == 0:
                event = pygame.event.Event(self.DEAD)
                event.character = self
                pygame.event.post(event)

    def reset_immunity(self):
        self._is_immune = False
        self.immunity_timer.reset()

    def rotate(self):
        if self.original_image is None:
            return self.original_image
        img = pygame.Surface(self.original_image.get_size())
        img = pygame.transform.rotate(self.original_image, self.angle)
        new_x, new_y = img.get_size()
        new_x = new_x - self.original_image.get_size()[0]
        new_y = new_y - self.original_image.get_size()[1]
        img.scroll(-int(new_x / 2), -int(new_y / 2))
        return img


class Enemy(Player):
    damage = 20

    def set_controller(self, controller_id: Controller):
        self.inventory.set_controller(controller_id)
        self.controller = AiPlayerController(self)

    def _draw(self):
        size = self.size.x
        sq_size = size // 2
        self.image = pygame.surface.Surface((size, size)).convert_alpha()
        self.image.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.circle(
            self.image, "purple", self.image.get_rect().center, size // 2
        )
        rect = pygame.Rect(
            (size - sq_size) // 2, (size - sq_size) // 2, sq_size, sq_size
        )
        pygame.draw.rect(self.image, "red", rect, 0)
        self.original_image = self.image.copy()

        # draw cursor image
        self.cursor_image = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()
        self.cursor_image.fill(pygame.Color(0, 0, 0, 0))
