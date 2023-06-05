from abc import ABC, abstractmethod

import pygame
import pygame._sdl2.controller

from input.actions import (
    BaseAction,
    ContinuousAction,
    CooldownCounterTimer,
    CounterTimer,
    OncePerPress,
    OncePerTimeout,
)
from input.constants import (
    DPAD,
    MAX_AXIS_VALUE,
    Axis,
    Button,
    Controller,
    Key,
    MouseButton,
)
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
    shooting_frequency: float

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


class GamepadInventoryController(BaseController):
    def __init__(
        self,
        controllable: InventoryControllable,
    ) -> None:
        self.gamepad = pygame._sdl2.controller.Controller(0)

        self.dpad_actions: list[
            tuple[tuple[Button, Button, Button, Button], BaseAction]
        ] = [(DPAD, OncePerPress(controllable.move))]
        self.button_actions: list[tuple[Button, BaseAction]] = [
            (Button.B, OncePerPress(controllable.close)),
        ]

    def control(self, dt: float):
        for d_keys, action in self.dpad_actions:
            up, down, left, right = d_keys
            keys = {}
            keys = {k: self.gamepad.get_button(k) for k in d_keys}

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

        for button, action in self.button_actions:
            value = self.gamepad.get_button(button)
            action.execute(value, dt)


class KeyboardInventoryController(BaseController):
    def __init__(self, controllable: InventoryControllable) -> None:
        udlr = (Key.E, Key.D, Key.S, Key.F)

        self.dpad_actions: list[tuple[tuple[Key, Key, Key, Key], BaseAction]] = [
            (udlr, OncePerPress(controllable.move))
        ]
        self.key_actions: list[tuple[Key, BaseAction]] = [
            (Key.T, OncePerPress(controllable.close)),
        ]

    def control(self, dt: float):
        for d_keys, action in self.dpad_actions:
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


class AIPlayerController(PlayerController):
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


class GamepadPlayerController(PlayerController):
    def __init__(
        self,
        controllable: PlayerControllable,
        max_jump_count: int,
        max_jump_time: float,
    ) -> None:
        self.gamepad = pygame._sdl2.controller.Controller(0)

        self._jump = CounterTimer(controllable.jump, max_jump_count, max_jump_time)

        self.stick_actions: list[tuple[tuple[Axis, ...], BaseAction]] = [
            ((Axis.LEFT_X,), ContinuousAction(controllable.move)),
            ((Axis.RIGHT_X, Axis.RIGHT_Y), ContinuousAction(controllable.move_cursor)),
        ]
        self.trigger_actions: list[tuple[Axis, BaseAction]] = [
            (Axis.TRIGGER_L, OncePerPress(controllable.next_mode)),
            (Axis.TRIGGER_R, ContinuousAction(controllable.destroy_block)),
            (
                Axis.TRIGGER_R,
                OncePerTimeout(controllable.shoot, 1 / controllable.shooting_frequency),
            ),
        ]
        self.trigger_threshold = 0.7 * MAX_AXIS_VALUE

        self.button_actions: list[tuple[Button, BaseAction]] = [
            (Button.START, OncePerPress(controllable.pause)),
            (Button.LB, CooldownCounterTimer(controllable.dash_left, 2, 0.2, 1)),
            (Button.RB, CooldownCounterTimer(controllable.dash_right, 2, 0.2, 1)),
            (Button.RB, OncePerPress(controllable.place_block)),
            (Button.Y, ContinuousAction(controllable.boost)),
            (Button.B, self._jump),
            (Button.B, ContinuousAction(controllable.glide)),
            (Button.X, OncePerPress(controllable.open_inventory)),
        ]

    def control(self, dt: float):
        for trigger, action in self.stick_actions:
            axes_values = [
                round(self.gamepad.get_axis(a) / MAX_AXIS_VALUE, 2) for a in trigger
            ]
            action.execute(True, dt, axes_values)
        for trigger, action in self.trigger_actions:
            value = self.gamepad.get_axis(trigger) > self.trigger_threshold
            action.execute(value, dt)

        for button, action in self.button_actions:
            value = self.gamepad.get_button(button)
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

        self.dpad_actions: list[tuple[tuple[Key, Key], BaseAction]] = [
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
            (
                MouseButton.SECONDARY,
                OncePerTimeout(controllable.shoot, 1 / controllable.shooting_frequency),
            ),
        ]

    def control(self, dt: float):
        self._perform_cursor_movement(dt)

        for d_keys, action in self.dpad_actions:
            left, right = d_keys
            keys = pygame.key.get_pressed()
            x_axis = 0
            if keys[left]:
                x_axis -= 1
            if keys[right]:
                x_axis += 1
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


class GamepadMenuController(BaseController):
    def __init__(self, controllable: MenuControllable) -> None:
        self.gamepad = pygame._sdl2.controller.Controller(0)
        self.dpad_actions: list[
            tuple[tuple[Button, Button, Button, Button], BaseAction]
        ] = [(DPAD, OncePerPress(controllable.move))]
        self.stick_actions: list[tuple[tuple[Axis, Axis], BaseAction]] = [
            ((Axis.LEFT_X, Axis.LEFT_Y), OncePerPress(controllable.move))
        ]
        self.button_actions: list[tuple[Button, BaseAction]] = [
            (Button.A, OncePerPress(controllable.select)),
        ]
        self.stick_threshold = 0.7 * MAX_AXIS_VALUE

    def control(self, dt: float):
        self._process_dpad_actions(dt)
        self._process_stick_actions(dt)
        self._process_button_actions(dt)

    def _process_dpad_actions(self, dt: float):
        for d_keys, action in self.dpad_actions:
            up, down, left, right = (self.gamepad.get_button(k) for k in d_keys)

            y_axis = 0
            if up:
                y_axis += 1
            if down:
                y_axis -= 1

            x_axis = 0
            if left:
                x_axis -= 1
            if right:
                x_axis += 1

            action.execute(bool(x_axis or y_axis), dt, [x_axis, y_axis])

    def _process_stick_actions(self, dt: float):
        for axes, action in self.stick_actions:
            x, y = axes
            x_axis = self.gamepad.get_axis(x.value)
            if x_axis <= -self.stick_threshold:
                x_axis = -1
            elif x_axis >= self.stick_threshold:
                x_axis = 1
            else:
                x_axis = 0
            y_axis = self.gamepad.get_axis(y.value)
            if y_axis <= -self.stick_threshold:
                y_axis = 1
            elif y_axis >= self.stick_threshold:
                y_axis = -1
            else:
                y_axis = 0
            action.execute(bool(x_axis or y_axis), dt, [x_axis, y_axis])

    def _process_button_actions(self, dt: float):
        for button, action in self.button_actions:
            value = self.gamepad.get_button(button)
            action.execute(value, dt)


class KeyboardMenuController(BaseController):
    def __init__(self, controllable: MenuControllable) -> None:
        udlr = (Key.E, Key.D, Key.S, Key.F)

        self.dpad_actions: list[tuple[tuple[Key, Key, Key, Key], BaseAction]] = [
            (udlr, OncePerPress(controllable.move))
        ]
        self.key_actions: list[tuple[Key, BaseAction]] = [
            (Key.SPACE, OncePerPress(controllable.select)),
        ]

    def control(self, dt: float):
        for d_keys, action in self.dpad_actions:
            up, down, left, right = d_keys
            keys = pygame.key.get_pressed()

            y_axis = 0
            if keys[up]:
                y_axis += 1
            if keys[down]:
                y_axis -= 1

            x_axis = 0
            if keys[left]:
                x_axis -= 1
            if keys[right]:
                x_axis += 1
            action.execute(bool(x_axis or y_axis), dt, [x_axis, y_axis])

        for key, action in self.key_actions:
            value = pygame.key.get_pressed()[key]
            action.execute(value, dt)
