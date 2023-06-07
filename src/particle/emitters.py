from __future__ import annotations

import pygame

from colors import Color
from particle.particles import Particle
from utils.blit import blit_multiple
from utils.timer import Timer


class Manager:
    def __init__(self) -> None:
        self.emitters: set[Emitter] = set()

    def add(self, emitter: Emitter):
        self.emitters.add(emitter)

    def remove(self, emitter: Emitter):
        try:
            self.emitters.remove(emitter)
        except KeyError:
            ...

    def update(self, dt: float):
        for emitter in self.emitters.copy():
            emitter.update(dt)

    def draw(self, surf: pygame.surface.Surface, offset: pygame.math.Vector2):
        for emitter in self.emitters.copy():
            emitter.draw(surf, offset)


class Emitter:
    def __init__(
        self,
        origin: pygame.math.Vector2,
        lifetime: float | None,
        rate: int,
        manager: Manager | None,
    ) -> None:
        if manager is None:
            raise ValueError

        self._particles = pygame.sprite.Group()
        self._lifetime = lifetime
        self.origin = origin
        self.rate = rate

        if lifetime is not None:
            self._age_timer = Timer(
                lifetime, self.kill if lifetime is not None else None
            )
            self._age_timer.start()

        self._emission_timer = Timer(1 / self.rate, self.emit)
        self._emission_timer.start()
        self._manager = manager
        self._manager.add(self)

    def __hash__(self) -> int:
        return hash(((self.origin.x, self.origin.y), self.rate, self._lifetime))

    def update(self, dt: float):
        if self._lifetime is not None:
            self._age_timer.inc(dt)
        self._emission_timer.inc(dt)
        self._particles.update(dt)

    def kill(self):
        self._manager.remove(self)

    def emit(self):
        self._emission_timer.reset()
        self._emission_timer.start()
        self._particles.add(Particle(self.origin, Color.BULLET, (2, 2), 100, 100))

    def draw(self, surf: pygame.surface.Surface, offset: pygame.math.Vector2):
        blit_multiple(surf, self._particles, offset)


class BulletShatter(Emitter):
    ...
