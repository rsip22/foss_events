# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator event formatting

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2005-2008 MoinMoin:ThomasWaldmann.
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from MoinSupport import *
from MoinMoin.wikiutil import escape

try:
    import vCalendar
except ImportError:
    vCalendar = None

# Event-only formatting.

def formatEvent(event, request, fmt, write=None):

    """
    Format the given 'event' using the 'request' and formatter 'fmt'. If the
    'write' parameter is specified, use it to write output.
    """

    details = event.getDetails()
    raw_details = event.getRawDetails()
    write = write or request.write

    if details.has_key("fragment"):
        write(fmt.anchordef(details["fragment"]))

    # Promote any title to a heading above the event details.

    if raw_details.has_key("title"):
        write(formatText(raw_details["title"], request, fmt))
    elif details.has_key("title"):
        write(fmt.heading(on=1, depth=1))
        write(fmt.text(details["title"]))
        write(fmt.heading(on=0, depth=1))

    # Produce a definition list for the rest of the details.

    write(fmt.definition_list(on=1))

    for term in event.all_terms:
        if term == "title":
            continue

        raw_value = raw_details.get(term)
        value = details.get(term)

        if raw_value or value:
            write(fmt.definition_term(on=1))
            write(fmt.text(term))
            write(fmt.definition_term(on=0))
            write(fmt.definition_desc(on=1))

            # Try and use the raw details, if available.

            if raw_value:
                write(formatText(raw_value, request, fmt))

            # Otherwise, format the processed details.

            else:
                if term in event.list_terms:
                    write(", ".join([formatText(unicode(v), request, fmt) for v in value]))
                else:
                    write(fmt.text(unicode(value)))

            write(fmt.definition_desc(on=0))

    write(fmt.definition_list(on=0))

def formatEventsForOutputType(events, request, mimetype, parent=None, descriptions=None, latest_timestamp=None, write=None):

    """
    Format the given 'events' using the 'request' for the given 'mimetype'.

    The optional 'parent' indicates the "natural" parent page of the events. Any
    event pages residing beneath the parent page will have their names
    reproduced as relative to the parent page.

    The optional 'descriptions' indicates the nature of any description given
    for events in the output resource.

    The optional 'latest_timestamp' indicates the timestamp of the latest edit
    of the page or event collection.

    If the 'write' parameter is specified, use it to write output.
    """

    write = write or request.write

    # Start the collection.

    if mimetype == "text/calendar" and vCalendar is not None:
        _write = vCalendar.iterwrite(write=write).write
        _write("BEGIN", {}, "VCALENDAR")
        _write("PRODID", {}, "-//MoinMoin//EventAggregatorSummary")
        _write("VERSION", {}, "2.0")

    elif mimetype == "application/rss+xml":

        # Using the page name and the page URL in the title, link and
        # description.

        path_info = getPathInfo(request)

        write('<rss version="2.0">\n')
        write('<channel>\n')
        write('<title>%s</title>\n' % path_info[1:])
        write('<link>%s%s</link>\n' % (request.getBaseURL(), path_info))
        write('<description>Events published on %s%s</description>\n' % (request.getBaseURL(), path_info))

        if latest_timestamp is not None:
            write('<lastBuildDate>%s</lastBuildDate>\n' % latest_timestamp.as_HTTP_datetime_string())
 
        # Sort the events by start date, reversed.

        ordered_events = getOrderedEvents(events)
        ordered_events.reverse()
        events = ordered_events

    elif mimetype == "text/html":
        write('<html>')
        write('<body>')

    # Output the collection one by one.

    for event in events:
        formatEventForOutputType(event, request, mimetype, parent, descriptions, write)

    # End the collection.

    if mimetype == "text/calendar" and vCalendar is not None:
        _write("END", {}, "VCALENDAR")

    elif mimetype == "application/rss+xml":
        write('</channel>\n')
        write('</rss>\n')

    elif mimetype == "text/html":
        write('</body>')
        write('</html>')

def formatEventForOutputType(event, request, mimetype, parent=None, descriptions=None, write=None):

    """
    Format the given 'event' using the 'request' for the given 'mimetype'.

    The optional 'parent' indicates the "natural" parent page of the events. Any
    event pages residing beneath the parent page will have their names
    reproduced as relative to the parent page.

    The optional 'descriptions' indicates the nature of any description given
    for events in the output resource.

    If the 'write' parameter is specified, use it to write output.
    """

    write = write or request.write
    event_details = event.getDetails()
    event_metadata = event.getMetadata()

    if mimetype == "text/calendar" and vCalendar is not None:

        # NOTE: A custom formatter making attributes for links and plain
        # NOTE: text for values could be employed here.

        _write = vCalendar.iterwrite(write=write).write

        # Get the summary details.

        event_summary = event.getSummary(parent)
        link = event.getEventURL()

        # Output the event details.

        _write("BEGIN", {}, "VEVENT")
        _write("UID", {}, link)
        _write("URL", {}, link)
        _write("DTSTAMP", {}, "%04d%02d%02dT%02d%02d%02dZ" % event_metadata["created"].as_tuple()[:6])
        _write("LAST-MODIFIED", {}, "%04d%02d%02dT%02d%02d%02dZ" % event_metadata["last-modified"].as_tuple()[:6])
        _write("SEQUENCE", {}, "%d" % event_metadata["sequence"])

        start = event_details["start"]
        end = event_details["end"]

        if isinstance(start, DateTime):
            params, value = getCalendarDateTime(start)
        else:
            params, value = {"VALUE" : "DATE"}, "%04d%02d%02d" % start.as_date().as_tuple()
        _write("DTSTART", params, value)

        if isinstance(end, DateTime):
            params, value = getCalendarDateTime(end)
        else:
            params, value = {"VALUE" : "DATE"}, "%04d%02d%02d" % end.next_day().as_date().as_tuple()
        _write("DTEND", params, value)

        _write("SUMMARY", {}, event_summary)

        # Optional details.

        if event_details.get("topics") or event_details.get("categories"):
            _write("CATEGORIES", {}, event_details.get("topics") or event_details.get("categories"))
        if event_details.has_key("location"):
            _write("LOCATION", {}, event_details["location"])
        if event_details.has_key("geo"):
            _write("GEO", {}, tuple([str(ref.to_degrees()) for ref in event_details["geo"]]))

        _write("END", {}, "VEVENT")

    elif mimetype == "application/rss+xml":

        event_page = event.getPage()
        event_details = event.getDetails()

        # Get a parser and formatter for the formatting of some attributes.

        fmt = request.html_formatter

        # Get the summary details.

        event_summary = event.getSummary(parent)
        link = event.getEventURL()

        write('<item>\n')
        write('<title>%s</title>\n' % escape(event_summary))
        write('<link>%s</link>\n' % link)

        # Write a description according to the preferred source of
        # descriptions.

        if descriptions == "page":
            description = event_details.get("description", "")
        else:
            description = event_metadata["last-comment"]

        write('<description>%s</description>\n' %
            fmt.text(event_page.formatText(description, fmt)))

        for topic in event_details.get("topics") or event_details.get("categories") or []:
            write('<category>%s</category>\n' %
                fmt.text(event_page.formatText(topic, fmt)))

        write('<pubDate>%s</pubDate>\n' % event_metadata["created"].as_HTTP_datetime_string())
        write('<guid>%s#%s</guid>\n' % (link, event_metadata["sequence"]))
        write('</item>\n')

    elif mimetype == "text/html":
        fmt = request.html_formatter
        fmt.setPage(request.page)
        formatEvent(event, request, fmt, write=write)

# iCalendar format helper functions.

def getCalendarDateTime(datetime):

    """
    Write to the given 'request' the 'datetime' using appropriate time zone
    information.
    """

    utc_datetime = datetime.to_utc()
    if utc_datetime:
        return {"VALUE" : "DATE-TIME"}, "%04d%02d%02dT%02d%02d%02dZ" % utc_datetime.padded().as_tuple()[:-1]
    else:
        zone = datetime.time_zone()
        params = {"VALUE" : "DATE-TIME"}
        if zone:
            params["TZID"] = zone
        return params, "%04d%02d%02dT%02d%02d%02d" % datetime.padded().as_tuple()[:-1]

# Helper functions.

def getOrderedEvents(events):

    """
    Return a list with the given 'events' ordered according to their start and
    end dates.
    """

    ordered_events = events[:]
    ordered_events.sort()
    return ordered_events

# vim: tabstop=4 expandtab shiftwidth=4
