import pygame
from biome import Biome

from settings import SCREEN_HEIGHT, SCREEN_WIDTH

COLOR_KEY = pygame.color.Color(127, 127, 0)


def blank_background():
    return pygame.surface.Surface((SCREEN_WIDTH * 2, SCREEN_HEIGHT))


class BackgroundResolver:
    def __init__(self) -> None:
        self.mountains = Mountains()

    def resolve(self, _: Biome, player_position: pygame.math.Vector2):
        return self.mountains.get_image(player_position)

class Background:
    distances = {
        1: 0.8,
        2: 0.7,
        3: 0.4,
    }

    def get_image(self, position: pygame.math.Vector2):
        delta_x = position.x % SCREEN_WIDTH
        layers = background_images[self.__class__]
        img = blank_background()
        img.fill((0, 0, 0))
        img.blit(layers[1], (-self.distances[1] * delta_x, 0))
        img.blit(layers[2], (-self.distances[2] * delta_x, 0))
        img.blit(layers[3], (-self.distances[3] * delta_x, 0))
        return img


class Mountains(Background):
    ...


background_images: dict[type[Background], dict[int, pygame.surface.Surface]] = {
    Mountains: {
        1: blank_background(),
        2: blank_background(),
        3: blank_background(),
    },
}


def load_background_images():
    img = background_images[Mountains][1]
    img.fill(COLOR_KEY)
    img.set_colorkey(COLOR_KEY)
    pygame.draw.polygon(
        img,
        pygame.color.Color(50, 50, 50),
        [
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 8),
            (0, SCREEN_HEIGHT),
            (SCREEN_WIDTH, SCREEN_HEIGHT),
        ],
    )

    img = background_images[Mountains][2]
    img.fill(COLOR_KEY)
    img.set_colorkey(COLOR_KEY)
    pygame.draw.polygon(
        img,
        pygame.color.Color(100, 100, 100),
        [
            (SCREEN_WIDTH // 2, 2 * (SCREEN_HEIGHT // 8)),
            (0, SCREEN_HEIGHT),
            (SCREEN_WIDTH, SCREEN_HEIGHT),
        ],
    )

    img = background_images[Mountains][3]
    img.fill(COLOR_KEY)
    img.set_colorkey(COLOR_KEY)
    pygame.draw.polygon(
        img,
        pygame.color.Color(150, 150, 150),
        [
            (SCREEN_WIDTH // 2, 3 * SCREEN_HEIGHT // 8),
            (0, SCREEN_HEIGHT),
            (SCREEN_WIDTH, SCREEN_HEIGHT),
        ],
    )
