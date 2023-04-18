import pygame
import pytest

from interface import Camera
from player import BasePlayer
from world import World


class MockedPlayer(BasePlayer):
    def __init__(self) -> None:
        self.rect = pygame.rect.Rect(0, 0, 10, 10)


class TestCamera:
    @pytest.fixture
    def player(self):
        return MockedPlayer()

    @pytest.fixture
    def world(self):
        return World((100, 100), 10, 10)

    def test_camera_on_center(self, player: BasePlayer, world: World):
        player.rect.center = (50, 50)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        assert rect.center == (50, 50)

    def test_camera_on_topleft_corner(self, player: BasePlayer, world: World):
        player.rect.center = (5, 5)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        assert rect.topleft == (0, 0)

    def test_camera_on_topright_corner(self, player: BasePlayer, world: World):
        player.rect.center = (90, 5)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        assert rect.top == 0
        assert rect.right == 100

    def test_camera_on_bottomleft_corner(self, player: BasePlayer, world: World):
        player.rect.center = (5, 90)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        assert rect.bottom == 100
        assert rect.left == 0

    def test_camera_on_bottomright_corner(self, player: BasePlayer, world: World):
        player.rect.center = (90, 90)
        camera = Camera((20, 20), player, world)

        rect = camera.get_rect()

        assert rect.bottom == 100
        assert rect.right == 100