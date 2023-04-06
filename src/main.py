import pygame


def main():
    pygame.init()

    size = [800, 600]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("Project Game")
    running = True
    clock = pygame.time.Clock()

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == ord("a"):
                    print("left")
                if event.key == pygame.K_RIGHT or event.key == ord("d"):
                    print("right")
                if event.key == pygame.K_UP or event.key == ord("w"):
                    print("jump")

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == ord("a"):
                    print("left stop")
                if event.key == pygame.K_RIGHT or event.key == ord("d"):
                    print("right stop")

        pygame.draw.circle(screen, "blue", [60, 250], 40)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
