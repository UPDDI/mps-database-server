import collections

# Variable to indicate that these should be split for special filters
COMBINED_VALUE_DELIMITER = '~@|'

INTERVAL_1_SIGIL = '     ~@i1'
INTERVAL_2_SIGIL = '     ~@i2'
SHAPE_SIGIL = '     ~@s'
TOOLTIP_SIGIL = '     ~@t'

# This shouldn't be repeated like so
# Converts: days -> minutes, hours -> minutes, minutes->minutes
TIME_CONVERSIONS = [
    ('day', 1440),
    ('hour', 60),
    ('minute', 1)
]

TIME_CONVERSIONS = collections.OrderedDict(TIME_CONVERSIONS)


# TODO EMPLOY THIS FUNCTION ELSEWHERE
def get_split_times(time_in_minutes):
    """Takes time_in_minutes and returns a dic with the time split into day, hour, minute"""
    times = {
        'day': 0,
        'hour': 0,
        'minute': 0
    }
    time_in_minutes_remaining = time_in_minutes
    for time_unit, conversion in list(TIME_CONVERSIONS.items()):
        initial_time_for_current_field = int(time_in_minutes_remaining / conversion)
        if initial_time_for_current_field:
            times[time_unit] = initial_time_for_current_field
            time_in_minutes_remaining -= initial_time_for_current_field * conversion
    # Add fractions of minutes if necessary
    if time_in_minutes_remaining:
        times['minute'] += time_in_minutes_remaining

    return times
