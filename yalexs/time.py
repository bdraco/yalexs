import datetime
from typing import Optional, Union

import ciso8601
import dateutil.parser


def parse_datetime(datetime_string: str) -> datetime.datetime:
    """Parse a datetime string."""
    try:
        ciso8601.parse_datetime(datetime_string)
    except ValueError:
        return dateutil.parser.parse(datetime_string)
