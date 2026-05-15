# src/utils/time.py
from datetime import datetime, timedelta

def minutes_to_timedelta(minutes: int) -> timedelta:
    return timedelta(minutes=minutes)

def now_utc() -> datetime:
    return datetime.utcnow()