from abc import ABC, abstractmethod
from typing import Any

import pygame

from characters import BaseCharacter
from input.constants import Controller
from input.controllers import (
    BaseController,
    JoystickMenuController,
    KeyboardMenuController,
    MenuControllable,
)
from settings import CONSOLE_FONT, DEFAULT_FONT, MENU_FONT
from world import BaseWorld


class ControllerDetection:
    CONTROLLER_DETECTED = pygame.event.custom_type()
    EVENTS = [CONTROLLER_DETECTED]

    def __init__(self) -> None:
        self.joystick_count = 0
        self.animation_time = 500
        self.display = pygame.display.get_surface()
        self.surface = pygame.surface.Surface(self.display.get_size())
        self.font = pygame.font.Font(MENU_FONT, 100)
        self.draw_static()

    def run(self, dt: float):
        self.draw(dt)
        self.detect_controller()

    def draw_static(self):
        self.surface.fill("black")

    def draw(self, _: float):
        text = self.font.render("Press any key/button", False, "white")
        self.surface.blit(text, (0, 0))
        self.display.blit(self.surface, self.display.get_rect())

    def detect_controller(self):
        joysticks = pygame.joystick.get_count()
        if self.joystick_count != joysticks:
            self.joystick_count = joysticks
            print(f"Joysticks detected: {joysticks}")

        if self.joystick_count > 0:
            if self.detect_joystick():
                return

        self.detect_keyboard_and_mouse()

    def detect_joystick(self):
        for joystick_id in range(self.joystick_count):
            joystick = pygame.joystick.Joystick(joystick_id)
            for button_id in range(joystick.get_numbuttons()):
                if joystick.get_button(button_id):
                    event = pygame.event.Event(self.CONTROLLER_DETECTED)
                    event.controller = Controller.JOYSTICK
                    pygame.event.post(event)
                    return True
        return False

    def detect_keyboard_and_mouse(self):
        r = pygame.key.get_pressed()

        # HACK: pygame prevents iterating directly over r
        if any(r[i] for i in range(len(r))):
            event = pygame.event.Event(self.CONTROLLER_DETECTED)
            event.controller = Controller.KEYBOARD
            pygame.event.post(event)
            return True
        return False


class Menu(MenuControllable):
    controller: BaseController

    class Item(pygame.sprite.Sprite):
        def __init__(self, text, event_id, *groups: pygame.sprite.Group) -> None:
            super().__init__(*groups)
            self.text = text
            self.event = pygame.event.Event(event_id)

            font = pygame.font.Font(MENU_FONT, 100)
            font_padding = 20
            text_surf = font.render(text, False, "blue")
            x, y = text_surf.get_size()
            padded_text_surf = pygame.surface.Surface(
                (x + 2 * font_padding, y + 2 * font_padding)
            ).convert_alpha()
            padded_text_surf.fill((0, 0, 0, 0))
            padded_text_surf.blit(text_surf, (font_padding, font_padding))

            self.original_image = padded_text_surf
            self.image = self.original_image.copy()
            self.highlighted_image = self.original_image.copy()
            pygame.draw.rect(
                self.highlighted_image, "blue", self.highlighted_image.get_rect(), 1
            )
            self.rect = self.image.get_rect()
            self.enabled = True
            self.highlighted = False

        def update(self, *args: Any, **kwargs: Any) -> None:
            self.image = (
                self.highlighted_image if self.highlighted else self.original_image
            )
            return super().update(*args, **kwargs)

    def __init__(self, items: dict[str, int]) -> None:
        self.font = pygame.font.Font(DEFAULT_FONT, 100)
        self._items = [self.Item(txt, id) for txt, id in items.items()]
        self.all_items = pygame.sprite.Group()
        self.all_items.add(self._items)

        self.display = pygame.display.get_surface()
        self.static_image = pygame.surface.Surface(self.display.get_size())
        self.highlighted_item = 0
        self.draw_static()
        pygame.joystick.init()
        joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        self.joystick = joysticks[0] if joysticks else None
        self.controller = JoystickMenuController(self)

    def draw_static(self):
        padding = 80
        font_padding = 20

        w, h = self.display.get_size()
        w, h = w - 2 * padding, h - 2 * padding
        menu_rect = pygame.rect.Rect(padding, padding, w, h)

        pygame.draw.rect(self.static_image, "blue", menu_rect, 1)

        for i, item in enumerate(self.all_items):
            if i == self.highlighted_item:
                item.highlighted = True
            item.rect.x = padding + font_padding
            item.rect.y = (
                padding + font_padding + i * (item.image.get_size()[1] + font_padding)
            )

    def run(self, dt: float):
        self.controller.control(dt)
        self.all_items.update()
        self.display.blit(self.static_image, (0, 0))
        self.display.blits(tuple((s.image, s.rect) for s in self.all_items))

    def highlight_prev(self):
        self.highlight_item(self.highlighted_item - 1)

    def highlight_next(self):
        self.highlight_item(self.highlighted_item + 1)

    def highlight_item(self, index: int):
        index = int(pygame.math.clamp(index, 0, len(self._items) - 1))
        self._items[self.highlighted_item].highlighted = False
        self.highlighted_item = index
        self._items[self.highlighted_item].highlighted = True

    def select(self, _: float):
        event = self._items[self.highlighted_item].event
        pygame.event.post(event)

    def move(self, _: float, x: float, y: float):
        if x < 0:
            self.highlight_prev()
        elif x > 0:
            self.highlight_next()
        if y < 0:
            self.highlight_next()
        elif y > 0:
            self.highlight_prev()

    def set_controller(self, controller_id: Controller):
        if controller_id == Controller.JOYSTICK:
            self.controller = JoystickMenuController(self)
        elif controller_id == Controller.KEYBOARD:
            self.controller = KeyboardMenuController(self)


class BaseInterfaceElement(ABC):
    line_positions: tuple[int, int]

    @abstractmethod
    def draw(self):
        ...


class PlayerStats(BaseInterfaceElement):
    def __init__(self, player: BaseCharacter) -> None:
        super().__init__()
        self.player = player
        self.line_positions = (10, 10)
        self.width, self.height = 100, 10
        self.fill_color = "red"
        self.border_color = "white"
        self.hp_bar = pygame.rect.Rect(*self.line_positions, self.width, self.height)
        self.hp_bar_fill = self.hp_bar.copy()

    def draw(self):
        display_surface = pygame.display.get_surface()
        self.hp_bar_fill.width = int(self.player.hp_percentage * self.width)
        pygame.draw.rect(display_surface, self.fill_color, self.hp_bar_fill)
        pygame.draw.rect(display_surface, self.border_color, self.hp_bar, 1)


class PlayerMode(BaseInterfaceElement):
    def __init__(self, player: BaseCharacter) -> None:
        super().__init__()
        self.player = player
        self.font = pygame.font.Font(CONSOLE_FONT, 30)

    def draw(self):
        display_surface = pygame.display.get_surface()
        s = self.font.render(self.player.mode.name, False, "white")
        display_surface.blit(s, (10, 70))


class TimeDisplay(BaseInterfaceElement):
    def __init__(self, world: BaseWorld) -> None:
        super().__init__()
        self.world = world
        self.font = pygame.font.Font(DEFAULT_FONT, 20)

    def draw(self):
        display_surface = pygame.display.get_surface()
        s = self.font.render(self.world.time.strftime("%H:%M"), False, "white")
        display_surface.blit(s, (10, 25))
        s = self.font.render(self.world.day_part.value, False, "white")
        display_surface.blit(s, (10, 45))
