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
        self.checked_coords: set[tuple[int, int]] = set()
        self.checked_blocks: set[BaseBlock] = set()

        self.clusters: list[set[BaseBlock]] = []
        self._starting_block: BaseBlock | None = None

        self.blocks = blocks

        self.start_point = bounding_rect.topleft
        self.end_point = bounding_rect.bottomright
        self.start_point = (
            self.start_point[0] // BLOCK_SIZE,
            self.start_point[1] // BLOCK_SIZE,
        )
        self.end_point = (
            self.end_point[0] // BLOCK_SIZE,
            self.end_point[1] // BLOCK_SIZE,
        )

    def detect(self):
        # iterate over lines first
        block = None
        for y, x in product(
            range(self.start_point[1] + 1, self.end_point[1]),
            range(self.start_point[0] + 1, self.end_point[0]),
        ):
            coords = (x, y)
            if coords in self.checked_coords:
                continue
            block = self.blocks.get_element(coords)
            if block is not None:
                if block in self.checked_blocks:
                    continue
                cluster = self._walk_around_cluster(block)
                self.checked_blocks.update(cluster)
                self.clusters.append(cluster)
                if len(self.clusters) > 3:
                    break
            else:
                self.checked_coords.add(coords)

    def _walk_around_cluster(self, block: BaseBlock):
        self._starting_block = block

        cluster = {block}
        index = 3
        for _ in range(MAX_SURROUNDING_LENGTH):
            block, index = self.get_next_block_index(self.blocks, block, index)  # type: ignore
            if block is None:
                break

            cluster.add(block)
            if self._starting_block == block:
                break
            # convert to opposite (+4) and next (+1)
            index += 5
        return cluster

    def paint_cluster(self, index: int, offset: pygame.math.Vector2, color):
        for block in self.clusters[index]:
            display = pygame.display.get_surface()
            pygame.draw.rect(display, color, block.rect.move(offset))

    def get_neighbor_coords(self, coords: tuple[int, int], index: int):
        """
        0 1 2
        7 x 3
        6 5 4
        """
        x_1, y_1 = coords
        x_2, y_2 = self.NEIGHBORS[index % 8]
        return (x_1 + x_2, y_1 + y_2)

    def get_next_block_index(
        self,
        blocks: Container2d[BaseBlock],
        block: BaseBlock,
        index: int,
    ):
        for i in range(8):
            _index = index + i
            coords = self.get_neighbor_coords(block.coords, _index)
            if coords[0] > self.end_point[0]:
                continue
            if coords[1] > self.end_point[1]:
                continue
            if coords[0] < self.start_point[0]:
                continue
            if coords[1] < self.start_point[1]:
                continue

            if coords in self.checked_coords:
                continue

            _block = blocks.get_element(coords)
            if _block is not None:
                return _block, _index
            self.checked_coords.add(coords)
        return None, 0
