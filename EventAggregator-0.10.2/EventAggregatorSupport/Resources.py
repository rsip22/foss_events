# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator resource acquisition and access

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from EventAggregatorSupport.Filter import *
from EventAggregatorSupport.Types import *

from DateSupport import Date, Month
from MoinSupport import *
from MoinRemoteSupport import getCachedResource, getCachedResourceMetadata

import codecs
import urllib

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    import vCalendar
except ImportError:
    vCalendar = None

# Obtaining event containers and events from such containers.

def getEventPages(pages):

    "Return a list of events found on the given 'pages'."

    # Get real pages instead of result pages.

    return map(EventPage, pages)

def getAllEventSources(request):

    "Return all event sources defined in the Wiki using the 'request'."

    sources_page = getattr(request.cfg, "event_aggregator_sources_page", "EventSourcesDict")

    # Remote sources are accessed via dictionary page definitions.

    return getWikiDict(sources_page, request)

def getEventResources(sources, calendar_start, calendar_end, request):

    """
    Return resource objects for the given 'sources' using the given
    'calendar_start' and 'calendar_end' to parameterise requests to the sources,
    and the 'request' to access configuration settings in the Wiki.
    """

    sources_dict = getAllEventSources(request)
    if not sources_dict:
        return []

    # Use dates for the calendar limits.

    if isinstance(calendar_start, Date):
        pass
    elif isinstance(calendar_start, Month):
        calendar_start = calendar_start.as_date(1)

    if isinstance(calendar_end, Date):
        pass
    elif isinstance(calendar_end, Month):
        calendar_end = calendar_end.as_date(-1)

    resources = []

    for source in sources:
        try:
            details = sources_dict[source].split()
            url = details[0]
            format = (details[1:] or ["ical"])[0]
        except (KeyError, ValueError):
            pass
        else:
            resource = getEventResourcesFromSource(url, format, calendar_start, calendar_end, request)
            if resource:
                resources.append(resource)

    return resources

def getEventResourcesFromSource(url, format, calendar_start, calendar_end, request):

    """
    Return a resource object for the given 'url' providing content in the
    specified 'format', using the given 'calendar_start' and 'calendar_end' to
    parameterise requests to the sources and the 'request' to access
    configuration settings in the Wiki.
    """

    # Prevent local file access.

    if url.startswith("file:"):
        return None

    # Parameterise the URL.
    # Where other parameters are used, care must be taken to encode them
    # properly.

    url = url.replace("{start}", urllib.quote_plus(calendar_start and str(calendar_start) or ""))
    url = url.replace("{end}", urllib.quote_plus(calendar_end and str(calendar_end) or ""))

    # Get a parser.
    # NOTE: This could be done reactively by choosing a parser based on
    # NOTE: the content type provided by the URL.

    if format == "ical" and vCalendar is not None:
        parser = vCalendar.parse
        resource_cls = EventCalendar
        required_content_type = "text/calendar"
    else:
        return None

    # Obtain the resource, using a cached version if appropriate.

    max_cache_age = int(getattr(request.cfg, "event_aggregator_max_cache_age", "300"))
    data = getCachedResource(request, url, "EventAggregator", "wiki", max_cache_age)
    if not data:
        return None

    # Process the entry, parsing the content.

    f = StringIO(data)
    try:
        # Get the content type and encoding, making sure that the data
        # can be parsed.

        url, content_type, encoding, metadata = getCachedResourceMetadata(f)

        if content_type != required_content_type:
            return None

        # Send the data to the parser.

        uf = codecs.getreader(encoding or "utf-8")(f)
        try:
            return resource_cls(url, parser(uf), metadata)
        finally:
            uf.close()
    finally:
        f.close()

def getEventsFromResources(resources):

    "Return a list of events supplied by the given event 'resources'."

    events = []

    for resource in resources:

        # Get all events described by the resource.

        for event in resource.getEvents():

            # Remember the event.

            events.append(event)

    return events

# Page-related functions.

def fillEventPageFromTemplate(template_page, new_page, event_details, category_pagenames):

    """
    Using the given 'template_page', complete the 'new_page' by copying the
    template and adding the given 'event_details' (a dictionary of event
    fields), setting also the 'category_pagenames' to define category
    membership.
    """

    event_page = EventPage(template_page)
    new_event_page = EventPage(new_page)
    new_event_page.copyPage(event_page)

    if new_event_page.getFormat() == "wiki":
        new_event = Event(new_event_page, event_details)
        new_event_page.setEvents([new_event])
        new_event_page.setCategoryMembership(category_pagenames)
        new_event_page.flushEventDetails()

    return new_event_page.getBody()

# Event selection from request parameters.

def getEventsUsingParameters(category_names, search_pattern, remote_sources,
    calendar_start, calendar_end, resolution, request):

    "Get the events according to the resolution of the calendar."

    if search_pattern:
        results         = getPagesForSearch(search_pattern, request)
    else:
        results         = []

    results            += getAllCategoryPages(category_names, request)
    pages               = getPagesFromResults(results, request)
    events              = getEventsFromResources(getEventPages(pages))
    events             += getEventsFromResources(getEventResources(remote_sources, calendar_start, calendar_end, request))
    all_shown_events    = getEventsInPeriod(events, getCalendarPeriod(calendar_start, calendar_end))
    earliest, latest    = getEventLimits(all_shown_events)

    # Get a concrete period of time.

    first, last = getConcretePeriod(calendar_start, calendar_end, earliest, latest, resolution)

    return all_shown_events, first, last

# vim: tabstop=4 expandtab shiftwidth=4
