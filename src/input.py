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


class OncePerPressAction(BaseAction):
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


class ContinuousCounterTimerAction(ResettableAction):
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


class ContinuousCooldownCounterTimerAction(ContinuousCounterTimerAction):
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


class JoystickController(BaseController):
    def __init__(
        self,
        move: ActionCommandType,
        move_cursor: ActionCommandType,
        change_mode: ActionCommandType,
        pause: ActionCommandType,
        jump: ActionCommandType,
        max_jump_count: int,
        max_jump_time: float,
        dash_left: ActionCommandType,
        dash_right: ActionCommandType,
        boost: ActionCommandType,
        glide: ActionCommandType,
        destroy_block: ActionCommandType,
    ) -> None:
        self.joystick = pygame.joystick.Joystick(0)

        self._jump = ContinuousCounterTimerAction(jump, max_jump_count, max_jump_time)

        self.axis_actions: list[tuple[tuple[int, ...], BaseAction]] = [
            ((0,), ContinuousAction(move)),
            ((2, 3), ContinuousAction(move_cursor)),
        ]

        self.button_actions: list[tuple[int, BaseAction]] = [
            (6, OncePerPressAction(change_mode)),
            (9, OncePerPressAction(pause)),
            (4, ContinuousCooldownCounterTimerAction(dash_left, 2, 0.2, 1)),
            (5, ContinuousCooldownCounterTimerAction(dash_right, 2, 0.2, 1)),
            (0, ContinuousAction(boost)),
            (7, ContinuousAction(destroy_block)),
            (1, self._jump),
            (1, ContinuousAction(glide)),
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
