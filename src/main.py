import argparse
import os
from pickle import UnpicklingError

from game import Game
from log import log
from sounds import Chord, Sample, play_samples, square_wave
from storage import PlayerStorage, WorldStorage


def play():
    game = Game()
    game.run()


def debug():
    os.environ["DEBUG"] = "1"
    play()


def world_viewer():
    # TODO: Implement
    log("Not implemented yet")


def world_builder():
    # TODO: Implement
    log("Not implemented yet")


def clear_db():
    try:
        WorldStorage().clear()
        PlayerStorage().clear()
    except (UnpicklingError, AttributeError) as exc:
        print(exc)


def sound():
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
            Sample(
                Chord.from_strings(sample.split()).to_frequencies(),
                square_wave,
                duration,
            )
            for sample, duration in samples
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
            Sample(
                Chord.from_strings(sample.split()).to_frequencies(),
                square_wave,
                duration,
            )
            for sample, duration in samples
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
