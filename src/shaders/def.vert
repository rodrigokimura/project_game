#version 330
// Vertex shader runs once for each vertex in the geometry

in vec2 in_vert;
in vec2 in_texcoord;
out vec2 uv;

void main() {
  // Send the texture coordinates to the fragment shader
  uv = in_texcoord;
  // Resolve the vertex position
  gl_Position = vec4(in_vert, 0.0, 1.0);
}
