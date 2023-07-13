from array import array
from typing import Any

import moderngl as mgl
import pygame
from moderngl import TRIANGLE_STRIP, Context, Program

from settings import BASE_DIR, SCREEN_HEIGHT, SCREEN_WIDTH


def load_program(ctx: Context, name: str):
    dir = BASE_DIR / "shaders"
    with open(dir / f"{name}.vert") as file:
        vertex_shader = file.read()

    with open(dir / f"{name}.frag") as file:
        fragment_shader = file.read()

    return ctx.program(
        vertex_shader=vertex_shader,
        fragment_shader=fragment_shader,
    )


def load_vao(
    ctx: Context, data: Any, program: Program, format: str, attributes: list[str]
):
    buffer = ctx.buffer(data)
    return ctx.vertex_array(program, [(buffer, format, *attributes)])


class Shader:
    def __init__(
        self, ctx: Context, name: str, data: Any, format: str, attributes: list[str]
    ) -> None:
        self.ctx = ctx
        self.prog = load_program(self.ctx, name)
        self.vao = load_vao(self.ctx, data, self.prog, format, attributes)

    def render(self, mode: int | None = None):
        self.vao.render(mode=mode or TRIANGLE_STRIP)  # type: ignore


class TextureShader(Shader):
    def __init__(self, ctx: Context) -> None:
        upper_left = (-1.0, 1.0, 0.0, 1.0)
        lower_left = (-1.0, -1.0, 0.0, 0.0)
        upper_right = (1.0, 1.0, 1.0, 1.0)
        lower_right = (1.0, -1.0, 1.0, 0.0)
        data = array("f", upper_left + lower_left + upper_right + lower_right)
        super().__init__(ctx, "def", data, "2f 2f", ["in_vert", "in_texcoord"])
        self.prog["surface"] = 0

        self.pg_texture = self.ctx.texture((SCREEN_WIDTH, SCREEN_HEIGHT), 4)
        self.pg_texture.filter = (mgl.NEAREST, mgl.NEAREST)  # type: ignore
        self.pg_texture.swizzle = "BGRA"

    def render(self, surface: pygame.surface.Surface):
        self.pg_texture.use(location=0)
        self.pg_texture.write(surface.get_view("1"))
        super().render()
