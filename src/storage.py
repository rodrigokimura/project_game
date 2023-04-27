import shelve
from abc import ABC, abstractmethod
from uuid import UUID

from commons import Storable
from log import log
from player import BasePlayer
from world import BaseWorld


class BaseStorage(ABC):
    @abstractmethod
    def get(self, id: UUID) -> Storable:
        ...

    @abstractmethod
    def store(self, item: Storable) -> bool:
        ...

    @abstractmethod
    def delete(self, item: Storable) -> bool:
        ...

    @abstractmethod
    def list_all(self) -> list[Storable]:
        ...

    def get_oldest(self) -> Storable:
        items = self.list_all()
        items.sort(key=lambda i: i.saved_at)
        return items[0]

    def get_newest(self) -> Storable:
        items = self.list_all()
        items.sort(key=lambda i: i.saved_at, reverse=True)
        return items[0]


class ShelveStorage(BaseStorage):
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def store(self, item: Storable) -> bool:
        print("updating timestamp")
        item.update_timestamp()
        with shelve.open(self.filename) as d:
            d[str(item.id)] = item
        log(f"Saved to {self.filename}")
        return True

    def get(self, id: UUID) -> Storable:
        with shelve.open(self.filename) as d:
            log(f"Loaded from {self.filename}")
            return d[str(id)]

    def delete(self, item: Storable) -> bool:
        with shelve.open(self.filename) as d:
            try:
                del d[str(item.id)]
            except KeyError:
                return False
        log(f"Deleted from {self.filename}")
        return True

    def list_all(self) -> list[Storable]:
        with shelve.open(self.filename) as d:
            log(f"Loaded from {self.filename}")
            return list(d.values())

    def clear(self):
        with shelve.open(self.filename) as d:
            d.clear()
            log(f"Deleted all records from {self.filename}")


class WorldStorage(ShelveStorage):
    def __init__(self) -> None:
        super().__init__("world_db")

    def store(self, world: BaseWorld) -> bool:
        if not isinstance(world, BaseWorld):
            raise ValueError("Cannot store non-worlds in WorldStorage")
        return super().store(world)

    def get(self, id: UUID) -> BaseWorld:
        world = super().get(id)
        if not isinstance(world, BaseWorld):
            raise ValueError("Cannot store non-worlds in WorldStorage")
        return world

    def get_oldest(self) -> BaseWorld:
        world = super().get_oldest()
        if not isinstance(world, BaseWorld):
            raise ValueError("Cannot store non-worlds in WorldStorage")
        return world

    def get_newest(self) -> BaseWorld:
        world = super().get_newest()
        if not isinstance(world, BaseWorld):
            raise ValueError("Cannot store non-worlds in WorldStorage")
        return world


class PlayerStorage(ShelveStorage):
    def __init__(self) -> None:
        super().__init__("player_db")

    def store(self, player: BasePlayer) -> bool:
        if not isinstance(player, BasePlayer):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.unload()
        return super().store(player)

    def get(self, id: UUID) -> BasePlayer:
        player = super().get(id)
        if not isinstance(player, BasePlayer):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.setup()
        return player

    def get_oldest(self) -> BasePlayer:
        player = super().get_oldest()
        if not isinstance(player, BasePlayer):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.setup()
        return player

    def get_newest(self) -> BasePlayer:
        player = super().get_newest()
        if not isinstance(player, BasePlayer):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.setup()
        return player
