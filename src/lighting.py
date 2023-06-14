from itertools import product
from math import radians, sin, sqrt

import pygame

from blocks import BaseBlock
from settings import BLOCK_SIZE, MAX_SURROUNDING_LENGTH
from utils.container import Container2d

Tetragon = tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]


class GlobalLight:
    def __init__(self) -> None:
        self.angle = 45


class ClusterDetector:
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

    def __init__(
        self,
        blocks: Container2d[BaseBlock],
        bounding_rect: pygame.rect.Rect,
    ) -> None:
        self.angle = 45
        self._checked_coords: set[tuple[int, int]] = set()
        self._checked_blocks: set[BaseBlock] = set()

        self.clusters: list[set[BaseBlock]] = []
        self.shadows: list[list[Tetragon]] = []
        self._starting_block: BaseBlock | None = None

        self._blocks = blocks

        start_x, start_y = bounding_rect.topleft
        end_x, end_y = bounding_rect.bottomright
        self.boundary_bottom_y = end_y
        self.start_x, self.start_y = (start_x // BLOCK_SIZE, start_y // BLOCK_SIZE)
        self.end_x, self.end_y = (end_x // BLOCK_SIZE, end_y // BLOCK_SIZE)

    def detect(self):
        # iterate over lines first
        block = None
        for y, x in product(
            range(self.start_y, self.end_y), range(self.start_x, self.end_x)
        ):
            coords = (x, y)
            if coords in self._checked_coords:
                continue

            block = self._blocks.get_element(coords)
            if block is None or block in self._checked_blocks:
                continue

            cluster, shadows = self._get_cluster(block)

            self._checked_blocks.update(cluster)
            self._checked_coords.update(b.coords for b in cluster)
            self.clusters.append(cluster)
            self.shadows.append(shadows)

    def _get_cluster(self, block: BaseBlock):
        self._starting_block = block

        rotating_index = 3
        direction_index = 3
        cluster: set[BaseBlock] = set()
        edges: list[Tetragon] = []
        vertex_1: tuple[int, int] = block.rect.center
        vertex_2: tuple[int, int] | None = None
        for _ in range(MAX_SURROUNDING_LENGTH):
            cluster.add(block)

            block, rotating_index = self._get_next_neighbor(self._blocks, block, rotating_index)  # type: ignore
            if block is None:
                break

            if direction_index != rotating_index:
                vertex_2 = block.rect.center
                vertex_3 = self._get_boundary_vertex(vertex_2)
                vertex_4 = self._get_boundary_vertex(vertex_1)
                edges.append((vertex_1, vertex_2, vertex_3, vertex_4))
                vertex_1 = vertex_2
                direction_index = rotating_index

            if self._starting_block == block:
                break

            # rotate: convert to opposite (+4) and next (+1)
            rotating_index += 5
        return cluster, edges

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
            if x > self.end_x or x < self.start_x or y > self.end_y or y < self.start_y:
                continue

            if (x, y) in self._checked_coords:
                continue

            _block = blocks.get_element((x, y))
            if _block is not None:
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
        y = self.boundary_bottom_y
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
            2,
        )
