from itertools import product
from math import radians, sin, sqrt

import pygame

from blocks import BaseBlock, Spike, Tree
from settings import BLOCK_SIZE, MAX_SURROUNDING_LENGTH
from utils.container import Container2d

Tetragon = tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]


class GlobalLight:
    def __init__(self) -> None:
        self.angle = 45


class ShadowCaster:
    NEIGHBORS = (
        (-1, -1),
        (0, -1),
        (1, -1),
        (1, 0),
        (1, 1),
        (0, 1),
        (-1, 1),
        (-1, 0),
    )
    BLOCKS_TO_IGNORE = (Tree, Spike)

    def __init__(
        self,
        blocks: Container2d[BaseBlock],
        boundary: pygame.rect.Rect,
    ) -> None:
        self.angle = 45
        self._checked_coords: set[tuple[int, int]] = set()
        self._checked_blocks: set[BaseBlock] = set()

        self.clusters: list[set[BaseBlock]] = []
        self.shadows: list[list[Tetragon]] = []

        self._blocks = blocks
        self._boundary = boundary

        self._boundary_bottom_y: int
        self._start_x: int
        self._start_y: int
        self._end_x: int
        self._end_y: int

    def detect(self, offset: pygame.math.Vector2, relative_time: float):
        self._reset()
        self._update_coords()
        self._update_angle(relative_time)
        # iterate over lines first
        block = None
        for y, x in product(
            range(self._start_y, self._end_y), range(self._start_x, self._end_x)
        ):
            coords = (x, y)
            if coords in self._checked_coords:
                continue

            block = self._blocks.get_element(coords)
            if (
                block is None
                or block in self._checked_blocks
                or isinstance(block, self.BLOCKS_TO_IGNORE)
            ):
                continue

            cluster, shadows = self._get_cluster(block, offset)

            self._checked_blocks.update(cluster)
            self._checked_coords.update(b.coords for b in cluster)
            self.clusters.append(cluster)
            self.shadows.append(shadows)

    def _reset(self):
        self._checked_coords.clear()
        self._checked_blocks.clear()
        self.clusters.clear()
        self.shadows.clear()

    def _update_coords(self):
        _pad = 1
        start_x, start_y = self._boundary.topleft
        end_x, end_y = self._boundary.bottomright
        self._boundary_bottom_y = end_y
        self._start_x, self._start_y = (
            start_x // BLOCK_SIZE - _pad,
            start_y // BLOCK_SIZE - _pad,
        )
        self._end_x, self._end_y = (
            end_x // BLOCK_SIZE + _pad,
            end_y // BLOCK_SIZE + _pad,
        )

    def _update_angle(self, relative_time: float):
        print(relative_time)
        max_angle = 45
        self.angle = (relative_time * 2 - 1) * max_angle
        print(self.angle)

    def _get_cluster(self, block: BaseBlock, offset: pygame.math.Vector2):
        _start = block
        _current = block
        _next = block

        rotating_index = 3
        direction_index = 3
        cluster: set[BaseBlock] = set()
        shadows: list[Tetragon] = []
        vertex_1: tuple[int, int] = _current.rect.center
        vertex_2: tuple[int, int] = _current.rect.center
        for _ in range(MAX_SURROUNDING_LENGTH):
            cluster.add(_current)

            _next, rotating_index = self._get_next_neighbor(self._blocks, _current, rotating_index)  # type: ignore
            if _next is None:
                break

            if direction_index != rotating_index:
                vertex_2 = _current.rect.center
                vertex_3 = self._get_boundary_vertex(vertex_2)
                vertex_4 = self._get_boundary_vertex(vertex_1)
                shadow = (vertex_1, vertex_2, vertex_3, vertex_4)
                shadows.append(shadow)
                self.paint_shadow(shadow, offset, "black")
                vertex_1 = vertex_2
                direction_index = rotating_index

            if _start == _next:
                vertex_2 = _next.rect.center
                vertex_3 = self._get_boundary_vertex(vertex_2)
                vertex_4 = self._get_boundary_vertex(vertex_1)
                shadows.append((vertex_1, vertex_2, vertex_3, vertex_4))
                break

            _current = _next

            # rotate: convert to opposite (+4) and next (+1)
            rotating_index += 5
        return cluster, shadows

    def _get_next_neighbor(
        self,
        blocks: Container2d[BaseBlock],
        block: BaseBlock,
        index: int,
    ):
        for i in range(8):
            _index = index + i
            _index %= 8
            (x, y) = self._get_neighbor_coords(block.coords, _index)

            # handle edge cases
            if (
                x > self._end_x
                or x < self._start_x
                or y > self._end_y
                or y < self._start_y
            ):
                continue

            if (x, y) in self._checked_coords:
                continue

            _block = blocks.get_element((x, y))
            if _block is not None and not isinstance(_block, self.BLOCKS_TO_IGNORE):
                return _block, _index
            self._checked_coords.add((x, y))
        return (None, 0)

    def _get_neighbor_coords(self, coords: tuple[int, int], index: int):
        """
        0 1 2
        7 x 3
        6 5 4
        """
        x_1, y_1 = coords
        x_2, y_2 = self.NEIGHBORS[index % 8]
        return (x_1 + x_2, y_1 + y_2)

    def _get_boundary_vertex(self, vertex: tuple[int, int]):
        x_0, y_0 = vertex
        y = self._boundary_bottom_y
        x = int(((y - y_0) / sqrt(1 / pow(sin(radians(self.angle)) - 1, 2))) + x_0)
        return (x, y)

    def paint_cluster(self, index: int, offset: pygame.math.Vector2, color):
        for block in self.clusters[index]:
            display = pygame.display.get_surface()
            pygame.draw.rect(display, color, block.rect.move(offset))

    def paint_shadow(self, vertices: Tetragon, offset: pygame.math.Vector2, color):
        display = pygame.display.get_surface()
        pygame.draw.polygon(
            display,
            color,
            tuple((pygame.math.Vector2(v) * 1) + offset for v in vertices),
        )
