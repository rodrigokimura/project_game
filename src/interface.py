import pygame

from player import BasePlayer
from world import World


class Camera:
    def __init__(self, size: tuple[int, int], player: BasePlayer, world: World) -> None:
        self.width, self.height = size
        self.player = player
        self.world = world

    def get_rect(self):
        rect = pygame.rect.Rect(0, 0, self.width, self.height)
        rect.center = self.player.rect.center

        top = self.player.rect.centery - self.height / 2
        if top <= 0:
            rect.top = 0

        bottom = self.player.rect.centery + self.height / 2
        if bottom >= self.world.surface.get_rect().height:
            rect.bottom = self.world.surface.get_rect().height

        left = self.player.rect.centerx - self.width / 2
        if left < 0:
            rect.left = 0

        right = self.player.rect.centerx + self.width / 2
        if right >= self.world.surface.get_rect().width:
            rect.right = self.world.surface.get_rect().width

        return rect
