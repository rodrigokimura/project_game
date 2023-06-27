from itertools import product
from typing import Generic, TypeVar

from utils.coords import Coords

Element = TypeVar("Element")


class Container2d(Generic[Element]):
    """Class to store 2D arrays of size [x, y]"""

    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self._container = [[]]
        self.empty()

    def get_element(self, coords: Coords) -> Element | None:
        try:
            return self._container[coords[0]][coords[1]]
        except IndexError:
            return None

    def set_element(self, coords: Coords, element: Element | None):
        self._container[coords[0]][coords[1]] = element  # type: ignore

    def empty(self):
        self._container = [
            [None for _ in range(self.size[1])] for _ in range(self.size[0])
        ]

    def get_surrounding(self, coords: Coords, padding: int):
        x, y = coords
        for _coords in product(
            range(x - padding, x + padding), range(y - padding, y + padding)
        ):
            yield self.get_element(_coords)

    def get_layer(self, coords: Coords, index: int):
        x, y = coords

        if index <= 0:
            return self.get_element(coords)

        points: set[Coords] = set()
        for i in range(2 + 2 * index):
            points.add((x + i, y - index))
            points.add((x + i, y + index))
            points.add((x - index, y + i))
            points.add((x + index, y + i))
