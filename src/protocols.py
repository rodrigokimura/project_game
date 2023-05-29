from typing import Protocol

import pygame


class HasRect(Protocol):
    rect: pygame.rect.Rect


class HasDamage(Protocol):
    @property
    def damage(self) -> int:
        ...
