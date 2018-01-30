# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator Macro

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2005-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from EventAggregatorSupport.Actions import get_date_functions
from EventAggregatorSupport.Resources import getEventsUsingParameters
from EventAggregatorSupport.View import View, getQualifiedParameter
from MoinDateSupport import getFormMonth
from MoinMoin import wikiutil

Dependencies = []

# Macro functions.

def execute(macro, args):

    """
    Execute the 'macro' with the given 'args': an optional list of selected
    category names (categories whose pages are to be shown), together with
    optional named arguments of the following forms:

      start=YYYY-MM     shows event details starting from the specified month
      start=YYYY-MM-DD  shows event details starting from the specified day
      start=current-N   shows event details relative to the current month
                        (or relative to the current day in "day" mode)
      end=YYYY-MM       shows event details ending at the specified month
      end=YYYY-MM-DD    shows event details ending on the specified day
      end=current+N     shows event details relative to the current month
                        (or relative to the current day in "day" mode)

      mode=calendar     shows a calendar view of events
      mode=day          shows a calendar day view of events
      mode=list         shows a list of events by month
      mode=table        shows a table of events
      mode=map          shows a map of events

      calendar=NAME     uses the given NAME to provide request parameters which
                        can be used to control the calendar view

      template=PAGE     uses the given PAGE as the default template for new
                        events (or the default template from the configuration
                        if not specified)

      parent=PAGE       uses the given PAGE as the parent of any new event page

    Calendar view options:

      names=daily       shows the name of an event on every day of that event
      names=weekly      shows the name of an event once per week

    Map view options:

      map=NAME          uses the given NAME as the map image, where an entry for
                        the map must be found in the EventMaps page (or another
                        page specified in the configuration by the
                        'event_aggregator_maps_page' setting) along with an
                        attached map image
    """

    request = macro.request
    fmt = macro.formatter
    page = fmt.page

    # Interpret the arguments.

    try:
        parsed_args = args and wikiutil.parse_quoted_separated(args, name_value=False) or []
    except AttributeError:
        parsed_args = args.split(",")

    parsed_args = [arg for arg in parsed_args if arg]

    # Get special arguments.

    category_names = []
    remote_sources = []
    search_pattern = None
    raw_calendar_start = None
    raw_calendar_end = None
    calendar_start = None
    calendar_end = None
    raw_mode = None
    mode = None
    name_usage = "weekly"
    calendar_name = None
    template_name = getattr(request.cfg, "event_aggregator_new_event_template", "EventTemplate")
    parent_name = None
    map_name = None

    for arg in parsed_args:
        if arg.startswith("start="):
            raw_calendar_start = arg[6:]

        elif arg.startswith("end="):
            raw_calendar_end = arg[4:]

        elif arg.startswith("mode="):
            raw_mode = arg[5:]

        elif arg.startswith("names="):
            name_usage = arg[6:]

        elif arg.startswith("calendar="):
            calendar_name = arg[9:]

        elif arg.startswith("template="):
            template_name = arg[9:]

        elif arg.startswith("parent="):
            parent_name = arg[7:]

        elif arg.startswith("map="):
            map_name = arg[4:]

        elif arg.startswith("source="):
            remote_sources.append(arg[7:])

        elif arg.startswith("search="):
            search_pattern = arg[7:]

        else:
            category_names.append(arg)

    # Find request parameters to override settings.

    mode = getQualifiedParameter(request, calendar_name, "mode", raw_mode or "calendar")

    # Different modes require different levels of precision by default.

    raw_resolution = raw_mode == "day" and "date" or "month"

    resolution = getQualifiedParameter(request, calendar_name, "resolution", mode == "day" and "date" or "month")
    resolution = mode == "calendar" and "month" or resolution

    # Determine the limits of the calendar.

    get_date, get_form_date = get_date_functions(raw_resolution)

    original_calendar_start = calendar_start = get_date(raw_calendar_start)
    original_calendar_end = calendar_end = get_date(raw_calendar_end)

    wider_calendar_start = getFormMonth(request, calendar_name, "wider-start")
    wider_calendar_end = getFormMonth(request, calendar_name, "wider-end")

    get_date, get_form_date = get_date_functions(resolution)

    calendar_start = get_form_date(request, calendar_name, "start") or calendar_start
    calendar_end = get_form_date(request, calendar_name, "end") or calendar_end

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

    return view.render(all_shown_events)

# vim: tabstop=4 expandtab shiftwidth=4
