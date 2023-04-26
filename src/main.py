import argparse

from log import log


def play():
    from game import Game

    game = Game()
    game.run()


def debug():
    import os

    os.environ["DEBUG"] = "1"
    play()


def world_viewer():
    # TODO: Implement
    log("Not implemented yet")


def world_builder():
    # TODO: Implement
    log("Not implemented yet")


if __name__ == "__main__":
    options = {
        "play": play,
        "debug": debug,
        "viewer": world_viewer,
        "builder": world_builder,
    }

    parser = argparse.ArgumentParser(description="Run game")
    parser.add_argument("--action", choices=options.keys(), default=next(iter(options)))
    args = parser.parse_args()
    action = args.action
    options[args.action]()
