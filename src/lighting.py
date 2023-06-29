import copy
import math
from itertools import product
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
        self.opacity: Container2d[int] = Container2d(blocks.size)
        self.opacity._container = [
            [0 for _ in range(self.opacity.size[1])]
            for _ in range(self.opacity.size[0])
        ]
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

        self.shadows: dict[Entrance, set[Coords]] = {}

    def setup(self):
        self._shadow_img = pygame.surface.Surface(
            (BLOCK_SIZE, BLOCK_SIZE)
        ).convert_alpha()

    def _detect_outer_layer(self, progress_callback: Callable[[float], None]):
        width, height = self.opacity.shape

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
        width, _ = self.opacity.shape

        # scan from left to right
        for x in range(width):
            self._scan_col(x)

            # report progress
            # since it's expensive, do it every 5%
            step_progress = x / width
            if int(step_progress * 100) % 5 == 0:
                progress_callback(step_progress)

    def _scan_col(self, x: int):
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
        width, _ = self.opacity.shape
        for x in range(width):
            for y in range(self.outer_layer[x] + 1):
                self._penetrate_light((x, y), 1)

            # report progress
            # since it's expensive, do it every 5%
            step_progress = x / width
            if int(step_progress * 100) % 5 == 0:
                progress_callback(step_progress)

        self._generate_opacity_for_entrances()

    def _generate_opacity_for_entrances(self):
        max_opacity = 0.8
        for entrance, shadow in self.shadows.items():
            for coords in shadow:
                self.opacity[coords] = 0
                for x, y in neighbors(coords):
                    if y > self.outer_layer[x] + 1:
                        self.opacity[x, y] = 0

        for entrance, shadow in self.shadows.items():
            for coords in shadow:
                opacity = max_opacity - self._get_distance_to_entrance(
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
            for point in points:
                if self._blocks.get_element(point):
                    self.set_opacity(point, opacity * multiplier, True)

    def _reverse_light_penetration(self, coords: Coords):
        (x, y) = coords
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
        self.set_opacity(coords, 0, False)
        for _, points in layers.items():
            for point in points:
                self.set_opacity(point, 0, False)

    def get_opacity(self, coords: Coords) -> int:
        return self.opacity[coords] or 0

    def set_opacity(self, coords: Coords, opacity: float, trunc_max=False):
        opacity *= 255
        if trunc_max:
            existing_opacity = self.opacity[coords] or 0
            opacity = max(existing_opacity, opacity)

        try:
            self.opacity[coords] = opacity
        except IndexError:
            ...

    def add_opacity(self, coords: Coords, opacity: float):
        _opacity = self.opacity[coords] or 0
        _opacity += opacity
        self.set_opacity(coords, _opacity)

    def cast(
        self,
        coords: Coords,
        offset: pygame.math.Vector2,
        display: pygame.surface.Surface,
        opacity: int,
    ):
        _opacity = (self.opacity[coords] or 0) + opacity
        if _opacity < 255:
            _opacity = 255 - _opacity
            self._shadow_img.set_alpha(_opacity)
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
                # NOTE: important when there is a gap of 2 tiles (or more) in height
                # between the entrance col and the next surface col
                if y == to_y and empty_count > 1 and top is not None:
                    entrances.add((top, (x, y)))

                empty_count += 1

        return entrances

    def _scan_entrance(self, entrance: Entrance):
        top, bottom = entrance
        x = top[0]
        coords_to_check: set[Coords] = {
            (x, y) for y in range(top[1] + 1, bottom[1] - 1)
        }
        already_checked: set[Coords] = set()

        self.shadows[entrance] = set()
        while coords_to_check:
            coords = coords_to_check.pop()
            already_checked.add(coords)

            self.shadows[entrance].add(coords)

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
            x, y = neighbor
            if y <= self.outer_layer[x]:
                continue
            if neighbor not in already_checked and self._get_distance_to_entrance(
                neighbor, entrance
            ) <= self._get_max_distance(entrance):
                if self._blocks.get_element(neighbor) is not None:
                    self.shadows[entrance].add(coords)
                    already_checked.add(neighbor)
                else:
                    coords_to_check.add(neighbor)

    def update_region(self, coords: Coords, place=True):
        _, height = self.opacity.shape
        x, y = coords
        if place:
            if y < self.outer_layer[x]:
                # revert shadow of prev outer layer
                for i in range(y, self.outer_layer[x] + 1):
                    self._reverse_light_penetration((x, i))
                # update outer layer
                self.outer_layer[x] = y
                # reapply shadow for outer layer
                for i in range(3):
                    for _y in range(self.outer_layer[x - 1 + i] + 1):
                        self._penetrate_light((x - 1 + i, _y), 1)
        else:
            if y == self.outer_layer[x]:
                for _y in range(height + 1):
                    self._penetrate_light((x, _y), 1)
                    if self._blocks.get_element((x, _y)):
                        self.outer_layer[x] = _y
                        break

        modified_entrances: list[Entrance] = []
        for entrance, shadow in self.shadows.items():
            for _coords in shadow:
                self.opacity[_coords] = 0
                for _x, _y in neighbors(_coords):
                    if _y > self.outer_layer[_x] + 1:
                        self.opacity[_x, _y] = 0

            # check if an entrance is being modified
            _x = entrance[0][0]
            if x - 1 <= _x <= x + 1:
                modified_entrances.append(entrance)

        deleted_entrance_cols: set[int] = set()
        for entrance in modified_entrances:
            del self.shadows[entrance]
            deleted_entrance_cols.add(entrance[0][0])

        for col in deleted_entrance_cols:
            # rescanning surrounding, important when expanding monocol entrance
            for i in range(3):
                self._scan_col(col - 1 + i)
                for _y in range(self.outer_layer[x - 1 + i] + 1):
                    self._penetrate_light((x - 1 + i, _y), 1)

        for i in range(3):
            self._scan_col(x - 1 + i)
            for _y in range(self.outer_layer[x - 1 + i] + 1):
                self._penetrate_light((x - 1 + i, _y), 1)

        self._generate_opacity_for_entrances()


class RadialLight:
    def __init__(self, length: int, blocks: Container2d[BaseBlock]) -> None:
        self._blocks = blocks
        self.length = length
        self.ray_count = self._get_ray_count()
        self.opacity: Container2d[int] = Container2d((2 * length + 1, 2 * length + 1))

        self._initial_rays_state = [True for _ in range(self.ray_count + 1)]

        self.position = pygame.math.Vector2()
        self._current_coords: Coords = (0, 0)

    def _get_ray_count(self):
        circle_length = 2 * math.pi * self.length * BLOCK_SIZE
        return int(circle_length // BLOCK_SIZE)

    def update(self):
        coords = int(self.position.x // BLOCK_SIZE), int(self.position.y // BLOCK_SIZE)
        if coords != self._current_coords:
            self._current_coords = coords
            self._update_opacity()

    def _update_opacity(self):
        self.opacity.empty()

        rays = copy.copy(self._initial_rays_state)
        for layer, ray in product(range(self.length), range(self.ray_count + 1)):
            # check for occlusion
            if rays[ray] is False:
                continue
            angle = (ray) / self.length
            length = (layer + 1) * BLOCK_SIZE

            x, y = (length * math.sin(angle), length * math.cos(angle))
            real_coords = (self.position.x + x, self.position.y + y)

            # occlude next tiles when block is found for this ray
            rays[ray] = (
                self._blocks.get_element(
                    (
                        int(real_coords[0] // BLOCK_SIZE),
                        int(real_coords[1] // BLOCK_SIZE),
                    )
                )
                is None
            )
            x, y = int(x // BLOCK_SIZE), int(y // BLOCK_SIZE)
            opacity = 1 - length / (self.length * BLOCK_SIZE)
            self.opacity[x, y] = opacity * 255

    def in_range(self, coords: Coords):
        return math.dist((0, 0), coords) <= self.length + 1

    def get_opacity(self, coords: Coords) -> int:
        coords = (
            int(coords[0] - (self.position.x // BLOCK_SIZE)),
            int(coords[1] - (self.position.y // BLOCK_SIZE)),
        )
        if self.in_range(coords):
            return self.opacity[coords] or 0
        return 0
