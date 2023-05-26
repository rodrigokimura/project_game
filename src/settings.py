import os
from pathlib import Path

DEBUG = bool(os.getenv("DEBUG", ""))

BLOCK_SIZE = 16

TITLE = "Project Game"

if DEBUG:
    SCREEN_WIDTH = 80 * BLOCK_SIZE  # 1280
    SCREEN_HEIGHT = 45 * BLOCK_SIZE  # 720
else:
    SCREEN_WIDTH = 120 * BLOCK_SIZE  # 1920
    SCREEN_HEIGHT = int(67.5 * BLOCK_SIZE)  # 1080

WORLD_SIZE = 8 * 80, 8 * 45
# WORLD_SIZE = 50 * 80, 50 * 45
DAY_DURATION = 10
# DAY_DURATION = 15 * 60

GRAVITY = 30
TERMINAL_VELOCITY = 30


PROJECT_DIR = Path(os.path.dirname(os.path.realpath(__file__)))

# DEFAULT_FONT = "freesansbold"
DEFAULT_FONT = PROJECT_DIR / "assets" / "pixeldroidBoticRegular.ttf"
CONSOLE_FONT = PROJECT_DIR / "assets" / "pixeldroidConsoleRegular.ttf"
MENU_FONT = PROJECT_DIR / "assets" / "pixeldroidMenuRegular.ttf"
