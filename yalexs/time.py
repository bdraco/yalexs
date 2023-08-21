from __future__ import annotations

import datetime
from functools import lru_cache

import ciso8601
import dateutil.parser


@lru_cache(maxsize=512)
def epoch_to_datetime(epoch: str | int | float) -> datetime.datetime:
    """Convert epoch to datetime."""
    return datetime.datetime.fromtimestamp(float(epoch) / 1000.0)


def parse_datetime(datetime_string: str) -> datetime.datetime:
    """Parse a datetime string."""
    try:
        return ciso8601.parse_datetime(datetime_string)
    except ValueError:
        return dateutil.parser.parse(datetime_string)
