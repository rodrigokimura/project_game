import enum

import pygame


class Controller(enum.IntEnum):
    AI = enum.auto()
    KEYBOARD = enum.auto()
    JOYSTICK = enum.auto()


class Button(enum.IntEnum):
    A = 2
    B = 1
    X = 3
    Y = 0
    LB = 4
    RB = 5
    LT = 6
    RT = 7
    START = 9


class Key(enum.IntEnum):
    ESC = pygame.K_ESCAPE
    Q = pygame.K_q
    W = pygame.K_w
    R = pygame.K_r
    T = pygame.K_t

    E = pygame.K_e
    D = pygame.K_d
    S = pygame.K_s
    F = pygame.K_f

    V = pygame.K_v

    SPACE = pygame.K_SPACE


class MouseButton(enum.IntEnum):
    MAIN = 0
    MIDDLE = 1
    SECONDARY = 2
