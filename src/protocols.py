from typing import Protocol

import pygame


class HasRect(Protocol):
    @property
    def rect(self) -> pygame.rect.Rect:
        ...


class HasDamage(Protocol):
    @property
    def damage(self) -> int:
        ...
