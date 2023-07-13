#version 330

layout (location = 0) in vec2 in_vert;

uniform vec2 pos;

void main() {
  vec2 res = vec2(320, 180);
  vec2 size = vec2(8, 8);

  vec2 _pos = pos - res / 2;
  _pos = _pos * vec2(1, -1);
  _pos = _pos / res * 4;

  size = size / res * 2;
  mat4 _size = mat4(1);
  _size[0][0] = size[0];
  _size[1][1] = size[1];
  gl_Position = _size * vec4(in_vert, 0.0, 1.0) + vec4(_pos, 0.0, 1.0);
}
