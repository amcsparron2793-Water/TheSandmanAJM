from typing import Optional
from datetime import datetime


class SnoozeExpirationMixin:
    DEFAULT_SNOOZE_EXPIRATION_LIMIT_HOURS = 24
    SECONDS_IN_HOUR = 3600

    @classmethod
    def is_snooze_expired(cls, snoozed_at: datetime, snooze_expiration_limit_hours: Optional[int] = None):
        if not snooze_expiration_limit_hours:
            snooze_expiration_limit_hours = cls.DEFAULT_SNOOZE_EXPIRATION_LIMIT_HOURS
        snooze_expiration_limit_seconds = snooze_expiration_limit_hours * cls.SECONDS_IN_HOUR
        time_since_snooze = (datetime.now() - snoozed_at)
        if time_since_snooze.total_seconds() >= snooze_expiration_limit_seconds:
            #print('msg_snoozed expired! Unsnoozing now!')
            return True
        return False
