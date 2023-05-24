import enum
from datetime import datetime, time, timedelta


class DayPart(enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


def convert_to_time(relative_time: float) -> time:
    return (datetime(1, 1, 1) + timedelta(days=relative_time)).time()


def get_day_part(t: time) -> DayPart:
    if t < time(5):
        return DayPart.NIGHT
    if t < time(12):
        return DayPart.MORNING
    if t < time(17):
        return DayPart.AFTERNOON
    if t < time(21):
        return DayPart.EVENING
    return DayPart.NIGHT
