from abc import ABC, abstractmethod
from itertools import product

import pygame

from blocks import BaseCollectible, collectible_images
from commons import Loadable
from input.constants import Button
from settings import DEFAULT_FONT, SCREEN_HEIGHT, SCREEN_WIDTH


class BaseInventory(Loadable, ABC):
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

    def close(self):
        pygame.event.post(pygame.event.Event(self.CLOSE))

    @abstractmethod
    def update(self):
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
        self.lr = True
        self.ud = True

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

    def update(self):
        self.update_image()

        if self.joystick is None:
            raise Loadable.UnloadedObject

        if self.joystick.get_button(Button.B):
            self.close()

        x, y = self.selected
        left_right, up_down = self.joystick.get_hat(0)

        if self.lr and left_right == -1:
            if x > 0:
                x -= 1
                self.lr = False
        elif self.lr and left_right == 1:
            if x < self.grid[0] - 1:
                x += 1
                self.lr = False
        elif left_right == 0:
            self.lr = True

        if self.ud and up_down == 1:
            if y > 0:
                y -= 1
                self.ud = False
        elif self.ud and up_down == -1:
            if y < self.grid[1] - 1:
                y += 1
                self.ud = False
        elif up_down == 0:
            self.ud = True

        self.selected = x, y

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
