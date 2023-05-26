from typing import Iterable

import pygame

from characters import BaseCharacter, Mode
from interface import BaseInterfaceElement
from log import log
from settings import BLOCK_SIZE, DEBUG
from world import BaseWorld


class Camera:
    def __init__(
        self,
        size: tuple[int, int],
        player: BaseCharacter,
        world: BaseWorld,
        interface_elements: Iterable[BaseInterfaceElement] | None = None,
        characters: list[BaseCharacter] | None = None,
    ) -> None:
        self.width, self.height = size
        self.rect = pygame.rect.Rect(0, 0, self.width, self.height)
        self.player = player
        self.world = world
        self.interface_elements = interface_elements or []
        self.characters = characters or []
        self.delta_x, self.delta_y = (0, 0)
        self.delta = pygame.math.Vector2()
        self._setup()

    def _setup(self):
        self.highlight = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()
        self.highlight.fill((0, 0, 0, 0))
        pygame.draw.rect(self.highlight, "red", (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2, 4)
        self.display_surface = pygame.display.get_surface()

    def update(self):
        self.update_rect()

        rect = self.display_surface.get_rect()
        self.delta_x = rect.x - self.rect.x
        self.delta_y = rect.y - self.rect.y

        self.display_surface.fill("black")

        self.draw_visibility_buffer()
        self.draw_collectibles()
        self.draw_player()
        self.draw_characters()

        for element in self.interface_elements:
            element.draw()

    def update_rect(self):
        self.rect.center = self.player.rect.center

        top = self.player.rect.centery - self.height / 2
        self.rect.top = max(top, 0)  # type: ignore

        bottom = self.player.rect.centery + self.height / 2
        if bottom >= self.world.rect.height:
            self.rect.bottom = self.world.rect.height

        left = self.player.rect.centerx - self.width / 2
        self.rect.left = max(left, 0)  # type: ignore

        right = self.player.rect.centerx + self.width / 2
        if right >= self.world.rect.width:
            self.rect.right = self.world.rect.width

    def draw_visibility_buffer(self):
        self.display_surface.blits(
            tuple(
                (spr.image, spr.rect.move(self.delta_x, self.delta_y))
                for spr in self.world.visibility_buffer.sprites()
            )
        )

    def draw_collectibles(self):
        self.display_surface.blits(
            tuple(
                (spr.collectible_image, spr.rect.move(self.delta_x, self.delta_y))
                for spr in self.world.collectibles.sprites()
            )
        )

    def draw_player(self):
        if self.player.image is None or self.player.cursor_image is None:
            raise self.player.UnloadedObject
        self.display_surface.blit(
            self.player.image, self.player.rect.move(self.delta_x, self.delta_y)
        )
        cursor_position = self.player.rect.move(
            self.player.cursor_position.x, self.player.cursor_position.y
        )
        if DEBUG:
            self.display_surface.blit(
                self.player.cursor_image,
                cursor_position.move(
                    self.player.cursor_image.get_size()[0] / 2,
                    self.player.cursor_image.get_size()[1] / 2,
                ).move(self.delta_x, self.delta_y),
            )
        if self.player.mode == Mode.CONSTRUCTION:
            coords = self.player.get_cursor_coords()
            self.display_surface.blit(
                self.highlight,
                (
                    coords[0] * BLOCK_SIZE + self.delta_x,
                    coords[1] * BLOCK_SIZE + self.delta_y,
                ),
            )
            if DEBUG:
                log(self.world.get_block(coords))
        elif self.player.mode == Mode.COMBAT:
            pygame.draw.line(
                self.display_surface,
                "red",
                self.player.rect.move(self.delta_x, self.delta_y).center,
                cursor_position.move(self.delta_x, self.delta_y).center,
            )

    def draw_characters(self):
        width, height = 50, 5
        for character in self.characters:
            if character.image is None:
                continue
            character_rect = character.rect.move(self.delta_x, self.delta_y)
            self.display_surface.blit(character.image, character_rect)
            hp_bar = character_rect.move(-(width - character.size.x) / 2, -10)
            hp_bar.size = width, height
            hp_bar_border = hp_bar.copy()
            hp_bar.width = int(hp_bar.width * character.hp_percentage)
            pygame.draw.rect(self.display_surface, "red", hp_bar)
            pygame.draw.rect(self.display_surface, "white", hp_bar_border, 1)
