from typing import NamedTuple

import pygame


class FillBorderColors(NamedTuple):
    fill: pygame.color.Color
    border: pygame.color.Color


class BorderOptions(NamedTuple):
    width: int = 1
    radius: int = 0
    sides: tuple[bool, bool, bool, bool] = (True, True, True, True)


def draw_bordered_rect(
    image: pygame.surface.Surface,
    rect: pygame.rect.Rect,
    colors: FillBorderColors,
    border_options: BorderOptions = BorderOptions(),
):
    pygame.draw.rect(image, colors.fill, rect)
    if all(border_options.sides):
        pygame.draw.rect(image, colors.border, rect, border_options.width)
    up, right, down, left = border_options.sides
    if up:
        pygame.draw.line(
            image, colors.border, rect.topleft, rect.topright, border_options.width
        )
    if down:
        pygame.draw.line(
            image,
            colors.border,
            rect.bottomleft,
            rect.bottomright,
            border_options.width,
        )
    if left:
        pygame.draw.line(
            image, colors.border, rect.topleft, rect.bottomleft, border_options.width
        )
    if right:
        pygame.draw.line(
            image, colors.border, rect.topright, rect.bottomright, border_options.width
        )
