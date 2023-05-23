from abc import abstractmethod
from itertools import product

import pygame

from blocks import BaseCollectible, collectible_images
from commons import Loadable
from input.constants import Controller
from input.controllers import (
    InventoryControllable,
    JoystickInventoryController,
    KeyboardInventoryController,
)
from settings import DEFAULT_FONT, SCREEN_HEIGHT, SCREEN_WIDTH


class BaseInventory(Loadable, InventoryControllable):
    CLOSE = pygame.event.custom_type()

    collectibles: dict[type[BaseCollectible], int]

    def add(self, collectible: type[BaseCollectible]):
        if collectible in self.collectibles:
            self.collectibles[collectible] += 1
        else:
            self.collectibles[collectible] = 1

    def remove(self, collectible: type[BaseCollectible]):
        if collectible in self.collectibles:
            if self.collectibles[collectible] > 1:
                self.collectibles[collectible] -= 1
            else:
                del self.collectibles[collectible]

    def pop(self) -> type[BaseCollectible] | None:
        if self.is_empty():
            return None
        selected = self.get_selected()
        if selected is None:
            return None
        cls, _ = selected
        self.remove(cls)
        return cls

    @abstractmethod
    def is_empty(self) -> bool:
        ...

    @abstractmethod
    def get_selected(self) -> tuple[type[BaseCollectible], int] | None:
        ...

    def close(self, _: float):
        pygame.event.post(pygame.event.Event(self.CLOSE))

    def set_controller(self, controller_id: Controller):
        if controller_id == Controller.JOYSTICK:
            self.controller = JoystickInventoryController(self)
        elif controller_id == Controller.KEYBOARD:
            self.controller = KeyboardInventoryController(self)

    @abstractmethod
    def update(self, dt: float):
        ...

    def __str__(self) -> str:
        return str(self.collectibles)


class Inventory(BaseInventory, Loadable):
    """Simple limitless inventory"""

    def __init__(self) -> None:
        self.collectibles: dict[type[BaseCollectible], int] = {}
        self.setup()
        self.grid = (20, 10)
        self.selected = (0, 0)

    def is_empty(self) -> bool:
        return not self.collectibles

    def get_selected(self):
        if self.is_empty():
            return None
        x, y = self.selected
        collectibles = [i for i in self.collectibles.items()]
        i = (x + 1) * (y + 1) - 1
        try:
            cls, count = collectibles[i]
            return cls, count
        except IndexError:
            return None

    def update(self, dt: float):
        self.update_image()

        if self.joystick is None:
            raise Loadable.UnloadedObject
        self.controller.control(dt)

    def move(self, _: float, x: float, y: float):
        selected_x, selected_y = self.selected

        if x == -1:
            if selected_x > 0:
                selected_x -= 1
        elif x == 1:
            if selected_x < self.grid[0] - 1:
                selected_x += 1

        if y == 1:
            if selected_y > 0:
                selected_y -= 1
        elif y == -1:
            if selected_y < self.grid[1] - 1:
                selected_y += 1

        self.selected = int(selected_x), int(selected_y)

    def update_image(self):
        if self.image is None or self.font is None:
            raise Loadable.UnloadedObject

        p = 100
        m = 30
        slot_size = 32
        slot_p = 10

        rect = pygame.rect.Rect(p, p, SCREEN_WIDTH - 2 * p, SCREEN_HEIGHT - 2 * p)
        pygame.draw.rect(self.image, "black", rect)
        pygame.draw.rect(self.image, "blue", rect, 1)
        slot_rect = pygame.rect.Rect(0, 0, slot_size, slot_size)
        collectibles = [i for i in self.collectibles.items()]

        for x, y in product(range(self.grid[0]), range(self.grid[1])):
            slot_rect.topleft = (
                p + m + x * (slot_size + slot_p),
                p + m + y * (slot_size + slot_p),
            )
            pygame.draw.rect(self.image, "blue", slot_rect, 1)

            i = y * self.grid[0] + x
            if i < len(collectibles):
                cls, count = collectibles[i]
                img = collectible_images[cls]
                self.image.blit(
                    img,
                    (
                        p + m + x * (slot_size + slot_p),
                        p + m + y * (slot_size + slot_p),
                    ),
                )
                txt = self.font.render(f"x {count}", False, "white")
                self.image.blit(
                    txt,
                    (
                        p + m + x * (slot_size + slot_p) + slot_size - 10,
                        p + m + y * (slot_size + slot_p) + slot_size - 10,
                    ),
                )

        # highlight
        slot_rect.topleft = (
            p + m + self.selected[0] * (slot_size + slot_p),
            p + m + self.selected[1] * (slot_size + slot_p),
        )
        pygame.draw.rect(self.image, "grey", slot_rect, 2)
        x, y = self.selected
        i = y * self.grid[0] + x
        try:
            cls, count = collectibles[i]
            txt = self.font.render(cls.__name__, False, "white")
            self.image.blit(
                txt,
                (
                    p + m + x * (slot_size + slot_p) + 10,
                    p + m + y * (slot_size + slot_p) + 10,
                ),
            )
        except IndexError:
            ...

        display = pygame.display.get_surface()
        display.blit(self.image, (0, 0))

    def setup(self):
        self.joystick = pygame.joystick.Joystick(0)
        self.image = pygame.surface.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.image = self.image.convert_alpha()
        self.image.fill((0, 0, 0, 0))
        self.font = pygame.font.Font(DEFAULT_FONT, 20)

    def unload(self):
        self.joystick = None
        self.image = None
        self.font = None
