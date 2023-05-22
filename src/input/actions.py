from abc import ABC, abstractmethod
from typing import Any, Callable

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
