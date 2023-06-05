import enum

import pygame
import pygame._sdl2.controller


class Controller(enum.IntEnum):
    AI = enum.auto()
    KEYBOARD = enum.auto()
    GAMEPAD = enum.auto()


# pylint: disable=no-member
class Button(enum.IntEnum):
    DPAD_UP = pygame.CONTROLLER_BUTTON_DPAD_UP
    DPAD_DOWN = pygame.CONTROLLER_BUTTON_DPAD_DOWN
    DPAD_RIGHT = pygame.CONTROLLER_BUTTON_DPAD_RIGHT
    DPAD_LEFT = pygame.CONTROLLER_BUTTON_DPAD_LEFT
    A = pygame.CONTROLLER_BUTTON_A
    B = pygame.CONTROLLER_BUTTON_B
    X = pygame.CONTROLLER_BUTTON_X
    Y = pygame.CONTROLLER_BUTTON_Y
    LB = pygame.CONTROLLER_BUTTON_LEFTSHOULDER
    RB = pygame.CONTROLLER_BUTTON_RIGHTSHOULDER
    START = pygame.CONTROLLER_BUTTON_START
    BACK = pygame.CONTROLLER_BUTTON_BACK


# pylint: disable=no-member
class Axis(enum.IntEnum):
    LEFT_X = pygame.CONTROLLER_AXIS_LEFTX
    LEFT_Y = pygame.CONTROLLER_AXIS_LEFTY
    RIGHT_X = pygame.CONTROLLER_AXIS_RIGHTX
    RIGHT_Y = pygame.CONTROLLER_AXIS_RIGHTY
    TRIGGER_L = pygame.CONTROLLER_AXIS_TRIGGERLEFT
    TRIGGER_R = pygame.CONTROLLER_AXIS_TRIGGERRIGHT


DPAD = (Button.DPAD_UP, Button.DPAD_DOWN, Button.DPAD_LEFT, Button.DPAD_RIGHT)
MAX_AXIS_VALUE = 32767


# pylint: disable=no-member
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
