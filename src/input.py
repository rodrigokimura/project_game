import enum
from abc import ABC, abstractmethod
from typing import Any, Callable

import pygame

from settings import BLOCK_SIZE, MENU_FONT

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


class PlayerController(BaseController):
    @abstractmethod
    def reset_jump(self):
        ...


class PlayerControllable(ABC):
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


class MenuControllable(ABC):
    @abstractmethod
    def move(self, dt: float, x: float, y: float):
        ...

    @abstractmethod
    def select(self, dt: float):
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


class KeyboardPlayerController(PlayerController):
    def __init__(
        self,
        controllable: PlayerControllable,
        max_jump_count: int,
        max_jump_time: float,
    ) -> None:
        self._jump = CounterTimer(controllable.jump, max_jump_count, max_jump_time)

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
        ]

    def control(self, dt: float):
        self._perform_cursor_movement(dt)

        for d_keys, action in self.direction_key_actions:
            left, right = d_keys
            keys = pygame.key.get_pressed()
            if keys[left] and keys[right]:
                x = 0
            elif keys[left]:
                x = -1
            elif keys[right]:
                x = 1
            else:
                x = 0
            action.do(True, dt, [x])

        for key, action in self.key_actions:
            value = pygame.key.get_pressed()[key]
            action.do(value, dt)

        for key, action in self.mouse_button_actions:
            value = pygame.mouse.get_pressed()[key]
            action.do(value, dt)

    def _perform_cursor_movement(self, dt: float):
        # assuming player position on center
        mouse_position = pygame.math.Vector2(pygame.mouse.get_pos())
        middle_screen = pygame.math.Vector2(pygame.display.get_surface().get_size()) / 2
        rel = mouse_position - middle_screen
        rel = rel.clamp_magnitude(BLOCK_SIZE * 5) / (BLOCK_SIZE * 5)
        axes_values = [round(rel.x, 2), round(rel.y, 2)]
        self.move_cursor.do(True, dt, axes_values)

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
            x, y = self.joystick.get_hat(hat)
            action.do(bool(y), dt, [x, y])

        for button, action in self.button_actions:
            value = self.joystick.get_button(button)
            action.do(value, dt)


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
                x = 0
            elif keys[up]:
                x = 1
            elif keys[down]:
                x = -1
            else:
                x = 0

            if keys[left] and keys[right]:
                y = 0
            elif keys[left]:
                y = 1
            elif keys[right]:
                y = -1
            else:
                y = 0
            action.do(bool(x or y), dt, [x, y])

        for key, action in self.key_actions:
            value = pygame.key.get_pressed()[key]
            action.do(value, dt)


class ControllerDetection:
    CONTROLLER_DETECTED = pygame.event.custom_type()
    EVENTS = [CONTROLLER_DETECTED]

    class Controller(enum.IntEnum):
        AI = enum.auto()
        KEYBOARD = enum.auto()
        JOYSTICK = enum.auto()

    def __init__(self) -> None:
        self.joystick_count = 0
        self.animation_time = 500
        self.display = pygame.display.get_surface()
        self.surface = pygame.surface.Surface(self.display.get_size())
        self.font = pygame.font.Font(MENU_FONT, 100)
        self.draw_static()

    def run(self, dt: float):
        self.draw(dt)
        self.detect_controller()

    def draw_static(self):
        self.surface.fill("black")

    def draw(self, _: float):
        text = self.font.render("Press any key/button", False, "white")
        self.surface.blit(text, (0, 0))
        self.display.blit(self.surface, self.display.get_rect())

    def detect_controller(self):
        joysticks = pygame.joystick.get_count()
        if self.joystick_count != joysticks:
            self.joystick_count = joysticks
            print(f"Joysticks detected: {joysticks}")

        if self.joystick_count > 0:
            if self.detect_joystick():
                return

        self.detect_keyboard_and_mouse()

    def detect_joystick(self):
        for joystick_id in range(self.joystick_count):
            joystick = pygame.joystick.Joystick(joystick_id)
            for button_id in range(joystick.get_numbuttons()):
                if joystick.get_button(button_id):
                    event = pygame.event.Event(self.CONTROLLER_DETECTED)
                    event.controller = self.Controller.JOYSTICK
                    pygame.event.post(event)
                    return True
        return False

    def detect_keyboard_and_mouse(self):
        r = pygame.key.get_pressed()

        # HACK: pygame prevents iterating directly over r
        if any(r[i] for i in range(len(r))):
            event = pygame.event.Event(self.CONTROLLER_DETECTED)
            event.controller = self.Controller.KEYBOARD
            pygame.event.post(event)
            return True
        return False
