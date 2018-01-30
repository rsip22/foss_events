# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregatorUpdate Action

    @copyright: 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from EventAggregatorSupport.Actions import get_date_functions
from EventAggregatorSupport import *
from MoinDateSupport import getParameterMonth
from MoinMoin.Page import Page
from MoinMoin import config

Dependencies = ['pages']

# Action function.

def execute(pagename, request):

    """
    On the given 'pagename', for the given 'request', write a page fragment
    producing the rendered calendar information for inclusion in an existing Web
    page. Since the page is not processed, all necessary parameters need to be
    supplied in the request.
    """

    form = get_form(request)
    page = Page(request, pagename)

    # Find settings from the request parameters only.

    calendar_name       = form.get("calendar", [None])[0]
    category_names      = form.get("category", [])
    search_pattern      = form.get("search", [None])[0]
    remote_sources      = form.get("source", [])
    name_usage          = getParameter(request, "names", "weekly")
    template_name       = getParameter(request, "template")
    parent_name         = getParameter(request, "parent")
    mode                = getParameter(request, "mode", "calendar")
    raw_resolution      = getParameter(request, "raw-resolution")
    resolution          = getParameter(request, "resolution", mode == "day" and "date" or "month")
    map_name            = getParameter(request, "map")

    # The underlying dimensions of the calendar are supplied in special
    # parameters.

    raw_calendar_start  = getParameter(request, "calendarstart")
    raw_calendar_end    = getParameter(request, "calendarend")

    # Different modes require different levels of precision by default.

    resolution = mode == "calendar" and "month" or resolution

    # Determine the limits of the calendar.

    get_date, _get_form_date = get_date_functions(raw_resolution)

    original_calendar_start = calendar_start = get_date(raw_calendar_start)
    original_calendar_end = calendar_end = get_date(raw_calendar_end)

    wider_calendar_start = getParameterMonth(getParameter(request, "wider-start"))
    wider_calendar_end = getParameterMonth(getParameter(request, "wider-end"))

    get_date, _get_form_date = get_date_functions(resolution)

    calendar_start = get_date(getParameter(request, "start")) or calendar_start
    calendar_end = get_date(getParameter(request, "end")) or calendar_end

    # Get the events according to the resolution of the calendar.

    all_shown_events, first, last = getEventsUsingParameters(
        category_names, search_pattern, remote_sources, calendar_start, calendar_end,
        resolution, request)

    # Define a view of the calendar, retaining useful navigational information.

    view = View(page, calendar_name,
        raw_calendar_start, raw_calendar_end,
        original_calendar_start, original_calendar_end,
        calendar_start, calendar_end,
        wider_calendar_start, wider_calendar_end,
        first, last, category_names, remote_sources, search_pattern, template_name,
        parent_name, mode, raw_resolution, resolution, name_usage, map_name)

    send_headers = get_send_headers(request)
    send_headers(["Content-Type: text/html; charset=%s" % config.charset])
    request.write(view.render(all_shown_events))

# vim: tabstop=4 expandtab shiftwidth=4
