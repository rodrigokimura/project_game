from itertools import product

import pygame

from blocks import BaseBlock
from settings import BLOCK_SIZE, MAX_SURROUNDING_LENGTH
from utils.container import Container2d


class Light:
    ...


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
        self._checked_coords: set[tuple[int, int]] = set()
        self._checked_blocks: set[BaseBlock] = set()

        self.clusters: list[set[BaseBlock]] = []
        self._starting_block: BaseBlock | None = None

        self._blocks = blocks

        start_x, start_y = bounding_rect.topleft
        end_x, end_y = bounding_rect.bottomright
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

            cluster = self._get_cluster(block)

            self._checked_blocks.update(cluster)
            self._checked_coords.update(b.coords for b in cluster)
            self.clusters.append(cluster)

            # TODO: avoid detecting clusters inside clusters
            # if len(self.clusters) > 3:
            #     break

    def _get_cluster(self, block: BaseBlock):
        self._starting_block = block

        index = 3
        cluster: set[BaseBlock] = set()
        for _ in range(MAX_SURROUNDING_LENGTH):
            cluster.add(block)
            block, index = self._get_next_neighbor(self._blocks, block, index)  # type: ignore
            if block is None:
                break

            if self._starting_block == block:
                break
            # convert to opposite (+4) and next (+1)
            index += 5
        return cluster

    def _get_next_neighbor(
        self,
        blocks: Container2d[BaseBlock],
        block: BaseBlock,
        index: int,
    ):
        for i in range(8):
            _index = index + i
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

    def paint_cluster(self, index: int, offset: pygame.math.Vector2, color):
        for block in self.clusters[index]:
            display = pygame.display.get_surface()
            pygame.draw.rect(display, color, block.rect.move(offset))
