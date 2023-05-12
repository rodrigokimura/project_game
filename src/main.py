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


def clear_db():
    from storage import PlayerStorage, WorldStorage

    try:
        WorldStorage().clear()
        PlayerStorage().clear()
    except Exception as e:
        print(e)


def sound():
    from sounds import Chord, Sample, play_samples, square_wave

    samples = [
        ("F G", 0.5),
        ("F G", 0.5),
        ("F G", 0.5),
        ("F G", 0.5),
        ("F G", 0.5),
        ("F G", 0.5),
        ("E G", 0.5),
        ("E G", 0.5),
        ("E G", 0.5),
        ("E G", 0.5),
        ("E G", 0.5),
        ("D B", 0.5),
        ("D B", 0.5),
        ("D B", 0.5),
        ("D B", 0.5),
        ("D A", 0.5),
        ("D B", 0.5),
        ("C C5", 1.2),
    ]
    play_samples(
        [
            Sample(Chord.from_str_list(s.split()).to_frequencies(), square_wave, d)
            for s, d in samples
        ]
    )

    samples = [
        ("G2", 1),
        ("G2", 1),
        ("G2", 1),
        ("D#2", 0.75),
        ("A#2", 0.25),
        ("G2", 1),
        ("D#2", 0.75),
        ("A#2", 0.25),
        ("G2", 1),
    ]
    play_samples(
        [
            Sample(Chord.from_str_list(s.split()).to_frequencies(), square_wave, d)
            for s, d in samples
        ]
    )


if __name__ == "__main__":
    options = {
        "play": play,
        "debug": debug,
        "viewer": world_viewer,
        "builder": world_builder,
        "clear_db": clear_db,
        "sound": sound,
    }

    parser = argparse.ArgumentParser(description="Run game")
    parser.add_argument("--action", choices=options.keys(), default=next(iter(options)))
    args = parser.parse_args()
    action = args.action
    options[args.action]()
