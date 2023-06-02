import pygame

from biome import Biome
from colors import Color
from settings import SCREEN_HEIGHT, SCREEN_WIDTH

COLOR_KEY = pygame.color.Color(127, 127, 0)


def blank_background(mult: int = 1):
    return pygame.surface.Surface((SCREEN_WIDTH * mult, SCREEN_HEIGHT))


class BackgroundResolver:
    def __init__(self) -> None:
        self.mountains = Mountains()

    def resolve(self, _: Biome, player_position: pygame.math.Vector2):
        return self.mountains.get_image(player_position)


class Background:
    color: Color
    displacements = {
        1: 0.8,
        2: 0.7,
        3: 0.5,
    }
    canvas = blank_background()

    def get_image(self, position: pygame.math.Vector2):
        delta_x = position.x % SCREEN_WIDTH
        layers = background_images[self.__class__]
        img = self.canvas
        img.fill(self.color)
        img.blits(
            tuple(
                (layers[index], (-disp * delta_x, 0))
                for index, disp in self.displacements.items()
            )
        )
        return img


class Mountains(Background):
    def __init__(self) -> None:
        self.color = Color.SKY


background_images: dict[type[Background], dict[int, pygame.surface.Surface]] = {
    Mountains: {
        1: blank_background(),
        2: blank_background(),
        3: blank_background(),
    },
}


def load_background_images():
    for index in Background.displacements:
        background_images[Mountains][index] = make_mountain_background(index)


def make_mountain_background(layer: int):
    colors = {
        1: Color.MOUNTAIN_1,
        2: Color.MOUNTAIN_2,
        3: Color.MOUNTAIN_3,
    }
    img = blank_background()
    width, height = img.get_size()
    disp = Background.displacements[layer]
    width *= disp
    img = pygame.transform.scale(img, (width, height))
    img.fill(COLOR_KEY)
    img.set_colorkey(COLOR_KEY)
    pygame.draw.polygon(
        img,
        colors[layer],
        [
            (width // 2, (height // 8) * layer),
            (0, height),
            (width, height),
        ],
    )
    img2 = blank_background(2)
    img2.fill(COLOR_KEY)
    img2.set_colorkey(COLOR_KEY)
    img2.blits(tuple((img, (i * img.get_width(), 0)) for i in range(4)))
    return img2
