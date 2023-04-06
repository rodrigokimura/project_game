import pygame


def main():
    pygame.init()

    size = [800, 600]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("Project Game")
    done = False
    clock = pygame.time.Clock()

    while not done:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        pygame.draw.circle(screen, "blue", [60, 250], 40)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
