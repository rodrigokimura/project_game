from unittest.mock import MagicMock, patch

import pygame
import pytest

from camera import Camera
from characters import BaseCharacter
from world import World


class MockedPlayer(BaseCharacter):
    def __init__(self) -> None:
        self.rect = pygame.rect.Rect(0, 0, 10, 10)

    def setup(self):
        ...

    def unload(self):
        ...

    def handle_collision(self):
        ...

    def set_controller(self):
        ...

    def should_fall(self) -> bool:
        return True


class TestCamera:
    @pytest.fixture
    def player(self):
        return MockedPlayer()

    @pytest.fixture
    def world(self):
        return World((100, 100), 10, 10)

    @pytest.fixture
    def mocked_setup(self):
        with patch.object(Camera, "_setup") as m:
            m.return_value = None
            yield m

    def test_camera_on_center(
        self, mocked_setup: MagicMock, player: BaseCharacter, world: World
    ):
        player.rect.center = (50, 50)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        mocked_setup.assert_called()
        assert rect.center == (50, 50)

    def test_camera_on_topleft_corner(
        self, mocked_setup: MagicMock, player: BaseCharacter, world: World
    ):
        player.rect.center = (5, 5)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        mocked_setup.assert_called()
        assert rect.topleft == (0, 0)

    def test_camera_on_topright_corner(
        self, mocked_setup: MagicMock, player: BaseCharacter, world: World
    ):
        player.rect.center = (90, 5)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        mocked_setup.assert_called()
        assert rect.top == 0
        assert rect.right == 100

    def test_camera_on_bottomleft_corner(
        self, mocked_setup: MagicMock, player: BaseCharacter, world: World
    ):
        player.rect.center = (5, 90)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        mocked_setup.assert_called()
        assert rect.bottom == 100
        assert rect.left == 0

    def test_camera_on_bottomright_corner(
        self, mocked_setup: MagicMock, player: BaseCharacter, world: World
    ):
        player.rect.center = (90, 90)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        mocked_setup.assert_called()
        assert rect.bottom == 100
        assert rect.right == 100
