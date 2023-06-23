from math import dist
from typing import Callable

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

        self.entrances: dict[Entrance, set[Coords]] = {}

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

        # scan from left to right
        for x in range(width):
            self._scan_col(x, height)

            # report progress
            # since it's expensive, do it every 5%
            step_progress = x / width
            if int(step_progress * 100) % 5 == 0:
                progress_callback(step_progress)

    def _scan_col(self, x: int, height: int):
        _curr = self.outer_layer[x]
        _next = self.outer_layer[x + 1]

        if _curr < _next:
            # scan for entrances in current col that go left
            entrances = self.find_entrances(x, _curr, _next + 1)
            for entrance in entrances:
                self._scan_entrance(entrance)

        if _curr > _next:
            # scan for entrances in next col that go right
            entrances = self.find_entrances(x + 1, _next, _curr + 1)
            for entrance in entrances:
                self._scan_entrance(entrance)

    def _generate_opacity_info(self, progress_callback: Callable[[float], None]):
        min_opacity = 0.8
        width, _ = self.opacity.size
        for x in range(width):
            first_non_empty = self.outer_layer[x]
            for y in range(first_non_empty + 1):
                self._penetrate_light((x, y), 1)

            # report progress
            # since it's expensive, do it every 5%
            step_progress = x / width
            if int(step_progress * 100) % 5 == 0:
                progress_callback(step_progress)

        for entrance, points in self.entrances.items():
            for coords in points:
                opacity = min_opacity - self._get_distance_to_entrance(
                    coords, entrance
                ) / self._get_max_distance(entrance)
                self._penetrate_light(coords, opacity)

    def _penetrate_light(self, coords: Coords, multiplier: float = 1):
        (x, y) = coords
        self.set_opacity(coords, 1 * multiplier, True)
        layers = {
            0.6: [
                (x, y + 1),
                (x, y - 1),
                (x + 1, y),
                (x - 1, y),
            ],
            0.2: [
                (x + 1, y + 1),
                (x - 1, y - 1),
                (x + 1, y - 1),
                (x - 1, y + 1),
            ],
        }
        for opacity, points in layers.items():
            for coords in points:
                if self._blocks.get_element(coords):
                    self.set_opacity(coords, opacity * multiplier, True)

    def get_opacity(self, coords: Coords) -> int:
        _opacity = self.opacity.get_element(coords)
        if _opacity is None:
            return 0
        return int(_opacity * 255)

    def set_opacity(self, coords: Coords, opacity: float, trunc_max=False):
        opacity = min(1, opacity)
        if trunc_max:
            existing_opacity = self.opacity.get_element(coords) or 0
            opacity = max(existing_opacity, opacity)

        try:
            self.opacity.set_element(coords, opacity)
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

    def _scan_entrance(self, entrance: Entrance):
        top, bottom = entrance
        x = top[0]
        coords_to_check: set[Coords] = {(x, y) for y in range(top[1] + 1, bottom[1])}
        already_checked: set[Coords] = set()

        self.entrances[entrance] = set()
        while coords_to_check:
            coords = coords_to_check.pop()
            already_checked.add(coords)

            self.entrances[entrance].add(coords)

            self._next_coords(coords, coords_to_check, already_checked, entrance)

    @staticmethod
    def _get_max_distance(entrance: Entrance):
        top, bottom = entrance
        _, top_y = top
        _, bottom_y = bottom
        return abs(bottom_y - top_y)

    @classmethod
    def _get_distance_to_entrance(cls, coords: Coords, entrance: Entrance):
        _, y = coords
        top, bottom = entrance
        entrance_x = top[0]
        top_y = top[1]
        bottom_y = bottom[1]
        if y > bottom_y:
            ref = (entrance_x, bottom_y)
        elif y < top_y:
            ref = (entrance_x, top_y)
        else:
            ref = (entrance_x, y)

        distance = dist(ref, coords)
        return distance

    def _next_coords(
        self,
        coords: Coords,
        coords_to_check: set[Coords],
        already_checked: set[Coords],
        entrance: Entrance,
    ):
        for neighbor in neighbors(coords):
            if neighbor not in already_checked and self._get_distance_to_entrance(
                neighbor, entrance
            ) <= self._get_max_distance(entrance):
                if self._blocks.get_element(neighbor) is not None:
                    self.entrances[entrance].add(coords)
                    already_checked.add(neighbor)
                else:
                    coords_to_check.add(neighbor)

    def update_region(self, coords: Coords, place=True):
        _, height = self.opacity.size
        x, y = coords
        print("ok")
        if place:
            if y < self.outer_layer[x]:
                self.outer_layer[x] = y
                ...

            ...
        else:
            ...
        for i in range(3):
            self._scan_col(x - 1 + i, height)
