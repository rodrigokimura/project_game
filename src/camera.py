from typing import Iterable

import pygame

from interface import BaseInterfaceElement
from log import log
from player import BasePlayer, Mode
from settings import BLOCK_SIZE, DEBUG
from world import BaseWorld


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
        self._setup()

    def _setup(self):
        self.highlight = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()
        self.highlight.fill((0, 0, 0, 0))
        pygame.draw.rect(self.highlight, "red", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2, 4)

    def get_rect(self):
        rect = pygame.rect.Rect(0, 0, self.width, self.height)
        rect.center = self.player.rect.center

        top = self.player.rect.centery - self.height / 2
        if top <= 0:
            rect.top = 0

        bottom = self.player.rect.centery + self.height / 2
        if bottom >= self.world.rect.height:
            rect.bottom = self.world.rect.height

        left = self.player.rect.centerx - self.width / 2
        if left < 0:
            rect.left = 0

        right = self.player.rect.centerx + self.width / 2
        if right >= self.world.rect.width:
            rect.right = self.world.rect.width

        return rect

    def update(self):
        display_surface = pygame.display.get_surface()
        dx = display_surface.get_rect().centerx - self.get_rect().centerx
        dy = display_surface.get_rect().centery - self.get_rect().centery

        display_surface.fill("black")
        display_surface.blits(
            tuple(
                (spr.image, spr.rect.move(dx, dy))
                for spr in self.world.visibility_buffer.sprites()
            )
        )
        # draw all collectibles
        display_surface.blits(
            tuple(
                (spr.image, spr.rect.move(dx, dy))
                for spr in self.world.collectibles.sprites()
            )
        )
        display_surface.blit(self.player.image, self.player.rect.move(dx, dy))

        # render player cursor
        cursor_position = self.player.rect.move(
            self.player.cursor_position.x, self.player.cursor_position.y
        )
        if DEBUG:
            display_surface.blit(
                self.player.cursor_image,
                cursor_position.move(
                    self.player.cursor_image.get_size()[0] / 2,
                    self.player.cursor_image.get_size()[1] / 2,
                ).move(dx, dy),
            )

        self.highlight_block()

        for el in self.interface_elements:
            el.draw()

    def highlight_block(self):
        display_surface = pygame.display.get_surface()
        dx = display_surface.get_rect().centerx - self.get_rect().centerx
        dy = display_surface.get_rect().centery - self.get_rect().centery
        cursor_position = self.player.rect.move(
            self.player.cursor_position.x, self.player.cursor_position.y
        )
        if self.player.mode == Mode.CONSTRUCTION:
            coords = self.player.get_cursor_coords()
            display_surface.blit(
                self.highlight,
                (coords[0] * BLOCK_SIZE + dx, coords[1] * BLOCK_SIZE + dy),
            )
            if DEBUG:
                log(self.world.get_block(coords))
        elif self.player.mode == Mode.COMBAT:
            pygame.draw.line(
                display_surface,
                "red",
                self.player.rect.move(dx, dy).center,
                cursor_position.move(dx, dy).center,
            )
