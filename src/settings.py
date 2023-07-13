import os
from pathlib import Path

DEBUG = bool(os.getenv("DEBUG", ""))

BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))

BLOCK_SIZE = 16

TITLE = "Project Game"

SCREEN_WIDTH = 80 * BLOCK_SIZE  # 1280
SCREEN_HEIGHT = 45 * BLOCK_SIZE  # 720

# SCREEN_WIDTH = 120 * BLOCK_SIZE  # 1920
# SCREEN_HEIGHT = int(67.5 * BLOCK_SIZE)  # 1080

WORLD_SIZE = 8 * 80, 8 * 45
if DEBUG:
    WORLD_SIZE = 2 * 80, 2 * 45

# WORLD_SIZE = 50 * 80, 50 * 45
DAY_DURATION = 10
# DAY_DURATION = 15 * 60

MAX_SURROUNDING_LENGTH = (SCREEN_WIDTH + SCREEN_HEIGHT) * 2 // BLOCK_SIZE

GRAVITY = 50
TERMINAL_VELOCITY = 30


PROJECT_DIR = Path(os.path.dirname(os.path.realpath(__file__)))

DEFAULT_FONT = PROJECT_DIR / "assets" / "pixeldroidBoticRegular.ttf"
CONSOLE_FONT = PROJECT_DIR / "assets" / "pixeldroidConsoleRegular.ttf"
MENU_FONT = PROJECT_DIR / "assets" / "pixeldroidMenuRegular.ttf"
