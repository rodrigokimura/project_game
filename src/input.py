from abc import ABC, abstractmethod

import pygame


class BaseAction(ABC):
    @abstractmethod
    def check(self) -> bool:
        ...


class ResettableAction(BaseAction):
    @abstractmethod
    def reset(self) -> bool:
        ...


class ContinuousAction(BaseAction):
    def check(self, value: bool) -> bool:
        return value


class OncePerPressAction(BaseAction):
    def __init__(self) -> None:
        self.state = False

    def check(self, value: bool) -> bool:
        if value and self.state:
            self.state = False
            return True
        elif not value:
            self.state = True
        return False


class ContinuousCounterTimerAction(ResettableAction):
    def __init__(self, max_count: int, max_time: float) -> None:
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
        self, max_count: int, max_time: float, cooldown_max_time: float
    ) -> None:
        super().__init__(max_count, max_time)
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


class BaseControl:
    ...


class JoystickControl(BaseControl):
    def __init__(self, max_jump_count: int, max_jump_time: float) -> None:
        self.joystick = pygame.joystick.Joystick(0)

        self._change_mode = OncePerPressAction()
        self._pause = OncePerPressAction()
        self._jump = ContinuousCounterTimerAction(max_jump_count, max_jump_time)
        self._boost = ContinuousAction()
        self._glide = ContinuousAction()
        self._destroy = ContinuousAction()
        self._dash_l = ContinuousCooldownCounterTimerAction(2, 0.2, 1)
        self._dash_r = ContinuousCooldownCounterTimerAction(2, 0.2, 1)

    def get_linear_movement(self):
        left_stick_x = self.joystick.get_axis(0)
        left_stick_x = round(left_stick_x, 1)
        return left_stick_x

    def get_cursor_position(self):
        right_stick_x = self.joystick.get_axis(2)
        right_stick_y = self.joystick.get_axis(3)
        return right_stick_x, right_stick_y

    def change_mode(self):
        lt = self.joystick.get_button(6)
        return self._change_mode.check(lt)

    def pause(self):
        start = self.joystick.get_button(9)
        return self._pause.check(start)

    def dash_left(self, dt: float):
        value = self.joystick.get_button(4)
        return self._dash_l.check(value, dt)

    def dash_right(self, dt: float):
        value = self.joystick.get_button(5)
        return self._dash_r.check(value, dt)

    def jump(self, dt: float):
        b = self.joystick.get_button(1)
        return self._jump.check(b, dt)

    def reset_jump(self):
        self._jump.reset()

    def boost(self):
        y = self.joystick.get_button(0)
        return self._boost.check(y)

    def glide(self):
        b = self.joystick.get_button(1)
        return self._glide.check(b)

    def destroy(self):
        rt = self.joystick.get_button(7)
        return self._destroy.check(rt)
