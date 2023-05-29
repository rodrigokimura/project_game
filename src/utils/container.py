from itertools import product
from typing import Generic, TypeVar

T = TypeVar("T")


class Container2d(Generic[T]):
    """Class to store 2D arrays of size [x, y]"""

    def __init__(self, size: tuple[int, int]) -> None:
        self._size = size
        self._container = [[]]
        self.empty()

    def get_element(self, coords: tuple[int, int]) -> T | None:
        try:
            return self._container[coords[0]][coords[1]]
        except IndexError:
            return None

    def set_element(self, coords: tuple[int, int], element: T):
        self._container[coords[0]][coords[1]] = element  # type: ignore

    def empty(self):
        self._container = [
            [None for _ in range(self._size[1])] for _ in range(self._size[0])
        ]

    def get_surrounding(self, coords: tuple[int, int], padding: int):
        x, y = coords
        for _coords in product(
            range(x - padding, x + padding), range(y - padding, y + padding)
        ):
            yield self.get_element(_coords)
