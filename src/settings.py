import os

TITLE = "Project Game"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

BLOCK_SIZE = 16
WORLD_SIZE = 200, 200
GRAVITY = 20

DEBUG = bool(os.getenv("DEBUG", False))
