from abc import ABC, abstractmethod
from typing import Iterable

import pygame

from player import BasePlayer
from world import World


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
        world: World,
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
