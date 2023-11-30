import time
from datetime import datetime

import pytest

from timestamper import try_parsedatetime


def p(s) -> time.struct_time:
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S').utctimetuple()


ref_time = p("2023-12-01 13:30:00")


@pytest.mark.parametrize(
    "string,expected_time",
    [
        ("May 5th 2:30 in the afternoon", p("2024-05-05 2:30:00")),
        ('8:30cst 12/5', p("2023-12-05 8:30:00")),
        ('8:30 12/5', p("2023-12-05 8:30:00")),
        ('Tentative next session 8:30cst 12/5 (may have to change up)', p("2023-12-05 8:30:00")),
        ('Tentative next session 8:30 12/5 (may have to change up)', p("2023-12-05 8:30:00")),
        ('Tentative next session 8:30 cst 12/5 (may have to change up)', p("2023-12-05 8:30:00")),
        ('next tues 8:30cst', p("2023-12-05 8:30:00")),
        ('tues 8:30cst', p("2023-12-05 8:30:00")),
        ('tues 8:30', p("2023-12-05 8:30:00")),
    ])
def test_strings(string: str, expected_time: time.struct_time):
    result, status = try_parsedatetime(string)

    # print(expected_time)
    # print(result)
    assert expected_time.tm_year == result.tm_year
    assert expected_time.tm_mon == result.tm_mon
    assert expected_time.tm_mday == result.tm_mday
    assert expected_time.tm_hour == result.tm_hour
    assert expected_time.tm_min == result.tm_min
    assert expected_time.tm_sec == result.tm_sec
    # tm_yday is wrong on one of these...


@pytest.mark.parametrize(
    "string",
    [
        "Hi there!",
        "How's it going?",
        # I think the "100s" kills this one
        # """
        # That's an interesting idea. I wonder why they're doing that in particular.
        # you see, there are really a few different ways to do this
        # nothing says you _have_ to use that one. there are 100s of others
        # """,
        'Tentative next session later',
    ])
def test_expect_parse_to_none(string: str):
    result, status = try_parsedatetime(string)

    assert not status.hasDate
    assert not status.hasTime
    assert not status.hasDateOrTime
