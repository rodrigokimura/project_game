from itertools import product

Coords = tuple[int, int]
NEIGHBORS = [delta for delta in product(range(-1, 2), range(-1, 2)) if delta != (0, 0)]


def neighbors(coords: Coords):
    for delta in NEIGHBORS:
        yield (coords[0] + delta[0], coords[1] + delta[1])
