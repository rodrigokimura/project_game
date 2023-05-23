from datetime import time

from day_cycle import DayPart, convert_to_time, get_day_part


def test_convert_to_time():
    m = {
        0: "00:00:00",
        0.25: "06:00:00",
        0.5: "12:00:00",
        0.75: "18:00:00",
    }
    for k, v in m.items():
        t = convert_to_time(k)
        assert str(t) == v


def test_get_day_part():
    m = {
        time(5): DayPart.MORNING,
        time(6): DayPart.MORNING,
        time(10): DayPart.MORNING,
        time(11): DayPart.MORNING,
        time(12): DayPart.AFTERNOON,
        time(15): DayPart.AFTERNOON,
        time(16): DayPart.AFTERNOON,
        time(17): DayPart.EVENING,
        time(20): DayPart.EVENING,
        time(21): DayPart.NIGHT,
        time(22): DayPart.NIGHT,
        time(1): DayPart.NIGHT,
        time(4): DayPart.NIGHT,
    }
    for k, v in m.items():
        dp = get_day_part(k)
        assert dp == v
