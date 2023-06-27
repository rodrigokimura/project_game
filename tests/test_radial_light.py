import pytest

from blocks import BaseBlock
from lighting import RadialLight
from log import log
from utils.container import Container2d


@pytest.fixture
def blocks():
    return Container2d((10, 10))


def test_radial_light(blocks: Container2d[BaseBlock]):
    radial_light = RadialLight(2, blocks)
    log(radial_light.offsets)
    print(len(radial_light.offsets))
