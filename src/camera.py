from itertools import product
from typing import Iterable

import pygame

from background import BackgroundResolver
from biome import Biome
from characters import BaseCharacter, Mode
from interface import BaseInterfaceElement
from log import log
from settings import BLOCK_SIZE, DEBUG
from world import World


class Camera:
    def __init__(
        self,
        size: tuple[int, int],
        player: BaseCharacter,
        world: World,
        interface_elements: Iterable[BaseInterfaceElement] | None = None,
        characters: list[BaseCharacter] | None = None,
    ) -> None:
        self.width, self.height = size
        self.rect = pygame.rect.Rect(0, 0, self.width, self.height)
        self.player = player
        self.world = world
        self.interface_elements = interface_elements or []
        self.characters = pygame.sprite.Group()
        if characters:
            self.characters.add(*characters)
        self.delta = (0, 0)
        self.background_resolver = BackgroundResolver()
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

        self.delta = rect.x - self.rect.x, rect.y - self.rect.y

        self.draw_background(self.player.position)
        self.draw_visible_area()
        self.draw_collectibles()
        self.draw_player()
        self.draw_characters()
        self.draw_bullets()

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

    def draw_background(self, position: pygame.math.Vector2):
        background = self.background_resolver.resolve(Biome(), position)
        self.display_surface.blit(background, (0, 0))

    def draw_visible_area(self):
        margin = 3

        for coords in product(
            range(
                self.rect.left // BLOCK_SIZE - margin,
                self.rect.right // BLOCK_SIZE + margin,
            ),
            range(
                self.rect.top // BLOCK_SIZE - margin,
                self.rect.bottom // BLOCK_SIZE + margin,
            ),
        ):
            block = self.world.get_block(coords)
            if block is not None:
                self.display_surface.blit(block.image, block.rect.move(self.delta))

    def draw_collectibles(self):
        self.display_surface.blits(
            tuple(
                (spr.collectible_image, spr.rect.move(self.delta))
                for spr in self.world.collectibles.sprites()
            )
        )

    def draw_player(self):
        if self.player.image is None or self.player.cursor_image is None:
            raise self.player.UnloadedObject
        self.display_surface.blit(self.player.image, self.player.rect.move(self.delta))
        cursor_position = self.player.rect.move(
            self.player.cursor_position.x, self.player.cursor_position.y
        )
        if DEBUG:
            self.display_surface.blit(
                self.player.cursor_image,
                cursor_position.move(
                    self.player.cursor_image.get_size()[0] / 2,
                    self.player.cursor_image.get_size()[1] / 2,
                ).move(self.delta),
            )
        if self.player.mode == Mode.CONSTRUCTION:
            coords = self.player.get_cursor_coords()
            self.display_surface.blit(
                self.highlight,
                (
                    coords[0] * BLOCK_SIZE + self.delta[0],
                    coords[1] * BLOCK_SIZE + self.delta[1],
                ),
            )
            if DEBUG:
                log(self.world.get_block(coords))
        elif self.player.mode == Mode.COMBAT:
            pygame.draw.line(
                self.display_surface,
                "red",
                self.player.rect.move(self.delta).center,
                cursor_position.move(self.delta).center,
            )

    def draw_characters(self):
        width, height = 50, 5
        for character in self.characters.sprites():
            if character.image is None:
                continue
            character_rect = character.rect.move(self.delta)
            self.display_surface.blit(character.image, character_rect)
            hp_bar = character_rect.move(-(width - character.size.x) / 2, -10)
            hp_bar.size = width, height
            hp_bar_border = hp_bar.copy()
            hp_bar.width = int(hp_bar.width * character.hp_percentage)
            pygame.draw.rect(self.display_surface, "red", hp_bar)
            pygame.draw.rect(self.display_surface, "white", hp_bar_border, 1)

    def draw_bullets(self):
        self.display_surface.blits(
            tuple(
                (spr.image, spr.rect.move(self.delta))
                for spr in self.world.bullets.sprites()
            )
        )
