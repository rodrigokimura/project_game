import pygame


def blit_multiple(
    image: pygame.surface.Surface,
    group: pygame.sprite.Group,
    offset: pygame.math.Vector2 | None = None,
    sprite_img_attr: str = "image",
):
    if offset:
        image.blits(
            (getattr(sprite, sprite_img_attr), sprite.rect.move(offset))  # type: ignore
            for sprite in group
        )
    else:
        image.blits(
            (getattr(sprite, sprite_img_attr), sprite.rect)  # type: ignore
            for sprite in group
        )
