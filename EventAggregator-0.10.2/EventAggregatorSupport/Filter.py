# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator event filtering functionality.

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from DateSupport import DateTime, Timespan, TimespanCollection, \
                        getCurrentDate, getCurrentMonth, cmp_dates_as_day_start

try:
    set
except NameError:
    from sets import Set as set

# Sortable values representing start and end limits of timespans/events.

START, END = 0, 1

# Event filtering and limits.

def getEventsInPeriod(events, calendar_period):

    """
    Return a collection containing those of the given 'events' which occur
    within the given 'calendar_period'.
    """

    all_shown_events = []

    for event in events:

        # Test for the suitability of the event.

        if event.as_timespan() is not None:

            # Compare the dates to the requested calendar window, if any.

            if event in calendar_period:
                all_shown_events.append(event)

    return all_shown_events

def getEventLimits(events):

    "Return the earliest and latest of the given 'events'."

    earliest = None
    latest = None

    for event in events:

        # Test for the suitability of the event.

        if event.as_timespan() is not None:
            ts = event.as_timespan()
            if earliest is None or ts.start < earliest:
                earliest = ts.start
            if latest is None or ts.end > latest:
                latest = ts.end

    return earliest, latest

def getLatestEventTimestamp(events):

    """
    Return the latest timestamp found from the given 'events'.
    """

    latest = None

    for event in events:
        metadata = event.getMetadata()

        if latest is None or latest < metadata["last-modified"]:
            latest = metadata["last-modified"]

    return latest

def getCalendarPeriod(calendar_start, calendar_end):

    """
    Return a calendar period for the given 'calendar_start' and 'calendar_end'.
    These parameters can be given as None.
    """

    # Re-order the window, if appropriate.

    if calendar_start is not None and calendar_end is not None and calendar_start > calendar_end:
        calendar_start, calendar_end = calendar_end, calendar_start

    return Timespan(calendar_start, calendar_end)

def getConcretePeriod(calendar_start, calendar_end, earliest, latest, resolution):

    """
    From the requested 'calendar_start' and 'calendar_end', which may be None,
    indicating that no restriction is imposed on the period for each of the
    boundaries, use the 'earliest' and 'latest' event months to define a
    specific period of interest.
    """

    # Define the period as starting with any specified start month or the
    # earliest event known, ending with any specified end month or the latest
    # event known.

    first = calendar_start or earliest
    last = calendar_end or latest

    # If there is no range of months to show, perhaps because there are no
    # events in the requested period, and there was no start or end month
    # specified, show only the month indicated by the start or end of the
    # requested period. If all events were to be shown but none were found show
    # the current month.

    if resolution == "date":
        get_current = getCurrentDate
    else:
        get_current = getCurrentMonth

    if first is None:
        first = last or get_current()
    if last is None:
        last = first or get_current()

    if resolution == "month":
        first = first.as_month()
        last = last.as_month()

    # Permit "expiring" periods (where the start date approaches the end date).

    return min(first, last), last

def getCoverage(events, resolution="date"):

    """
    Determine the coverage of the given 'events', returning a collection of
    timespans, along with a dictionary mapping locations to collections of
    slots, where each slot contains a tuple of the form (timespans, events).
    """

    all_events = {}
    full_coverage = TimespanCollection(resolution)

    # Get event details.

    for event in events:
        event_details = event.getDetails()

        # Find the coverage of this period for the event.

        # For day views, each location has its own slot, but for month
        # views, all locations are pooled together since having separate
        # slots for each location can lead to poor usage of vertical space.

        if resolution == "datetime":
            event_location = event_details.get("location")
        else:
            event_location = None

        # Update the overall coverage.

        full_coverage.insert_in_order(event)

        # Add a new events list for a new location.
        # Locations can be unspecified, thus None refers to all unlocalised
        # events.

        if not all_events.has_key(event_location):
            all_events[event_location] = [TimespanCollection(resolution, [event])]

        # Try and fit the event into an events list.

        else:
            slot = all_events[event_location]

            for slot_events in slot:

                # Where the event does not overlap with the events in the
                # current collection, add it alongside these events.

                if not event in slot_events:
                    slot_events.insert_in_order(event)
                    break

            # Make a new element in the list if the event cannot be
            # marked alongside existing events.

            else:
                slot.append(TimespanCollection(resolution, [event]))

    return full_coverage, all_events

def getCoverageScale(coverage):

    """
    Return a scale for the given coverage so that the times involved are
    exposed. The scale consists of a list of non-overlapping timespans forming
    a contiguous period of time, where each timespan is accompanied in a tuple
    by a limit and a list of original time details. Thus, the scale consists of
    (timespan, limit, set-of-times) tuples.
    """

    times = {}

    for timespan in coverage:
        start, end = timespan.as_limits()

        # Add either genuine times or dates converted to times.

        if isinstance(start, DateTime):
            value = start
            key = value.to_utc(), START
        else:
            value = start.as_start_of_day()
            key = value, START

        if not times.has_key(key):
            times[key] = set()
        times[key].add(value)

        if isinstance(end, DateTime):
            value = end
            key = value.to_utc(), END
        else:
            value = end.as_date().next_day()
            key = value, END

        if not times.has_key(key):
            times[key] = set()
        times[key].add(value)

    keys = times.keys()
    keys.sort(cmp_tuples_with_dates_as_day_start)

    scale = []
    first = 1
    start, start_limit = None, None

    for time, limit in keys:
        if not first:
            scale.append((Timespan(start, time), limit, times[(start, start_limit)]))
        else:
            first = 0
        start, start_limit = time, limit

    return scale

def cmp_tuples_with_dates_as_day_start(a, b):

    """
    Compare (datetime, limit) tuples, where identical datetimes are
    distinguished by the limit associated with them.
    """

    a_date, a_limit = a
    b_date, b_limit = b
    result = cmp_dates_as_day_start(a_date, b_date)

    if result == 0:
        if a_limit < b_limit:
            return -1
        else:
            return 1

    return result

# vim: tabstop=4 expandtab shiftwidth=4
