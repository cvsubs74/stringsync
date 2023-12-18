import enum
import datetime

import pytz


class TimeFrame(enum.Enum):
    CURRENT_WEEK = 'Current Week'
    PREVIOUS_WEEK = 'Previous Week'
    CURRENT_MONTH = 'Current Month'
    PREVIOUS_MONTH = 'Previous Month'
    CURRENT_YEAR = 'Current Year'
    PREVIOUS_YEAR = 'Previous Year'
    HISTORICAL = 'Historical Data'

    @classmethod
    def choices(cls):
        # This will return a list of tuples (enum_member, enum_member.value)
        return [(item, item.value) for item in cls]

    def get_date_range(self, timezone='America/Los_Angeles'):
        # Get today's date as a date object
        tz = pytz.timezone(timezone)
        now = datetime.datetime.now(tz)
        today = now.date()

        if self == TimeFrame.CURRENT_WEEK:
            start_date = today - datetime.timedelta(days=today.weekday())  # Monday
            end_date = start_date + datetime.timedelta(days=7, seconds=-1)
        elif self == TimeFrame.PREVIOUS_WEEK:
            start_date = today - datetime.timedelta(days=today.weekday() + 7)
            end_date = start_date + datetime.timedelta(days=7, seconds=-1)
        elif self == TimeFrame.CURRENT_MONTH:
            start_date = today.replace(day=1)
            # Calculate end date as the first day of the next month, then subtract one second
            end_date = (start_date + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(seconds=1)
        elif self == TimeFrame.PREVIOUS_MONTH:
            first_day_current_month = today.replace(day=1)
            start_date = (first_day_current_month - datetime.timedelta(days=1)).replace(day=1)
            end_date = first_day_current_month - datetime.timedelta(seconds=1)
        elif self == TimeFrame.CURRENT_YEAR:
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(year=today.year + 1, month=1, day=1) - datetime.timedelta(seconds=1)
        elif self == TimeFrame.PREVIOUS_YEAR:
            start_date = today.replace(year=today.year - 1, month=1, day=1)
            end_date = today.replace(month=1, day=1) - datetime.timedelta(seconds=1)
        elif self == TimeFrame.HISTORICAL:
            start_date = datetime.date.min
            end_date = datetime.datetime.combine(today, datetime.time(23, 59))
        else:
            # Default case or unrecognized timeframe
            start_date = today
            end_date = today + datetime.timedelta(days=1, seconds=-1)

        return start_date, end_date
