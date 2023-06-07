from itertools import product

import pygame

from blocks import BaseBlock
from settings import BLOCK_SIZE
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
        (-1, 1),
    )

    def __init__(self) -> None:
        self.checked_coords = set()
        self.checked_blocks = set()

    def detect_clusters(
        self,
        blocks: Container2d[BaseBlock],
        bounding_rect: pygame.rect.Rect,
        offset: pygame.math.Vector2,
    ):
        # find first non empty cell

        start_point = bounding_rect.topleft
        end_point = bounding_rect.bottomright
        start_point = start_point[0] // BLOCK_SIZE, start_point[1] // BLOCK_SIZE
        end_point = end_point[0] // BLOCK_SIZE, end_point[1] // BLOCK_SIZE

        # iterate over lines first
        block = None
        for y, x in product(
            range(start_point[1], end_point[1]),
            range(start_point[0], end_point[0]),
        ):
            self.checked_coords.add((x, y))
            block = blocks.get_element((x, y))
            if block is not None:
                self.checked_blocks.add(block)
                break

        if block is None:
            return

        clusters = []
        index = 6
        while True:
            index = self.convert_to_opposing_index(index)
            index = self.get_next_index(index)
            self.paint_block(block, offset)
            self.checked_blocks.add(block)
            block, index = self.get_next_block_index(blocks, block, index)
            if block is None:
                break
            if block.coords[0] >= end_point[0]:
                block, index = self.get_next_block_index(blocks, block, 5)
                if block is None:
                    break
            if block.coords[1] >= end_point[1]:
                block, index = self.get_next_block_index(blocks, block, 7)
                if block is None:
                    break
            if block.coords[0] <= start_point[0]:
                block, index = self.get_next_block_index(blocks, block, 3)
                if block is None:
                    break
            if block.coords[1] <= start_point[1]:
                block, index = self.get_next_block_index(blocks, block, 1)
                if block is None:
                    break

    def paint_block(self, block: BaseBlock, offset: pygame.math.Vector2):
        display = pygame.display.get_surface()
        pygame.draw.rect(display, "red", block.rect.move(offset))

    def get_neighbor_coords(self, coords: tuple[int, int], index: int):
        """
        0 1 2
        7 x 3
        6 5 4
        """
        index = index % 7 - 1
        x_1, y_1 = coords
        x_2, y_2 = self.NEIGHBORS[index]
        return (x_1 + x_2, y_1 + y_2)

    def get_next_block_index(
        self, blocks: Container2d[BaseBlock], block: BaseBlock, index: int
    ):
        for i in range(8):
            _index = index + i
            coords = self.get_neighbor_coords(block.coords, _index)
            if coords is None:
                continue
            if coords in self.checked_coords:
                continue
            self.checked_coords.add(coords)
            _block = blocks.get_element(coords)
            if _block is None:
                continue
            if _block in self.checked_blocks:
                continue
            self.checked_blocks.add(_block)
            return _block, _index
        return None, 0

    def convert_to_opposing_index(self, index: int):
        index -= 4
        if index < 0:
            index += 8
        return index

    @staticmethod
    def get_next_index(index):
        index += 1
        return index % 7 - 1
