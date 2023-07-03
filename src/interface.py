from abc import ABC, abstractmethod
from typing import Any

import pygame
import pygame._sdl2.controller
import pygame.freetype

from characters import BaseCharacter
from colors import Color, InterfaceColor
from draw import FillBorderColors, draw_bordered_rect
from input.constants import Button, Controller
from input.controllers import (
    BaseController,
    GamepadMenuController,
    KeyboardMenuController,
    MenuControllable,
)
from settings import CONSOLE_FONT, DEFAULT_FONT, MENU_FONT
from utils.timer import Timer
from world import World


class ControllerDetection:
    CONTROLLER_DETECTED = pygame.event.custom_type()
    EVENTS = [CONTROLLER_DETECTED]

    def __init__(self) -> None:
        self.gamepad_count = 0
        self.display = pygame.display.get_surface()
        self.timer = Timer(0.2, self._toggle_animation_state)
        self.timer.start()
        self._draw_static()
        self._on = True

    def _toggle_animation_state(self):
        self._on = not self._on
        self.timer.reset()
        self.timer.start()

    def run(self, dt: float):
        self.timer.inc(dt)
        self.draw(dt)
        self.detect_controller()

    def _draw_static(self):
        self.display.fill(InterfaceColor.MENU_BACKGROUND)
        font = pygame.freetype.Font(MENU_FONT, 100)
        font.antialiased = False
        font.pad = True
        self.text_surf, self.text_rect = font.render(
            "Press any key/button", InterfaceColor.PRIMARY_FONT
        )
        self.text_rect.center = self.display.get_rect().center

    def draw(self, _: float):
        if self._on:
            self.display.blit(self.text_surf, self.text_rect)
        else:
            self.display.fill(InterfaceColor.MENU_BACKGROUND)

    def detect_controller(self):
        # pylint: disable=protected-access
        # pylint: disable=no-member
        gamepads = pygame._sdl2.controller.get_count()
        if self.gamepad_count != gamepads:
            self.gamepad_count = gamepads

        if self.gamepad_count > 0:
            if self.detect_gamepad():
                return

        self.detect_keyboard_and_mouse()

    def detect_gamepad(self):
        for id_ in range(self.gamepad_count):
            # pylint: disable=protected-access
            # pylint: disable=no-member
            gamepad = pygame._sdl2.controller.Controller(id_)
            for button in Button:
                if gamepad.get_button(button):
                    event = pygame.event.Event(self.CONTROLLER_DETECTED)
                    event.controller = Controller.GAMEPAD
                    pygame.event.post(event)
                    return True
        return False

    def detect_keyboard_and_mouse(self):
        key_states = pygame.key.get_pressed()

        # HACK: pygame prevents iterating directly over r
        if any(key_states[i] for i in range(len(key_states))):
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

            font = pygame.freetype.Font(MENU_FONT, 100)
            font.antialiased = False
            font.pad = True
            _padding = 15
            text_surf, text_rect = font.render(text, InterfaceColor.PRIMARY_FONT)
            _image = pygame.surface.Surface(
                (text_rect.width + 2 * _padding, text_rect.height + 2 * _padding)
            ).convert_alpha()
            _image.fill(Color.TRANSPARENT)
            _image.blit(text_surf, (_padding, _padding))
            self.original_image = _image
            self.image = self.original_image.copy()
            self.highlighted_image = self.original_image.copy()
            pygame.draw.rect(
                self.highlighted_image,
                InterfaceColor.MENU_HIGHLIGHT,
                self.highlighted_image.get_rect(),
                1,
            )
            self.rect = self.image.get_rect()
            self.highlighted = False

        def update(self, *args: Any, **kwargs: Any) -> None:
            self.image = (
                self.highlighted_image if self.highlighted else self.original_image
            )
            return super().update(*args, **kwargs)

    def __init__(self, items: dict[str, int]) -> None:
        self._items = [self.Item(txt, id) for txt, id in items.items()]
        self.all_items = pygame.sprite.Group()
        self.all_items.add(self._items)

        self.display = pygame.display.get_surface()
        self.static_image = pygame.surface.Surface(self.display.get_size())
        self.highlighted_item = 0
        self.draw_static()

    def draw_static(self):
        padding = 80
        font_padding = 20

        width, height = self.display.get_size()
        width, height = width - 2 * padding, height - 2 * padding
        menu_rect = pygame.rect.Rect(padding, padding, width, height)

        draw_bordered_rect(
            self.static_image,
            menu_rect,
            FillBorderColors(
                InterfaceColor.MENU_BACKGROUND, InterfaceColor.MENU_BORDER
            ),
        )

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
        if controller_id == Controller.GAMEPAD:
            self.controller = GamepadMenuController(self)
        elif controller_id == Controller.KEYBOARD:
            self.controller = KeyboardMenuController(self)


class BaseInterfaceElement(ABC):
    line_positions: tuple[int, int]
    font_color: InterfaceColor = InterfaceColor.PRIMARY_FONT
    background_color: InterfaceColor = InterfaceColor.MENU_BACKGROUND

    @abstractmethod
    def draw(self):
        ...


class PlayerStats(BaseInterfaceElement):
    def __init__(self, player: BaseCharacter) -> None:
        super().__init__()
        self.player = player
        self.line_positions = (10, 10)
        self.width, self.height = 100, 10
        self.fill_color = InterfaceColor.HEALTH_POINTS
        self.border_color = InterfaceColor.BORDER
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
        self.font = pygame.freetype.Font(CONSOLE_FONT, 30)
        self.font.antialiased = False
        self.font.pad = True

    def draw(self):
        display_surface = pygame.display.get_surface()
        self.font.render_to(
            display_surface,
            (10, 60),
            self.player.mode.name,
            self.font_color,
            self.background_color,
        )


class TimeDisplay(BaseInterfaceElement):
    def __init__(self, world: World) -> None:
        self.world = world
        self.font = pygame.freetype.Font(DEFAULT_FONT, 20)
        self.font.antialiased = False
        self.font.pad = True

    def draw(self):
        display_surface = pygame.display.get_surface()
        self.font.render_to(
            display_surface,
            (10, 25),
            self.world.time.strftime("%H:%M"),
            self.font_color,
            self.background_color,
        )
        self.font.render_to(
            display_surface,
            (10, 42),
            self.world.day_part.value,
            self.font_color,
            self.background_color,
        )
