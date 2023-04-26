from abc import ABC

from collectibles import BaseCollectible


class BaseInventory(ABC):
    collectibles: dict[type[BaseCollectible], int]

    def add(self, collectible: BaseCollectible):
        if collectible.__class__ in self.collectibles:
            self.collectibles[collectible.__class__] += 1
        else:
            self.collectibles[collectible.__class__] = 1

    def remove(self, collectible: BaseCollectible):
        if collectible.__class__ in self.collectibles:
            if self.collectibles[collectible.__class__] > 0:
                self.collectibles[collectible.__class__] -= 1
            else:
                del self.collectibles[collectible.__class__]

    def __str__(self) -> str:
        return str(self.collectibles)


class Inventory(BaseInventory):
    """Simple limitless inventory"""

    def __init__(self) -> None:
        self.collectibles: dict[type[BaseCollectible], int] = {}
