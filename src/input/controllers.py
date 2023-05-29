from abc import ABC, abstractmethod

import pygame

from input.actions import (
    BaseAction,
    ContinuousAction,
    CooldownCounterTimer,
    CounterTimer,
    OncePerPress,
)
from input.constants import Button, Controller, Key, MouseButton
from settings import BLOCK_SIZE


class BaseController(ABC):
    @abstractmethod
    def control(self, dt: float):
        ...


class PlayerController(BaseController):
    @abstractmethod
    def reset_jump(self):
        ...


class BaseControllable(ABC):
    @abstractmethod
    def set_controller(self, controller_id: Controller):
        ...


class PlayerControllable(BaseControllable):
    cursor_range: int

    @abstractmethod
    def move(self, dt: float, amount: float):
        ...

    @abstractmethod
    def move_cursor(self, dt: float, x: float, y: float):
        ...

    @abstractmethod
    def next_mode(self, dt: float):
        ...

    @abstractmethod
    def pause(self, dt: float):
        ...

    @abstractmethod
    def jump(self, dt: float):
        ...

    @abstractmethod
    def dash_left(self, dt: float):
        ...

    @abstractmethod
    def dash_right(self, dt: float):
        ...

    @abstractmethod
    def place_block(self, dt: float):
        ...

    @abstractmethod
    def boost(self, dt: float):
        ...

    @abstractmethod
    def glide(self, dt: float):
        ...

    @abstractmethod
    def destroy_block(self, dt: float):
        ...

    @abstractmethod
    def open_inventory(self, dt: float):
        ...

    @abstractmethod
    def shoot(self, dt: float):
        ...


class MenuControllable(BaseControllable):
    @abstractmethod
    def move(self, dt: float, x: float, y: float):
        ...

    @abstractmethod
    def select(self, dt: float):
        ...


class InventoryControllable(BaseControllable):
    @abstractmethod
    def move(self, dt: float, x: float, y: float):
        ...

    @abstractmethod
    def close(self, dt: float):
        ...


class JoystickInventoryController(BaseController):
    def __init__(
        self,
        controllable: InventoryControllable,
    ) -> None:
        self.joystick = pygame.joystick.Joystick(0)
        self.hat_actions: list[tuple[int, BaseAction]] = [
            (0, OncePerPress(controllable.move))
        ]
        self.button_actions: list[tuple[Button, BaseAction]] = [
            (Button.B, OncePerPress(controllable.close)),
        ]

    def control(self, dt: float):
        for hat, action in self.hat_actions:
            x_axis, y_axis = self.joystick.get_hat(hat)
            action.execute(bool(x_axis or y_axis), dt, [x_axis, y_axis])

        for button, action in self.button_actions:
            value = self.joystick.get_button(button)
            action.execute(value, dt)


class KeyboardInventoryController(BaseController):
    def __init__(self, controllable: InventoryControllable) -> None:
        udlr = (Key.E, Key.D, Key.S, Key.F)

        self.direction_actions: list[tuple[tuple[Key, Key, Key, Key], BaseAction]] = [
            (udlr, OncePerPress(controllable.move))
        ]
        self.key_actions: list[tuple[Key, BaseAction]] = [
            (Key.T, OncePerPress(controllable.close)),
        ]

    def control(self, dt: float):
        for d_keys, action in self.direction_actions:
            up, down, left, right = d_keys
            keys = pygame.key.get_pressed()

            if keys[up] and keys[down]:
                y_axis = 0
            elif keys[up]:
                y_axis = 1
            elif keys[down]:
                y_axis = -1
            else:
                y_axis = 0

            if keys[left] and keys[right]:
                x_axis = 0
            elif keys[left]:
                x_axis = -1
            elif keys[right]:
                x_axis = 1
            else:
                x_axis = 0

            action.execute(bool(x_axis or y_axis), dt, [x_axis, y_axis])

        for key, action in self.key_actions:
            value = pygame.key.get_pressed()[key]
            action.execute(value, dt)


class AiPlayerController(PlayerController):
    def __init__(
        self,
        controllable: PlayerControllable,
    ) -> None:
        self.controllable = controllable
        self.timer = 0

    def control(self, dt: float):
        self.timer += dt
        if self.timer < 0.8:
            self.controllable.move(dt, 0.5)
        elif self.timer < 1.6:
            self.controllable.move(dt, -0.5)
        else:
            self.timer = 0

    def reset_jump(self):
        ...


class JoystickPlayerController(PlayerController):
    def __init__(
        self,
        controllable: PlayerControllable,
        max_jump_count: int,
        max_jump_time: float,
    ) -> None:
        self.joystick = pygame.joystick.Joystick(0)

        self._jump = CounterTimer(controllable.jump, max_jump_count, max_jump_time)

        self.axis_actions: list[tuple[tuple[int, ...], BaseAction]] = [
            ((0,), ContinuousAction(controllable.move)),
            ((2, 3), ContinuousAction(controllable.move_cursor)),
        ]

        self.button_actions: list[tuple[Button, BaseAction]] = [
            (Button.LT, OncePerPress(controllable.next_mode)),
            (Button.START, OncePerPress(controllable.pause)),
            (Button.LB, CooldownCounterTimer(controllable.dash_left, 2, 0.2, 1)),
            (Button.RB, CooldownCounterTimer(controllable.dash_right, 2, 0.2, 1)),
            (Button.RB, OncePerPress(controllable.place_block)),
            (Button.Y, ContinuousAction(controllable.boost)),
            (Button.RT, ContinuousAction(controllable.destroy_block)),
            (Button.RT, OncePerPress(controllable.shoot)),
            (Button.B, self._jump),
            (Button.B, ContinuousAction(controllable.glide)),
            (Button.X, OncePerPress(controllable.open_inventory)),
        ]

    def control(self, dt: float):
        for axes, action in self.axis_actions:
            axes_values = [round(self.joystick.get_axis(a), 2) for a in axes]
            action.execute(True, dt, axes_values)

        for button, action in self.button_actions:
            value = self.joystick.get_button(button)
            action.execute(value, dt)

    def reset_jump(self):
        self._jump.reset()


class KeyboardPlayerController(PlayerController):
    def __init__(
        self,
        controllable: PlayerControllable,
        max_jump_count: int,
        max_jump_time: float,
    ) -> None:
        self._jump = CounterTimer(controllable.jump, max_jump_count, max_jump_time)

        self.cursor_range = controllable.cursor_range
        self.move_cursor = ContinuousAction(controllable.move_cursor)

        self.direction_key_actions: list[tuple[tuple[Key, Key], BaseAction]] = [
            ((Key.S, Key.F), ContinuousAction(controllable.move)),
        ]

        self.key_actions: list[tuple[Key, BaseAction]] = [
            (Key.Q, OncePerPress(controllable.next_mode)),
            (Key.ESC, OncePerPress(controllable.pause)),
            (Key.W, CooldownCounterTimer(controllable.dash_left, 2, 0.2, 1)),
            (Key.R, CooldownCounterTimer(controllable.dash_right, 2, 0.2, 1)),
            (Key.R, OncePerPress(controllable.place_block)),
            (Key.V, ContinuousAction(controllable.boost)),
            (Key.SPACE, self._jump),
            (Key.SPACE, ContinuousAction(controllable.glide)),
            (Key.T, OncePerPress(controllable.open_inventory)),
        ]
        self.mouse_button_actions: list[tuple[MouseButton, BaseAction]] = [
            (MouseButton.MAIN, OncePerPress(controllable.place_block)),
            (MouseButton.SECONDARY, ContinuousAction(controllable.destroy_block)),
            (MouseButton.SECONDARY, OncePerPress(controllable.shoot)),
        ]

    def control(self, dt: float):
        self._perform_cursor_movement(dt)

        for d_keys, action in self.direction_key_actions:
            left, right = d_keys
            keys = pygame.key.get_pressed()
            if keys[left] and keys[right]:
                x_axis = 0
            elif keys[left]:
                x_axis = -1
            elif keys[right]:
                x_axis = 1
            else:
                x_axis = 0
            action.execute(True, dt, [x_axis])

        for key, action in self.key_actions:
            value = pygame.key.get_pressed()[key]
            action.execute(value, dt)

        for key, action in self.mouse_button_actions:
            value = pygame.mouse.get_pressed()[key]
            action.execute(value, dt)

    def _perform_cursor_movement(self, dt: float):
        # assuming player position on center
        mouse_position = pygame.math.Vector2(pygame.mouse.get_pos())
        middle_screen = pygame.math.Vector2(pygame.display.get_surface().get_size()) / 2
        rel = mouse_position - middle_screen
        rel = rel.clamp_magnitude(BLOCK_SIZE * self.cursor_range) / (
            BLOCK_SIZE * self.cursor_range
        )
        axes_values = [round(rel.x, 2), round(rel.y, 2)]
        self.move_cursor.execute(True, dt, axes_values)

    def reset_jump(self):
        self._jump.reset()


class JoystickMenuController(BaseController):
    def __init__(self, controllable: MenuControllable) -> None:
        self.joystick = pygame.joystick.Joystick(0)
        self.hat_actions: list[tuple[int, BaseAction]] = [
            (0, OncePerPress(controllable.move))
        ]
        self.button_actions: list[tuple[Button, BaseAction]] = [
            (Button.A, OncePerPress(controllable.select)),
        ]

    def control(self, dt: float):
        for hat, action in self.hat_actions:
            x_axis, y_axis = self.joystick.get_hat(hat)
            action.execute(bool(x_axis or y_axis), dt, [x_axis, y_axis])

        for button, action in self.button_actions:
            value = self.joystick.get_button(button)
            action.execute(value, dt)


class KeyboardMenuController(BaseController):
    def __init__(self, controllable: MenuControllable) -> None:
        udlr = (Key.E, Key.D, Key.S, Key.F)

        self.direction_actions: list[tuple[tuple[Key, Key, Key, Key], BaseAction]] = [
            (udlr, OncePerPress(controllable.move))
        ]
        self.key_actions: list[tuple[Key, BaseAction]] = [
            (Key.SPACE, OncePerPress(controllable.select)),
        ]

    def control(self, dt: float):
        for d_keys, action in self.direction_actions:
            up, down, left, right = d_keys
            keys = pygame.key.get_pressed()

            if keys[up] and keys[down]:
                y_axis = 0
            elif keys[up]:
                y_axis = 1
            elif keys[down]:
                y_axis = -1
            else:
                y_axis = 0

            if keys[left] and keys[right]:
                x_axis = 0
            elif keys[left]:
                x_axis = -1
            elif keys[right]:
                x_axis = 1
            else:
                x_axis = 0
            action.execute(bool(x_axis or y_axis), dt, [x_axis, y_axis])

        for key, action in self.key_actions:
            value = pygame.key.get_pressed()[key]
            action.execute(value, dt)
