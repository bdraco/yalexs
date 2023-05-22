import datetime

import ciso8601
import dateutil.parser


def parse_datetime(datetime_string: str) -> datetime.datetime:
    """Parse a datetime string."""
    try:
        return ciso8601.parse_datetime(datetime_string)
    except ValueError:
        return dateutil.parser.parse(datetime_string)
