from abc import abstractmethod
from itertools import product

import pygame
import pygame.freetype

from blocks import BaseCollectible, collectible_images
from colors import Color, InterfaceColor
from commons import Loadable
from draw import FillBorderColors, draw_bordered_rect
from input.constants import Controller
from input.controllers import (
    BaseController,
    InventoryControllable,
    JoystickInventoryController,
    KeyboardInventoryController,
)
from settings import CONSOLE_FONT, SCREEN_HEIGHT, SCREEN_WIDTH


class BaseInventory(Loadable, InventoryControllable):
    CLOSE = pygame.event.custom_type()

    collectibles: dict[type[BaseCollectible], int]
    controller: BaseController | None = None

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

    font: pygame.freetype.Font | None
    image: pygame.surface.Surface | None

    def __init__(self) -> None:
        self.collectibles: dict[type[BaseCollectible], int] = {}
        self.grid = (20, 10)
        self.selected = (0, 0)
        self.padding = 100
        self.margin = 30
        self.slot_size = 32
        self.slot_p = 10
        self.slot_rect = pygame.rect.Rect(0, 0, self.slot_size, self.slot_size)
        self.image: pygame.surface.Surface | None = None
        self._static_image: pygame.surface.Surface | None = None
        self.setup()

    def is_empty(self) -> bool:
        return not self.collectibles

    def get_selected(self):
        if self.is_empty():
            return None

        x, y = self.selected
        collectibles = list(self.collectibles.items())
        i = (x + 1) * (y + 1) - 1
        try:
            cls, count = collectibles[i]
            return cls, count
        except IndexError:
            return None

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

    def setup(self):
        self._draw_static()
        self.font = pygame.freetype.Font(CONSOLE_FONT, 32)
        self.image = self._static_image.copy()  # type: ignore

    def _draw_static(self):
        self._draw_background()
        self._draw_boundary()
        self._draw_slots()

    def _draw_background(self):
        self._static_image = pygame.surface.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        ).convert_alpha()
        self._static_image.fill(Color.TRANSPARENT)

    def _draw_boundary(self):
        if self._static_image is None:
            raise self.UnloadedObject

        bounding_box = pygame.rect.Rect(
            self.padding,
            self.padding,
            SCREEN_WIDTH - 2 * self.padding,
            SCREEN_HEIGHT - 2 * self.padding,
        )
        draw_bordered_rect(
            self._static_image,
            bounding_box,
            FillBorderColors(
                InterfaceColor.INVENTORY_BACKROUND, InterfaceColor.INVENTORY_ITEM_BORDER
            ),
        )

    def _draw_slots(self):
        if self._static_image is None:
            raise self.UnloadedObject

        for x, y in product(range(self.grid[0]), range(self.grid[1])):
            self.slot_rect.topleft = self._get_slot_rel_coords((x, y))
            pygame.draw.rect(
                self._static_image,
                InterfaceColor.INVENTORY_ITEM_BORDER,
                self.slot_rect,
                1,
            )

    def unload(self):
        self._static_image = None
        self.image = None
        self.font = None
        self.controller = None

    def update(self, dt: float):
        if self.controller is None:
            raise self.UnloadedObject

        self._update_image()
        self.controller.control(dt)

    def _update_image(self):
        if self._static_image is None or self.font is None:
            raise Loadable.UnloadedObject

        self.image = self._static_image.copy()

        self._draw_collectibles()
        self._highlight_selected()

        pygame.display.get_surface().blit(self.image, (0, 0))

    def _draw_collectibles(self):
        if self.image is None or self.font is None:
            raise self.UnloadedObject

        collectibles = list(self.collectibles.items())

        for x, y in product(range(self.grid[0]), range(self.grid[1])):
            i = y * self.grid[0] + x

            if i < len(collectibles):
                cls, count = collectibles[i]
                img = collectible_images[cls]
                self.image.blit(img, self._get_slot_rel_coords((x, y), (10, 10)))
                self.font.render_to(
                    self.image,
                    self._get_slot_rel_coords((x, y), (20, 20)),
                    str(count),
                    InterfaceColor.PRIMARY_FONT,
                )

    def _get_slot_rel_coords(
        self, coords: tuple[int, int], offset: tuple[int, int] = (0, 0)
    ):
        return tuple(
            self.padding + self.margin + coord * (self.slot_size + self.slot_p) + offset
            for coord, offset in zip(coords, offset)
        )

    def _highlight_selected(self):
        if self.image is None or self.font is None:
            raise self.UnloadedObject

        collectibles = list(self.collectibles.items())
        x, y = self.selected
        self.slot_rect.topleft = self._get_slot_rel_coords((x, y))
        pygame.draw.rect(
            self.image, InterfaceColor.INVENTORY_HIGHLIGHT, self.slot_rect, 2
        )
        i = y * self.grid[0] + x
        if i < len(collectibles):
            cls, _ = collectibles[i]
            self.font.render_to(
                self.image,
                self._get_slot_rel_coords((x, y), (10, 10)),
                cls.__name__,
                InterfaceColor.PRIMARY_FONT,
            )
