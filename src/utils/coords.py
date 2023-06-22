from itertools import product
from typing import Generator

NEIGHBORS = [delta for delta in product(range(-1, 2), range(-1, 2)) if delta != (0, 0)]

Coords = tuple[int, int]


def neighbors(coords: Coords) -> Generator[Coords, None, None]:
    for delta in NEIGHBORS:
        yield (coords[0] + delta[0], coords[1] + delta[1])
