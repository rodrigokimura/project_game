from enum import IntEnum


class CyclingIntEnum(IntEnum):
    @classmethod
    def _missing_(cls, value: int):
        if value < 1:
            return list(cls)[-1]
        return list(cls)[0]
