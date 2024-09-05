from __future__ import annotations

import datetime
import typing as t

import pendulum

from pendulum.duration import Duration
from pendulum.parsing import _Interval
from pendulum.parsing import parse as base_parse
from pendulum.tz.timezone import UTC


if t.TYPE_CHECKING:
    from pendulum.date import Date
    from pendulum.datetime import DateTime
    from pendulum.interval import Interval
    from pendulum.time import Time

try:
    from pendulum._pendulum import Duration as RustDuration
except ImportError:
    RustDuration = None  # type: ignore[assignment,misc]


def parse(text: str, **options: t.Any) -> Date | Time | DateTime | Duration:
    """
    Converts a given text into a date or time object based on specific parsing
    rules and options provided through keyword arguments. It sets an option for
    now, if not already set, before calling another internal _parse function to
    perform the actual parsing.

    Args:
        text (str*): Required for the function to execute. It represents the input
            string that needs to be parsed into a date or time-related object.
        **options (t.Any*): Dictionary of keyword arguments

    Returns:
        Date | Time | DateTime | Duration*: An object representing a date and/or
        time, possibly with duration information. The exact type depends on the
        input text and options provided.

    """
    # Use the mock now value if it exists
    options["now"] = options.get("now")

    return _parse(text, **options)


def _parse(text: str, **options: t.Any) -> Date | DateTime | Time | Duration | Interval:
    """
    Handles date and time parsing from a given text string, converting it into
    various formats such as dates, times, durations, or intervals using the
    `pendulum` library. It also accommodates special cases like "now" and supports
    timezone handling.

    """
    # Handling special cases
    if text == "now":
        return pendulum.now()

    parsed = base_parse(text, **options)

    if isinstance(parsed, datetime.datetime):
        return pendulum.datetime(
            parsed.year,
            parsed.month,
            parsed.day,
            parsed.hour,
            parsed.minute,
            parsed.second,
            parsed.microsecond,
            tz=parsed.tzinfo or options.get("tz", UTC),
        )

    if isinstance(parsed, datetime.date):
        return pendulum.date(parsed.year, parsed.month, parsed.day)

    if isinstance(parsed, datetime.time):
        return pendulum.time(
            parsed.hour, parsed.minute, parsed.second, parsed.microsecond
        )

    if isinstance(parsed, _Interval):
        if parsed.duration is not None:
            duration = parsed.duration

            if parsed.start is not None:
                dt = pendulum.instance(parsed.start, tz=options.get("tz", UTC))

                return pendulum.interval(
                    dt,
                    dt.add(
                        years=duration.years,
                        months=duration.months,
                        weeks=duration.weeks,
                        days=duration.remaining_days,
                        hours=duration.hours,
                        minutes=duration.minutes,
                        seconds=duration.remaining_seconds,
                        microseconds=duration.microseconds,
                    ),
                )

            dt = pendulum.instance(
                t.cast(datetime.datetime, parsed.end), tz=options.get("tz", UTC)
            )

            return pendulum.interval(
                dt.subtract(
                    years=duration.years,
                    months=duration.months,
                    weeks=duration.weeks,
                    days=duration.remaining_days,
                    hours=duration.hours,
                    minutes=duration.minutes,
                    seconds=duration.remaining_seconds,
                    microseconds=duration.microseconds,
                ),
                dt,
            )

        return pendulum.interval(
            pendulum.instance(
                t.cast(datetime.datetime, parsed.start), tz=options.get("tz", UTC)
            ),
            pendulum.instance(
                t.cast(datetime.datetime, parsed.end), tz=options.get("tz", UTC)
            ),
        )

    if isinstance(parsed, Duration):
        return parsed

    if RustDuration is not None and isinstance(parsed, RustDuration):
        return pendulum.duration(
            years=parsed.years,
            months=parsed.months,
            weeks=parsed.weeks,
            days=parsed.days,
            hours=parsed.hours,
            minutes=parsed.minutes,
            seconds=parsed.seconds,
            microseconds=parsed.microseconds,
        )

    raise NotImplementedError
