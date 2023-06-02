from typing import NamedTuple

import pygame


class FillBorderColors(NamedTuple):
    fill: pygame.color.Color
    border: pygame.color.Color


def draw_bordered_rect(
    image: pygame.surface.Surface,
    rect: pygame.rect.Rect,
    colors: FillBorderColors,
    border_width: int = 1,
    sides: tuple[bool, bool, bool, bool] = (True, True, True, True),
):
    pygame.draw.rect(image, colors.fill, rect)
    if all(sides):
        pygame.draw.rect(image, colors.border, rect, border_width)
    up, right, down, left = sides
    if up:
        pygame.draw.line(
            image, colors.border, rect.topleft, rect.topright, border_width
        )
    if down:
        pygame.draw.line(
            image, colors.border, rect.bottomleft, rect.bottomright, border_width
        )
    if left:
        pygame.draw.line(
            image, colors.border, rect.topleft, rect.bottomleft, border_width
        )
    if right:
        pygame.draw.line(
            image, colors.border, rect.topright, rect.bottomright, border_width
        )
