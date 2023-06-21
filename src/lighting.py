from typing import Callable

import pygame

from blocks import BaseBlock
from settings import BLOCK_SIZE
from utils.container import Container2d


class ShadowCaster:
    def __init__(
        self,
        blocks: Container2d[BaseBlock],
        boundary: pygame.rect.Rect,
    ) -> None:
        self.opacity: Container2d[float] = Container2d(blocks.size)
        self.outer_layer: list[int] = [0 for _ in range(blocks.size[0])]

        self._blocks = blocks
        self._boundary = boundary

        self._boundary_bottom_y: int
        self._start_x: int
        self._start_y: int
        self._end_x: int
        self._end_y: int
        self._pad = -1
        self._shadow_img: pygame.surface.Surface

    def setup(self):
        self._shadow_img = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()

    def _detect_outer_layer(self, progress_callback: Callable[[float], None]):
        width, height = self.opacity.size
        total_blocks = width * height
        i = 0
        # scan from left to right
        for x in range(width):
            for y in range(height):
                coords = (x, y)
                block = self._blocks.get_element(coords)
                if block is not None:
                    self.outer_layer[x] = y
                    break

                # report progress
                # since it's expensive, do it every 1%
                i += 1
                step_progress = i / total_blocks
                if i % (total_blocks // 100) == 0:
                    progress_callback(step_progress)

    def _generate_opacity_info(self, progress_callback: Callable[[float], None]):
        width, _ = self.opacity.size
        for x in range(width):
            first_non_empty = self.outer_layer[x]
            for y in range(first_non_empty + 1):
                self._light_point((x, y))

            # report progress
            # since it's expensive, do it every 1%
            step_progress = x / width
            if x % (width // 100) == 0:
                progress_callback(step_progress)

    def _light_point(self, coords: tuple[int, int]):
        layer_1 = 0.1
        layer_2 = 0.05
        (x, y) = coords
        self.set_opacity(coords, 1)
        for i in range(3):
            self.add_opacity((x - 1 + i, y - 2), layer_2)
            self.add_opacity((x - 1 + i, y + 2), layer_2)

            self.add_opacity((x - 2, y - 1 + i), layer_2)
            self.add_opacity((x + 2, y - 1 + i), layer_2)

            for j in range(3):
                self.add_opacity((x - 1 + i, y - 1 + j), layer_1)

    def get_opacity(self, coords: tuple[int, int]) -> int:
        _opacity = self.opacity.get_element(coords)
        if _opacity is None:
            return 0
        return int(_opacity * 255)

    def set_opacity(self, coords: tuple[int, int], opacity: float):
        try:
            self.opacity.set_element(coords, min(1, opacity))
        except IndexError:
            ...

    def add_opacity(self, coords: tuple[int, int], opacity: float):
        _opacity = self.opacity.get_element(coords) or 0
        _opacity += opacity
        self.set_opacity(coords, _opacity)

    def cast(
        self,
        coords: tuple[int, int],
        offset: pygame.math.Vector2,
        display: pygame.surface.Surface,
    ):
        opacity = self.get_opacity(coords)
        if opacity < 255:
            opacity = 255 - opacity
            self._shadow_img.set_alpha(opacity)
            display.blit(
                self._shadow_img,
                (coords[0] * BLOCK_SIZE + offset.x, coords[1] * BLOCK_SIZE + offset.y),
            )
