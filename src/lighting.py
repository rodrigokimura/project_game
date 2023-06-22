from math import dist
from typing import Callable, Literal

import pygame

from blocks import BaseBlock
from settings import BLOCK_SIZE
from utils.container import Container2d
from utils.coords import Coords, neighbors

Entrance = tuple[Coords, Coords]


class ShadowCaster:
    def __init__(
        self,
        blocks: Container2d[BaseBlock],
        boundary: pygame.rect.Rect,
    ) -> None:
        self.opacity: Container2d[float] = Container2d(blocks.size)
        self.outer_layer: list[int] = [0 for _ in range(blocks.size[0] + 1)]

        self._blocks = blocks
        self._boundary = boundary

        self._boundary_bottom_y: int
        self._start_x: int
        self._start_y: int
        self._end_x: int
        self._end_y: int
        self._pad = -1
        self._shadow_img: pygame.surface.Surface

        self.entrances_to_left: set[Entrance] = set()
        self.entrances_to_right: set[Entrance] = set()

    def setup(self):
        self._shadow_img = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()

    def _detect_outer_layer(self, progress_callback: Callable[[float], None]):
        width, height = self.opacity.size

        # scan from left to right
        for x in range(width):
            for y in range(height):
                coords = (x, y)
                block = self._blocks.get_element(coords)
                if block is not None:
                    self.outer_layer[x] = y
                    break

            # report progress
            # since it's expensive, do it every 5%
            step_progress = x / width
            if int(step_progress * 100) % 5 == 0:
                progress_callback(step_progress)

    def _generate_light_entrances_info(
        self, progress_callback: Callable[[float], None]
    ):
        width, height = self.opacity.size
        entrances = set()

        # scan from left to right
        for x in range(width):
            _curr = self.outer_layer[x]
            _next = self.outer_layer[x + 1]

            if _curr < _next:
                # scan for entrances in current col that go left
                entrances = self.find_entrances(x, _curr, height)
                for entrance in entrances:
                    self.scan_entrance(entrance, "left")

                self.entrances_to_left.update(entrances)

            if _curr > _next:
                # scan for entrances in next col that go right
                entrances = self.find_entrances(x + 1, _next, _curr)
                for entrance in entrances:
                    self.scan_entrance(entrance, "right")

                self.entrances_to_right.update(entrances)

            # report progress
            # since it's expensive, do it every 5%
            step_progress = x / width
            if int(step_progress * 100) % 5 == 0:
                progress_callback(step_progress)

        print(f"Left: {self.entrances_to_left}")
        print(f"Right: {self.entrances_to_right}")

    def _generate_opacity_info(self, progress_callback: Callable[[float], None]):
        width, _ = self.opacity.size
        for x in range(width):
            first_non_empty = self.outer_layer[x]
            for y in range(first_non_empty + 1):
                self._light_point((x, y))

            # report progress
            # since it's expensive, do it every 5%
            step_progress = x / width
            if int(step_progress * 100) % 5 == 0:
                progress_callback(step_progress)

    def _light_point(self, coords: Coords):
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

    def get_opacity(self, coords: Coords) -> int:
        _opacity = self.opacity.get_element(coords)
        if _opacity is None:
            return 0
        return int(_opacity * 255)

    def set_opacity(self, coords: Coords, opacity: float):
        try:
            self.opacity.set_element(coords, min(1, opacity))
        except IndexError:
            ...

    def add_opacity(self, coords: Coords, opacity: float):
        _opacity = self.opacity.get_element(coords) or 0
        _opacity += opacity
        self.set_opacity(coords, _opacity)

    def cast(
        self,
        coords: Coords,
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

    def find_entrances(self, x: int, from_y: int, to_y: int):
        entrances: set[Entrance] = set()
        top: Coords | None = None
        bottom: Coords | None = None
        empty_count = 0

        for y in range(from_y, to_y + 1):
            block = self._blocks.get_element((x, y))
            if block is not None:
                if top is None:
                    top = block.coords
                    empty_count = 0

                if bottom is None:
                    bottom = block.coords

                    # need at least 1 non-empty tile between top and bottom to define an entrance
                    if empty_count > 1:
                        entrances.add((top, bottom))
                        top = block.coords
                        empty_count = 0
                    bottom = None
            else:
                empty_count += 1
        return entrances

    def scan_entrance(
        self, entrance: Entrance, direction: Literal["left"] | Literal["right"]
    ):
        top, bottom = entrance
        x = top[0]
        coords_to_check: set[Coords] = {(x, y) for y in range(top[1], bottom[1] + 1)}
        already_checked: set[Coords] = set()
        if direction == "left":
            while coords_to_check:
                coords = coords_to_check.pop()
                already_checked.add(coords)

                # TODO: add opcity info logic
                self._next_coords(coords, coords_to_check, already_checked, entrance)

        elif direction == "right":
            ...
        else:
            raise NotImplementedError

    @staticmethod
    def _get_max_distance(entrance: Entrance):
        top, bottom = entrance
        _, top_y = top
        _, bottom_y = bottom
        return abs(bottom_y - top_y)

    @classmethod
    def _is_close_to_entrance(cls, coords: Coords, entrance: Entrance):
        top, bottom = entrance
        mid_point = (top[0], (top[1] + bottom[1]) // 2)
        distance = dist(mid_point, coords)
        return distance <= cls._get_max_distance(entrance)

    def _next_coords(
        self,
        coords: Coords,
        coords_to_check: set[Coords],
        already_checked: set[Coords],
        entrance: Entrance,
    ):
        for neighbor in neighbors(coords):
            if (
                neighbor not in already_checked
                and self._is_close_to_entrance(neighbor, entrance)
                and self._blocks.get_element(neighbor) is None
            ):
                coords_to_check.add(neighbor)
