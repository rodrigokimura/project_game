import enum
from datetime import datetime, time, timedelta


class DayPart(enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


def convert_to_time(relative_time: float) -> time:
    return (datetime(1, 1, 1) + timedelta(days=relative_time)).time()


def get_day_part(_time: time) -> DayPart:
    if _time < time(5):
        return DayPart.NIGHT
    if _time < time(12):
        return DayPart.MORNING
    if _time < time(17):
        return DayPart.AFTERNOON
    if _time < time(21):
        return DayPart.EVENING
    return DayPart.NIGHT
