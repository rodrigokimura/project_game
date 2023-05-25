from typing import Generic, TypeVar

T = TypeVar("T")


class Container2d(Generic[T]):
    """Class to store 2D arrays of size [x, y]"""

    def __init__(self, size: tuple[int, int]) -> None:
        self._container = [[None for _ in range(size[1])] for _ in range(size[0])]

    def get_element(self, coords: tuple[int, int]) -> T | None:
        return self._container[coords[0]][coords[1]]

    def set_element(self, coords: tuple[int, int], element: T):
        self._container[coords[0]][coords[1]] = element  # type: ignore
