from abc import ABC, abstractmethod
from typing import Any, Iterable

import pygame

from player import BasePlayer
from world import BaseWorld


class Menu:
    class Item(pygame.sprite.Sprite):
        def __init__(self, text, event_id, *groups: pygame.sprite.Group) -> None:
            super().__init__(*groups)
            self.text = text
            self.event = pygame.event.Event(event_id)

            font = pygame.sysfont.SysFont("freesansbold", 100)
            font_padding = 20
            text_surf = font.render(text, True, "blue")
            x, y = text_surf.get_size()
            padded_text_surf = pygame.surface.Surface(
                (x + 2 * font_padding, y + 2 * font_padding)
            )
            padded_text_surf.blit(text_surf, (font_padding, font_padding))

            self.original_image = padded_text_surf
            self.highlighted_image = self.original_image.copy()
            self.image = self.original_image.copy()
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
        self.font = pygame.sysfont.SysFont("freesansbold", 100)
        self._items = [self.Item(txt, id) for txt, id in items.items()]
        self.all_items = pygame.sprite.Group()
        self.all_items.add(self._items)

        self.display = pygame.display.get_surface()
        self.surface = pygame.surface.Surface(self.display.get_size())
        self.highlighted_item = 0
        self.draw_static()
        pygame.joystick.init()
        joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        self.joystick = joysticks[0] if joysticks else None

    def draw_static(self):
        padding = 80
        font_padding = 20

        w, h = self.display.get_size()
        w, h = w - 2 * padding, h - 2 * padding
        menu_rect = pygame.rect.Rect(padding, padding, w, h)

        pygame.draw.rect(self.surface, "blue", menu_rect, 1)

        for i, item in enumerate(self.all_items):
            if i == self.highlighted_item:
                item.highlighted = True
            item.rect.x = padding + font_padding
            item.rect.y = (
                padding + font_padding + i * (item.image.get_size()[1] + font_padding)
            )

    def run(self):
        self.all_items.draw(self.surface)

        d_pad_events = pygame.event.get(pygame.JOYHATMOTION)
        d_pad_events = [e for e in d_pad_events if e.hat == 0]
        if d_pad_events:
            d = d_pad_events[0].value[1]
            if d == 1:
                self.highlight_prev()
            elif d == -1:
                self.highlight_next()
        button_events = pygame.event.get(pygame.JOYBUTTONDOWN)
        if button_events:
            b = button_events[0].button
            if b == 0:
                self.select()

        self.all_items.update()
        self.display.blit(self.surface, (0, 0))

    def highlight_prev(self):
        self.highlight_item(self.highlighted_item - 1)

    def highlight_next(self):
        self.highlight_item(self.highlighted_item + 1)

    def highlight_item(self, index: int):
        index = int(pygame.math.clamp(index, 0, len(self._items) - 1))
        self._items[self.highlighted_item].highlighted = False
        self.highlighted_item = index
        self._items[self.highlighted_item].highlighted = True

    def select(self):
        event = self._items[self.highlighted_item].event
        pygame.event.post(event)


class BaseInterfaceElement(ABC):
    relative_position: tuple[int, int]

    @abstractmethod
    def draw(self):
        ...


class Camera:
    def __init__(
        self,
        size: tuple[int, int],
        player: BasePlayer,
        world: BaseWorld,
        interface_elements: Iterable[BaseInterfaceElement] | None = None,
    ) -> None:
        self.width, self.height = size
        self.player = player
        self.world = world
        self.interface_elements = interface_elements or []

    def get_rect(self):
        rect = pygame.rect.Rect(0, 0, self.width, self.height)
        rect.center = self.player.rect.center

        top = self.player.rect.centery - self.height / 2
        if top <= 0:
            rect.top = 0

        bottom = self.player.rect.centery + self.height / 2
        if bottom >= self.world.surface.get_rect().height:
            rect.bottom = self.world.surface.get_rect().height

        left = self.player.rect.centerx - self.width / 2
        if left < 0:
            rect.left = 0

        right = self.player.rect.centerx + self.width / 2
        if right >= self.world.surface.get_rect().width:
            rect.right = self.world.surface.get_rect().width

        return rect

    def update(self):
        display_surface = pygame.display.get_surface()
        display_surface.blit(self.world.surface, (0, 0), self.get_rect())

        for el in self.interface_elements:
            el.draw()


class PlayerStats(BaseInterfaceElement):
    def __init__(self, player: BasePlayer) -> None:
        super().__init__()
        self.player = player
        self.relative_position = (10, 10)
        self.width, self.height = 100, 10
        self.fill_color = "red"
        self.border_color = "white"
        self.hp_bar = pygame.rect.Rect(*self.relative_position, self.width, self.height)
        self.hp_bar_fill = self.hp_bar.copy()

    def draw(self):
        super().draw()
        display_surface = pygame.display.get_surface()
        self.hp_bar_fill.width = int(self.player.hp_percentage * self.width)
        pygame.draw.rect(display_surface, self.fill_color, self.hp_bar_fill)
        pygame.draw.rect(display_surface, self.border_color, self.hp_bar, 1)
