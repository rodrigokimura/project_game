from collections.abc import Callable, Collection

import numpy
import pygame
import scipy
from numpy.typing import ArrayLike

SAMPLE_RATE = 44100

pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)

SAMPLE_LENGTH = 4096

REFERENCE_PITCH = 440
REFERENCE_OCTAVE = 4
NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def notation_to_frequency(notation: str) -> float:
    note, octave = notation_to_note_octave(notation)

    if note not in NOTES:
        raise ValueError(f"Note ({note}) should be one of {NOTES}")

    pitch_diff = NOTES.index(note) - 9
    octave_diff = octave - REFERENCE_OCTAVE
    diff = octave_diff * len(NOTES) + pitch_diff

    return 2 ** (1 / 12 * diff) * REFERENCE_PITCH


def notation_to_note_octave(note: str) -> tuple[str, int]:
    has_octave = note[-1].isdigit()
    if has_octave:
        octave = int(note[-1])
        note = note[:-1]
    else:
        octave = REFERENCE_OCTAVE
    if note not in NOTES:
        raise ValueError(f"{note} should be one of {NOTES}")
    return note, octave


def frequencies_to_sound(
    frequencies: Collection[float], waveform: Callable[[float, int], ArrayLike]
) -> pygame.mixer.Sound:
    arr = sum(waveform(f, SAMPLE_LENGTH) for f in frequencies)  # type: ignore
    arr = numpy.c_[arr, arr]
    return pygame.sndarray.make_sound(arr)


def sine_wave(frequency: float, peak: int):
    length = SAMPLE_RATE / frequency
    arr = numpy.arange(int(length)) * (2 * numpy.pi / length)
    wave = peak * numpy.sin(arr)
    return numpy.resize(wave, (SAMPLE_RATE,)).astype(numpy.int16)


def square_wave(frequency: float, peak: int):
    arr = numpy.linspace(0, 1, int(500 * 440 / frequency), endpoint=False)
    wave = peak * scipy.signal.square(2 * numpy.pi * 5 * arr)
    return numpy.resize(wave, (SAMPLE_RATE,)).astype(numpy.int16)


class Note:
    def __init__(self, notation: str) -> None:
        self.notation = notation
        self.frequency = notation_to_frequency(notation)


class Chord:
    def __init__(self, notes: Collection[Note]) -> None:
        self.notes = notes

    def to_frequencies(self) -> list[float]:
        return [note.frequency for note in self.notes]

    @classmethod
    def from_strings(cls, strings: list[str]):
        return cls([Note(string) for string in strings])


class Sample:
    def __init__(
        self,
        frequencies: Collection[float],
        waveform: Callable[[float, int], ArrayLike] = square_wave,
        duration: float = 1,
    ) -> None:
        self.sound = frequencies_to_sound(frequencies, waveform)
        self.duration = duration


def play_samples(samples: Collection[Sample]):
    millis = 300
    pygame.time.delay(80)
    for sample in samples:
        sample.sound.play(-1)
        pygame.time.delay(int(sample.duration * millis))
        sample.sound.fadeout(50)
        pygame.time.delay(80)
