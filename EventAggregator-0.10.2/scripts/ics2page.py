# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Conversion of iCalendar resources to event pages

    @copyright: 2011 by Paul Boddie <paul@boddie.org.uk>

    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from collections import defaultdict
from EventAggregatorSupport import Date
import vCalendar
import codecs
import re

date_regexp_str = ur'(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})'
time_regexp_str = ur'(?P<hour>[0-2][0-9])(?P<minute>[0-5][0-9])(?:(?P<second>[0-6][0-9]))?'

date_regexp = re.compile(date_regexp_str, re.UNICODE)
time_regexp = re.compile(time_regexp_str, re.UNICODE)

def convert(value, pattern):
    match = pattern.match(value)
    if match:
        return match.groups()
    else:
        return [value]

def convert_date(value, end=0):
    fields = convert(value, date_regexp)
    if len(fields) == 1:
        return value
    else:
        date = Date(map(int, fields))
        if end:
            date = date.day_update(-1)
        return str(date)

def convert_time(value):
    fields = convert(value, time_regexp)
    if len(fields) == 1:
        return value
    else:
        return ":".join(fields)

def convert_to_time_and_zone(value):
    for sign in ("-", "+", " "):
        parts = value.split(sign)
        if len(parts) > 1:
            return parts[0], (sign + parts[1]).lstrip()
    return value, ""

def convert_datetime(value, end=0):
    parts = value.split("T")
    if len(parts) == 1:
        return convert_date(value, end)
    else:
        date, time = parts[:2]
        if value.endswith("Z"):
            time, zone = time[:-1], "UTC"
        else:
            time, zone = convert_to_time_and_zone(time)
        return "%s %s %s" % (convert_date(date), convert_time(time), zone)

def parse_event(it):
    event = defaultdict(unicode)

    for name, parameters, value in it:
        if name == "END" and value == "VEVENT":
            break
        if name.startswith("DT"):
            value = convert_datetime(value, name == "DTEND")
        event[name] = value

    return event

if __name__ == "__main__":
    import os, sys
    progname = os.path.split(sys.argv[0])[-1]

    try:
        it = vCalendar.iterparse(sys.argv[1])
    except IndexError:
        print >>sys.stderr, "Usage: %s <iCalendar filename>" % progname
        sys.exit(1)

    events = []

    for name, parameters, value in it:
        if name == "BEGIN" and value == "VEVENT":
            event = parse_event(it)
            event["DTEND"] = event["DTEND"] or event["DTSTART"]
            events.append(event)

    out = codecs.getwriter("utf-8")(sys.stdout)

    for event in events:
        out.write(u"""
== %(SUMMARY)s ==

 Start:: %(DTSTART)s
 End:: %(DTEND)s
 Summary:: %(SUMMARY)s
 Topics:: %(CATEGORIES)s
 Location:: %(LOCATION)s
 URL:: %(URL)s
""" % event)

    out.write("""
----
CategoryEvents
""")

# vim: tabstop=4 expandtab shiftwidth=4
