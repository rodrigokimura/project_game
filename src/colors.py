import enum

from pygame.color import Color as _Color


class Color(_Color, enum.Enum):
    TRANSPARENT = _Color(0, 0, 0, 0)
    PURE_WHITE = _Color("#ffffff")
    PURE_BLACK = _Color("#000000")
    SKY = _Color("#bde0fe")
    LEAF_FILL = _Color("#2a9d8f")
    LEAF_BORDER = _Color("#344e41")
    TRUNK_FILL = _Color("#d4a373")
    TRUNK_BORDER = _Color("#bc6c25")
    MOUNTAIN_1 = _Color("#d5bdaf")
    MOUNTAIN_2 = _Color("#e3d5ca")
    MOUNTAIN_3 = _Color("#f5ebe0")
    ROCK_FILL = _Color("#8d99ae")
    ROCK_BORDER = _Color("#2b2d42")
    CURSOR = _Color("#ca6702")
    PLAYER_PRIMARY = _Color("#2b2d42")
    PLAYER_SECONDARY = _Color("#cad2c5")
    ENEMY_PRIMARY = _Color("#7209b7")
    ENEMY_SECONDARY = _Color("#3a0ca3")
    BULLET = _Color("#dc2f02")


class InterfaceColor(_Color, enum.Enum):
    AIM_ASSIST_LINE = _Color("#ef233c")
    BLOCK_CURSOR = _Color("#fb5607")
    HEALTH_POINTS = _Color("#d90429")
    HEALTH_POINTS_BAR_BORDER = _Color("#d9d9d9")
    PRIMARY_FONT = _Color("#d9d9d9")
    BORDER = _Color("#edf2f4")
    MENU_BACKGROUND = _Color("#353535")
    MENU_BORDER = _Color("#d9d9d9")
    MENU_HIGHLIGHT = _Color("#caf0f8")
    INVENTORY_HIGHLIGHT = _Color("#e5e5e5")
    INVENTORY_BACKROUND = _Color("#3535350f")
    INVENTORY_ITEM_BORDER = _Color("#8d99ae")
