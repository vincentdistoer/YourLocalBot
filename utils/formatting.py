import datetime, discord
from discord.ext import commands
from typing import Union

class Times:
    @property
    def utc(cls):
        return datetime.datetime.utcnow()


class Humanreadable:

    @classmethod
    def date(cls, datetime_format):
        return datetime_format.strftime('%d/%m/%Y %Z')

    @classmethod
    def time(cls, datetime_format):
        return datetime_format.strftime("%I:%M %p")

    @classmethod
    def both(cls, datetime_format):
        return datetime_format.strftime(f"{cls.time(datetime_format)} @ {cls.date(datetime_format)}")

    @classmethod
    def dynamic_time(cls, time):
        date_join = datetime.datetime.strptime(str(time), "%Y-%m-%d %H:%M:%S.%f")
        date_now = datetime.datetime.now(datetime.timezone.utc)
        date_now = date_now.replace(tzinfo=None)
        since_join = date_now - date_join

        m, s = divmod(int(since_join.total_seconds()), 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        if d > 0:
            msg = "{0}d {1}h {2}m {3}s ago"
        elif d == 0 and h > 0:
            msg = "{1}h {2}m {3}s ago"
        elif d == 0 and h == 0 and m > 0:
            msg = "{2}m {3}s ago"
        elif d == 0 and h == 0 and m == 0 and s > 0:
            msg = "{3}s ago"
        else:
            msg = ""
        return msg.format(d, h, m, s)

    @classmethod
    def to_minutes(cls, time):
        date_join = datetime.datetime.strptime(str(time), "%Y-%m-%d %H:%M:%S.%f")
        date_now = datetime.datetime.now(datetime.timezone.utc)
        date_now = date_now.replace(tzinfo=None)
        since_join = date_now - date_join

        m, s = divmod(int(since_join.total_seconds()), 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return m

class ABCs:
    @staticmethod
    def alpha():
        return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i',
        'j', 'k', 'l', 'm', 'n', 'o', 'o', 'p', 'q', 'r', 's', 't',
        'u', 'v', 'w', 'x', 'y', 'z']
    @staticmethod
    def num():
        return [1,2,3,4,5,6,7,8,9,0]
