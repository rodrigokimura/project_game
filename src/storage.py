import shelve
from abc import ABC, abstractmethod
from uuid import UUID

from characters import BaseCharacter
from commons import Storable
from log import log
from world import BaseWorld


class BaseStorage(ABC):
    @abstractmethod
    def get(self, _id: UUID) -> Storable:
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
        with shelve.open(self.filename) as database:
            database[str(item.id)] = item
        log(f"Saved to {self.filename}")
        return True

    def get(self, _id: UUID) -> Storable:
        with shelve.open(self.filename) as database:
            log(f"Loaded from {self.filename}")
            return database[str(_id)]

    def delete(self, item: Storable) -> bool:
        with shelve.open(self.filename) as database:
            try:
                del database[str(item.id)]
            except KeyError:
                return False
        log(f"Deleted from {self.filename}")
        return True

    def list_all(self) -> list[Storable]:
        with shelve.open(self.filename) as database:
            log(f"Loaded from {self.filename}")
            return list(database.values())

    def clear(self):
        with shelve.open(self.filename) as database:
            database.clear()
            log(f"Deleted all records from {self.filename}")


class WorldStorage(ShelveStorage):
    def __init__(self) -> None:
        super().__init__("world_db")

    def store(self, world: BaseWorld) -> bool:
        if not isinstance(world, BaseWorld):
            raise ValueError("Cannot store non-worlds in WorldStorage")
        world.unload()
        return super().store(world)

    def get(self, _id: UUID) -> BaseWorld:
        world = super().get(_id)
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

    def store(self, player: BaseCharacter) -> bool:
        if not isinstance(player, BaseCharacter):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.unload()
        return super().store(player)

    def get(self, _id: UUID) -> BaseCharacter:
        player = super().get(_id)
        if not isinstance(player, BaseCharacter):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.setup()
        return player

    def get_oldest(self) -> BaseCharacter:
        player = super().get_oldest()
        if not isinstance(player, BaseCharacter):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.setup()
        return player

    def get_newest(self) -> BaseCharacter:
        player = super().get_newest()
        if not isinstance(player, BaseCharacter):
            raise ValueError("Cannot store non-players in PlayerStorage")
        player.setup()
        return player
