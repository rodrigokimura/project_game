from itertools import product
from typing import Iterable

import pygame
from numpy import divide

from background import BackgroundResolver
from biome import Biome
from characters import BaseCharacter, Mode
from colors import Color, InterfaceColor
from interface import BaseInterfaceElement
from lighting import ShadowCaster
from log import log
from settings import BLOCK_SIZE, DEBUG
from utils.blit import blit_multiple
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
        self.position = pygame.math.Vector2()
        self.player = player
        self.world = world
        self.interface_elements = interface_elements or []
        self.characters = pygame.sprite.Group()
        if characters:
            self.characters.add(*characters)
        self.background_resolver = BackgroundResolver()
        self.shadow_caster = ShadowCaster(self.world.blocks, self.rect)
        self._setup()

    def _setup(self):
        self.highlight = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()
        self.highlight.fill(Color.TRANSPARENT)
        pygame.draw.rect(
            self.highlight,
            InterfaceColor.BLOCK_CURSOR,
            (0, 0, BLOCK_SIZE, BLOCK_SIZE),
            2,
            4,
        )
        self.display_surface = pygame.display.get_surface()

    def update(self):
        self._update_rect()
        self._update_position()
        self._draw_background(self.player.position)
        self._draw_shadows(self.world.relative_time)
        self._draw_visible_area()
        self._draw_collectibles()
        self._draw_player()
        self._draw_characters()
        self._draw_bullets()
        self._draw_particles()
        self._draw_interface_elements()

    def _update_rect(self):
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

    def _update_position(self):
        self.position.update(self.rect.topleft)

    def _draw_background(self, position: pygame.math.Vector2):
        background = self.background_resolver.resolve(Biome(), position)
        self.display_surface.blit(background, (0, 0))

    def _draw_visible_area(self):
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
                self.display_surface.blit(block.image, block.rect.move(-self.position))

    def _draw_collectibles(self):
        blit_multiple(
            self.display_surface,
            self.world.collectibles,
            -self.position,
            "collectible_image",
        )

    def _draw_player(self):
        if self.player.image is None or self.player.cursor_image is None:
            raise self.player.UnloadedObject

        self.display_surface.blit(
            self.player.image, self.player.rect.move(-self.position)
        )

        if DEBUG:
            self.display_surface.blit(
                self.player.cursor_image,
                (
                    self.player.position
                    + self.player.cursor_position
                    - self.position
                    - divide(self.player.cursor_image.get_size(), 2)
                ),
            )
        if self.player.mode == Mode.CONSTRUCTION:
            self._draw_block_cursor()
        elif self.player.mode == Mode.COMBAT:
            self._draw_aim_assist()

    def _draw_block_cursor(self):
        if not self.player.cursor_position:
            return
        self.display_surface.blit(
            self.highlight,
            (self.player.position + self.player.cursor_position)
            // BLOCK_SIZE
            * BLOCK_SIZE
            - self.position,
        )
        if DEBUG:
            log(self.world.get_block(self.player.get_cursor_coords()))

    def _draw_aim_assist(self):
        angle_deviation = (1 - self.player.shooting_accuracy) * 90
        _, cursor_angle = self.player.cursor_position.as_polar()
        aim_max = pygame.math.Vector2.from_polar(
            (self.player.shooting_range, cursor_angle + angle_deviation)
        )
        aim_min = pygame.math.Vector2.from_polar(
            (self.player.shooting_range, cursor_angle - angle_deviation)
        )
        if aim_min and aim_max and self.player.cursor_position:
            pygame.draw.line(
                self.display_surface,
                InterfaceColor.AIM_ASSIST_LINE,
                self.player.rect.move(-self.position).center,
                self.rect.move(aim_max).move(-self.position).center,
            )
            pygame.draw.line(
                self.display_surface,
                InterfaceColor.AIM_ASSIST_LINE,
                self.player.rect.move(-self.position).center,
                self.rect.move(aim_min).move(-self.position).center,
            )
            pygame.draw.circle(
                self.display_surface,
                InterfaceColor.AIM_ASSIST_LINE,
                self.player.rect.move(-self.position).center,
                self.player.shooting_range,
                1,
            )

    def _draw_characters(self):
        width, height = 50, 5
        for character in self.characters.sprites():
            if character.image is None:
                continue
            character_rect = character.rect.move(-self.position)
            self.display_surface.blit(character.image, character_rect)
            hp_bar = character_rect.move(-(width - character.size.x) / 2, -10)
            hp_bar.size = width, height
            hp_bar_border = hp_bar.copy()
            hp_bar.width = int(hp_bar.width * character.hp_percentage)
            pygame.draw.rect(self.display_surface, InterfaceColor.HEALTH_POINTS, hp_bar)
            pygame.draw.rect(
                self.display_surface,
                InterfaceColor.HEALTH_POINTS_BAR_BORDER,
                hp_bar_border,
                1,
            )

    def _draw_bullets(self):
        blit_multiple(self.display_surface, self.world.bullets, -self.position)

    def _draw_particles(self):
        self.world.particle_manager.draw(self.display_surface, -self.position)

    def _draw_interface_elements(self):
        for element in self.interface_elements:
            element.draw()

    def _draw_shadows(self, relative_time: float):
        self.shadow_caster.detect(-self.position, relative_time)
        # if DEBUG:
        #     try:
        #         colors = ("red", "blue", "green", "yellow", "magenta", "cyan")
        #         for i in range(len(self.shadow_caster.clusters)):
        #             color = colors[i % len(colors)]
        #             # cluster_detector.paint_cluster(i, -self.position, color)
        #             for shadow in self.shadow_caster.shadows[i]:
        #                 self.shadow_caster.paint_shadow(shadow, -self.position, color)
        #         print(f"{len(self.shadow_caster.clusters)} clusters detected")
        #     except IndexError:
        #         ...
