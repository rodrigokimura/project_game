from itertools import product

import pytest

from blocks import BaseBlock, Rock
from lighting import RadialLight
from utils.container import Container2d


@pytest.fixture
def blocks():
    blocks = Container2d((10, 10))
    w, h = blocks.size
    for coords in product(range(w), range(h)):
        rock = Rock(coords, 0, 0)
        blocks.set_element(coords, rock)
    return blocks


def test_radial_light(blocks: Container2d[BaseBlock]):
    radial_light = RadialLight(2, blocks)
    # radial_light.iter_rays()
    # for c in radial_light.iter_rays():
    #     print(c)
