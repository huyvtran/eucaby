"""Dates utils."""

import datetime


class FixedOffset(datetime.tzinfo):
    """Subclass with tzinfo interface with fixed offset."""

    def __init__(self, offset=0):
        self._offset = datetime.timedelta(minutes=offset)

    def utcoffset(self, date_time):
        return self._offset

    def tzname(self, date_time):
        # Example: "-7:0"
        hours = self._offset/60
        minutes = self._offset - hours*60
        return '{}:{}'.format(hours, minutes)

    def dst(self, date_time):
        return datetime.timedelta(0)


def timezone_date(dt, offset):
    """Presents datetime in the timezone."""
    if offset is None:
        return dt
    # If timezone information is missing set it to UTC
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=FixedOffset(0))

    return dt.astimezone(FixedOffset(offset))
