import enum
from abc import ABC, abstractmethod
from typing import Any, Callable

import pygame

ActionCommandType = Callable[..., None]


class BaseAction(ABC):
    def __init__(self, command: ActionCommandType) -> None:
        self.command = command

    @abstractmethod
    def check(self, value: bool, dt: float) -> bool:
        ...

    def do(self, value: bool, dt: float, command_args: list[Any] | None = None):
        command_args = command_args or []
        if self.check(value, dt):
            self.command(dt, *command_args)


class ResettableAction(BaseAction):
    @abstractmethod
    def reset(self) -> bool:
        ...


class ContinuousAction(BaseAction):
    def check(self, value: bool, _: float) -> bool:
        return value


class OncePerPress(BaseAction):
    def __init__(self, command: ActionCommandType) -> None:
        super().__init__(command)
        self.state = False

    def check(self, value: bool, _: float) -> bool:
        if value and self.state:
            self.state = False
            return True
        elif not value:
            self.state = True
        return False


class CounterTimer(ResettableAction):
    def __init__(
        self, command: ActionCommandType, max_count: int, max_time: float
    ) -> None:
        super().__init__(command)
        self._past_value = False
        self.state = False
        self.counter = 0
        self.timer = 0
        self.max_count = max_count
        self.max_time = max_time

    def check(self, value: bool, dt: float):
        # TODO: decrease complexity
        if value != self._past_value:
            self._past_value = value
            if value:
                self.state = True
                self.counter += 1
            else:
                if self.counter < self.max_count:
                    self.timer = 0
        elif value:
            if self.counter < self.max_count and self.timer < self.max_time:
                if self.state:
                    self.timer += dt
                    return True
            else:
                self.state = False
        return False

    def reset(self):
        self.timer = 0
        self.counter = 0


class CooldownCounterTimer(CounterTimer):
    def __init__(
        self,
        command: ActionCommandType,
        max_count: int,
        max_time: float,
        cooldown_max_time: float,
    ) -> None:
        super().__init__(command, max_count, max_time)
        self.cooldown_timer = 0
        self.cooldown_max_time = cooldown_max_time

    def reset_cooldown(self):
        self.cooldown_timer = 0

    def check(self, value: bool, dt: float):
        if self.cooldown_timer >= self.cooldown_max_time:
            self.reset()
            self.reset_cooldown()

        check = super().check(value, dt)
        if not check:
            self.cooldown_timer += dt
        return check


class BaseController(ABC):
    @abstractmethod
    def control(self, dt: float):
        ...


class Controllable(ABC):
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


class JoystickController(BaseController):
    def __init__(
        self,
        controllable: Controllable,
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
            (Button.Y, ContinuousAction(controllable.boost)),
            (Button.RT, ContinuousAction(controllable.destroy_block)),
            (Button.B, self._jump),
            (Button.B, ContinuousAction(controllable.glide)),
            (Button.X, OncePerPress(controllable.open_inventory)),
        ]

    def control(self, dt: float):
        for axes, action in self.axis_actions:
            axes_values = [round(self.joystick.get_axis(a), 2) for a in axes]
            action.do(True, dt, axes_values)

        for button, action in self.button_actions:
            value = self.joystick.get_button(button)
            action.do(value, dt)

    def reset_jump(self):
        self._jump.reset()
