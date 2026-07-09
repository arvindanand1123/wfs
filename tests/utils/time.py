from datetime import UTC, datetime


class TimeUtils:
    @classmethod
    def now(cls, as_string=False):
        ts = datetime.now(UTC)
        if as_string:
            return str(ts)
        else:
            return ts
