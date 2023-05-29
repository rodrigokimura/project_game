from typing import Any

import pygame


def custom_collision_detection(sprite_left: Any, sprite_right: Any):
    return pygame.sprite.collide_mask(sprite_left, sprite_right) is not None
