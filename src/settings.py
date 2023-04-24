import os

BLOCK_SIZE = 16

TITLE = "Project Game"
SCREEN_WIDTH = 80 * BLOCK_SIZE  # 1280
SCREEN_HEIGHT = 45 * BLOCK_SIZE  # 720

WORLD_SIZE = 8 * 80, 8 * 45
# WORLD_SIZE = 50 * 80, 50 * 45
DAY_DURATION = 10
# DAY_DURATION = 15 * 60

GRAVITY = 30
TERMINAL_VELOCITY = 30

DEBUG = bool(os.getenv("DEBUG", False))
