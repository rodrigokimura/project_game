import enum
import math
from abc import ABC, abstractmethod
from typing import Any, Optional

import pygame

from blocks import BaseBlock, BaseCollectible, BaseHazard
from commons import Loadable, Storable
from input import BaseController, Controllable, JoystickController
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


class BasePlayer(Storable, Loadable, Controllable, GravitySprite, ABC):
    IMMUNITY_OVER = pygame.event.custom_type()
    DEAD = pygame.event.custom_type()
    PAUSE = pygame.event.custom_type()
    OPEN_INVENTORY = pygame.event.custom_type()
    DESTROY_BLOCK = pygame.event.custom_type()

    EVENTS = [IMMUNITY_OVER, DEAD, PAUSE, DESTROY_BLOCK, OPEN_INVENTORY]

    collidable_sprites_buffer: pygame.sprite.Group

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
    jump_scalar_velocity = 15
    dash_scalar_velocity = 60

    cursor_position = pygame.math.Vector2(0, 0)
    cursor_range = 5

    # should be less than gravity, otherwise player will fly up
    glide_scalar_acceleration = 10

    @property
    def hp_percentage(self):
        return self.health_points / self.max_health_points

    def move(self, _: float, amount: float):
        self.velocity.x = amount * self.linear_velocity

    def move_cursor(self, _: float, x: float, y: float):
        right_stick = pygame.math.Vector2(x, y)
        self.cursor_position = right_stick * self.cursor_range * BLOCK_SIZE

    def next_mode(self, _: float):
        self.mode = Mode(self.mode + 1)

    def destroy_block(self, _: float):
        if self.mode in (Mode.EXPLORATION, Mode.CONSTRUCTION):
            pygame.event.post(pygame.event.Event(self.DESTROY_BLOCK))

    def place_block(self, _: float):
        if self.mode == Mode.CONSTRUCTION:
            self.inventory.get_selected()
            print("Placing block")

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

    def _destroy_block(self, block: BaseBlock, dt: float):
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

    def update(self, dt: float):
        self.process_control_requests(dt)
        self.fall(dt)
        self.handle_collision()

    @abstractmethod
    def handle_collision(self):
        ...


class Player(BasePlayer):
    controller: JoystickController | None

    def __init__(
        self,
        gravity: int,
        terminal_velocity: int,
        position: Optional[tuple[int, int]],
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(gravity, terminal_velocity, *groups)
        self.inventory = Inventory()
        self.max_health_points = 100
        self.health_points = self.max_health_points

        position = position or pygame.display.get_surface().get_rect().center

        self.size = pygame.math.Vector2(2 * BLOCK_SIZE)
        self.position = pygame.math.Vector2(*position)

        self.angle = 0

        # for jumping mechanics
        self.max_jump_time = 0.2
        self.max_jump_count = 2

        self.setup()

        if self.image is None:
            raise Loadable.UnloadedObject
        self.rect = self.image.get_rect(center=self.position)

        self.max_immunity_time = 0.5
        self._is_immune = False

    def setup(self):
        # load unpickleble attributes
        self.controller = JoystickController(
            self, self.max_jump_count, self.max_jump_time
        )
        self.bottom_sprite = StandingBase(
            pygame.rect.Rect(
                self.position.x - 1, self.position.y + self.size.y / 2, 2, 1
            )
        )
        self._draw()
        self._create_collision_mask()
        self.inventory.setup()

    def unload(self):
        self.bottom_sprite = None
        self.original_image = None
        self.cursor_image = None
        self.image = None
        self.mask = None
        self.controller = None
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
        self.check_immunity()
        self.update_position(dt)
        self.update_angle(dt)
        self.update_image()

    def check_immunity(self):
        immunity_events = pygame.event.get(self.IMMUNITY_OVER, pump=False)
        if immunity_events:
            self._is_immune = False
            pygame.time.set_timer(self.IMMUNITY_OVER, 0)

    def reset_jump(self):
        if self.controller is None:
            raise Loadable.UnloadedObject
        self.controller.reset_jump()

    def handle_collision(self):
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
        self.position.y = ground_rect.top - self.size.y // 2
        self.reset_jump()
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
        if self.original_image is None:
            return
        img = pygame.Surface(self.original_image.get_size())
        img = pygame.transform.rotate(self.original_image, self.angle)
        new_x, new_y = img.get_size()
        new_x = new_x - self.original_image.get_size()[0]
        new_y = new_y - self.original_image.get_size()[1]
        img.scroll(-int(new_x / 2), -int(new_y / 2))
        return img
