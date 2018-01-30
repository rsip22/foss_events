# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator user interface library

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from EventAggregatorSupport.Filter import getCalendarPeriod, getEventsInPeriod, \
                                          getCoverage, getCoverageScale
from EventAggregatorSupport.Locations import getMapsPage, getLocationsPage, Location

from GeneralSupport import sort_none_first
from LocationSupport import getMapReference, getNormalisedLocation, \
                            getPositionForCentrePoint, getPositionForReference
from MoinDateSupport import getFullDateLabel, getFullMonthLabel
from MoinSupport import *
from ViewSupport import getColour, getBlackOrWhite

from MoinMoin.Page import Page
from MoinMoin.action import AttachFile
from MoinMoin import wikiutil

try:
    set
except NameError:
    from sets import Set as set

# Utility functions.

def to_plain_text(s, request):

    "Convert 's' to plain text."

    fmt = getFormatterClass(request, "plain")(request)
    fmt.setPage(request.page)
    return formatText(s, request, fmt)

def getLocationPosition(location, locations):

    """
    Attempt to return the position of the given 'location' using the 'locations'
    dictionary provided. If no position can be found, return a latitude of None
    and a longitude of None.
    """

    latitude, longitude = None, None

    if location is not None:
        try:
            latitude, longitude = map(getMapReference, locations[location].split())
        except (KeyError, ValueError):
            pass

    return latitude, longitude

# Event sorting.

def sort_start_first(x, y):
    x_ts = x.as_limits()
    if x_ts is not None:
        x_start, x_end = x_ts
        y_ts = y.as_limits()
        if y_ts is not None:
            y_start, y_end = y_ts
            start_order = cmp(x_start, y_start)
            if start_order == 0:
                return cmp(x_end, y_end)
            else:
                return start_order
    return 0

# User interface abstractions.

class View:

    "A view of the event calendar."

    def __init__(self, page, calendar_name,
        raw_calendar_start, raw_calendar_end,
        original_calendar_start, original_calendar_end,
        calendar_start, calendar_end,
        wider_calendar_start, wider_calendar_end,
        first, last, category_names, remote_sources, search_pattern, template_name,
        parent_name, mode, raw_resolution, resolution, name_usage, map_name):

        """
        Initialise the view with the current 'page', a 'calendar_name' (which
        may be None), the 'raw_calendar_start' and 'raw_calendar_end' (which
        are the actual start and end values provided by the request), the
        calculated 'original_calendar_start' and 'original_calendar_end' (which
        are the result of calculating the calendar's limits from the raw start
        and end values), the requested, calculated 'calendar_start' and
        'calendar_end' (which may involve different start and end values due to
        navigation in the user interface), and the requested
        'wider_calendar_start' and 'wider_calendar_end' (which indicate a wider
        view used when navigating out of the day view), along with the 'first'
        and 'last' months of event coverage.

        The additional 'category_names', 'remote_sources', 'search_pattern',
        'template_name', 'parent_name' and 'mode' parameters are used to
        configure the links employed by the view.

        The 'raw_resolution' is used to parameterise download links, whereas the
        'resolution' affects the view for certain modes and is also used to
        parameterise links.

        The 'name_usage' parameter controls how names are shown on calendar mode
        events, such as how often labels are repeated.

        The 'map_name' parameter provides the name of a map to be used in the
        map mode.
        """

        self.page = page
        self.calendar_name = calendar_name
        self.raw_calendar_start = raw_calendar_start
        self.raw_calendar_end = raw_calendar_end
        self.original_calendar_start = original_calendar_start
        self.original_calendar_end = original_calendar_end
        self.calendar_start = calendar_start
        self.calendar_end = calendar_end
        self.wider_calendar_start = wider_calendar_start
        self.wider_calendar_end = wider_calendar_end
        self.template_name = template_name
        self.parent_name = parent_name
        self.mode = mode
        self.raw_resolution = raw_resolution
        self.resolution = resolution
        self.name_usage = name_usage
        self.map_name = map_name

        # Search-related parameters for links.

        self.category_name_parameters = "&".join([("category=%s" % name) for name in category_names])
        self.remote_source_parameters = "&".join([("source=%s" % source) for source in remote_sources])
        self.search_pattern = search_pattern

        # Calculate the duration in terms of the highest common unit of time.

        self.first = first
        self.last = last
        self.duration = abs(last - first) + 1

        if self.calendar_name:

            # Store the view parameters.

            self.previous_start = first.previous()
            self.next_start = first.next()
            self.previous_end = last.previous()
            self.next_end = last.next()

            self.previous_set_start = first.update(-self.duration)
            self.next_set_start = first.update(self.duration)
            self.previous_set_end = last.update(-self.duration)
            self.next_set_end = last.update(self.duration)

    def getIdentifier(self):

        "Return a unique identifier to be used to refer to this view."

        # NOTE: Nasty hack to get a unique identifier if no name is given.

        return self.calendar_name or str(id(self))

    def getQualifiedParameterName(self, argname):

        "Return the 'argname' qualified using the calendar name."

        return getQualifiedParameterName(self.calendar_name, argname)

    def getDateQueryString(self, argname, date, prefix=1):

        """
        Return a query string fragment for the given 'argname', referring to the
        month given by the specified 'year_month' object, appropriate for this
        calendar.

        If 'prefix' is specified and set to a false value, the parameters in the
        query string will not be calendar-specific, but could be used with the
        summary action.
        """

        suffixes = ["year", "month", "day"]

        if date is not None:
            args = []
            for suffix, value in zip(suffixes, date.as_tuple()):
                suffixed_argname = "%s-%s" % (argname, suffix)
                if prefix:
                    suffixed_argname = self.getQualifiedParameterName(suffixed_argname)
                args.append("%s=%s" % (suffixed_argname, value))
            return "&".join(args)
        else:
            return ""

    def getRawDateQueryString(self, argname, date, prefix=1):

        """
        Return a query string fragment for the given 'argname', referring to the
        date given by the specified 'date' value, appropriate for this
        calendar.

        If 'prefix' is specified and set to a false value, the parameters in the
        query string will not be calendar-specific, but could be used with the
        summary action.
        """

        if date is not None:
            if prefix:
                argname = self.getQualifiedParameterName(argname)
            return "%s=%s" % (argname, wikiutil.url_quote(date))
        else:
            return ""

    def getNavigationLink(self, start, end, mode=None, resolution=None, wider_start=None, wider_end=None):

        """
        Return a query string fragment for navigation to a view showing months
        from 'start' to 'end' inclusive, with the optional 'mode' indicating the
        view style and the optional 'resolution' indicating the resolution of a
        view, if configurable.

        If the 'wider_start' and 'wider_end' arguments are given, parameters
        indicating a wider calendar view (when returning from a day view, for
        example) will be included in the link.
        """

        return "%s&%s&%s=%s&%s=%s&%s&%s" % (
            self.getRawDateQueryString("start", start),
            self.getRawDateQueryString("end", end),
            self.getQualifiedParameterName("mode"), mode or self.mode,
            self.getQualifiedParameterName("resolution"), resolution or self.resolution,
            self.getRawDateQueryString("wider-start", wider_start),
            self.getRawDateQueryString("wider-end", wider_end),
            )

    def getUpdateLink(self, start, end, mode=None, resolution=None, wider_start=None, wider_end=None):

        """
        Return a query string fragment for navigation to a view showing months
        from 'start' to 'end' inclusive, with the optional 'mode' indicating the
        view style and the optional 'resolution' indicating the resolution of a
        view, if configurable. This link differs from the conventional
        navigation link in that it is sufficient to activate the update action
        and produce an updated region of the page without needing to locate and
        process the page or any macro invocation.

        If the 'wider_start' and 'wider_end' arguments are given, parameters
        indicating a wider calendar view (when returning from a day view, for
        example) will be included in the link.
        """

        parameters = [
            self.getRawDateQueryString("start", start, 0),
            self.getRawDateQueryString("end", end, 0),
            self.category_name_parameters,
            self.remote_source_parameters,
            self.getRawDateQueryString("wider-start", wider_start, 0),
            self.getRawDateQueryString("wider-end", wider_end, 0),
            ]

        pairs = [
            ("calendar", self.calendar_name or ""),
            ("calendarstart", self.raw_calendar_start or ""),
            ("calendarend", self.raw_calendar_end or ""),
            ("mode", mode or self.mode),
            ("resolution", resolution or self.resolution),
            ("raw-resolution", self.raw_resolution),
            ("parent", self.parent_name or ""),
            ("template", self.template_name or ""),
            ("names", self.name_usage),
            ("map", self.map_name or ""),
            ("search", self.search_pattern or ""),
            ]

        url = self.page.url(self.page.request,
            "action=EventAggregatorUpdate&%s" % (
                "&".join([("%s=%s" % (key, wikiutil.url_quote(value))) for (key, value) in pairs] + parameters)
            ), relative=True)

        return "return replaceCalendar('EventAggregator-%s', '%s')" % (self.getIdentifier(), url)

    def getNewEventLink(self, start):

        """
        Return a query string activating the new event form, incorporating the
        calendar parameters, specialising the form for the given 'start' date or
        month.
        """

        if start is not None:
            details = start.as_tuple()
            pairs = zip(["start-year=%d", "start-month=%d", "start-day=%d"], details)
            args = [(param % value) for (param, value) in pairs]
            args = "&".join(args)
        else:
            args = ""

        # Prepare navigation details for the calendar shown with the new event
        # form.

        navigation_link = self.getNavigationLink(
            self.calendar_start, self.calendar_end
            )

        return "action=EventAggregatorNewEvent%s%s&template=%s&parent=%s&%s" % (
            args and "&%s" % args,
            self.category_name_parameters and "&%s" % self.category_name_parameters,
            self.template_name, self.parent_name or "",
            navigation_link)

    def getFullDateLabel(self, date):
        return getFullDateLabel(self.page.request, date)

    def getFullMonthLabel(self, year_month):
        return getFullMonthLabel(self.page.request, year_month)

    def getFullLabel(self, arg, resolution):
        return resolution == "date" and self.getFullDateLabel(arg) or self.getFullMonthLabel(arg)

    def _getCalendarPeriod(self, start_label, end_label, default_label):

        """
        Return a label describing a calendar period in terms of the given
        'start_label' and 'end_label', with the 'default_label' being used where
        the supplied start and end labels fail to produce a meaningful label.
        """

        output = []
        append = output.append

        if start_label:
            append(start_label)
        if end_label and start_label != end_label:
            if output:
                append(" - ")
            append(end_label)
        return "".join(output) or default_label

    def getCalendarPeriod(self):

        "Return the period description for the shown calendar."

        _ = self.page.request.getText
        return self._getCalendarPeriod(
            self.calendar_start and self.getFullLabel(self.calendar_start, self.resolution),
            self.calendar_end and self.getFullLabel(self.calendar_end, self.resolution),
            _("All events")
            )

    def getOriginalCalendarPeriod(self):

        "Return the period description for the originally specified calendar."

        _ = self.page.request.getText
        return self._getCalendarPeriod(
            self.original_calendar_start and self.getFullLabel(self.original_calendar_start, self.raw_resolution),
            self.original_calendar_end and self.getFullLabel(self.original_calendar_end, self.raw_resolution),
            _("All events")
            )

    def getRawCalendarPeriod(self):

        "Return the raw period description for the calendar."

        _ = self.page.request.getText
        return self._getCalendarPeriod(
            self.raw_calendar_start,
            self.raw_calendar_end,
             _("No period specified")
            )

    def writeDownloadControls(self):

        """
        Return a representation of the download controls, featuring links for
        view, calendar and customised downloads and subscriptions.
        """

        page = self.page
        request = page.request
        fmt = request.formatter
        _ = request.getText

        output = []
        append = output.append

        # The full URL is needed for webcal links.

        full_url = "%s%s" % (request.getBaseURL(), getPathInfo(request))

        # Generate the links.

        download_dialogue_link = "action=EventAggregatorSummary&parent=%s&search=%s%s%s" % (
            self.parent_name or "",
            self.search_pattern or "",
            self.category_name_parameters and "&%s" % self.category_name_parameters,
            self.remote_source_parameters and "&%s" % self.remote_source_parameters
            )
        download_all_link = download_dialogue_link + "&doit=1"
        download_link = download_all_link + ("&%s&%s" % (
            self.getDateQueryString("start", self.calendar_start, prefix=0),
            self.getDateQueryString("end", self.calendar_end, prefix=0)
            ))

        # The entire calendar download uses the originally specified resolution
        # of the calendar as does the dialogue. The other link uses the current
        # resolution.

        download_dialogue_link += "&resolution=%s" % self.raw_resolution
        download_all_link += "&resolution=%s" % self.raw_resolution
        download_link += "&resolution=%s" % self.resolution

        # Subscription links just explicitly select the RSS format.

        subscribe_dialogue_link = download_dialogue_link + "&format=RSS"
        subscribe_all_link = download_all_link + "&format=RSS"
        subscribe_link = download_link + "&format=RSS"

        # Adjust the "download all" and "subscribe all" links if the calendar
        # has an inherent period associated with it.

        period_limits = []

        if self.raw_calendar_start:
            period_limits.append("&%s" %
                self.getRawDateQueryString("start", self.raw_calendar_start, prefix=0)
                )
        if self.raw_calendar_end:
            period_limits.append("&%s" %
                self.getRawDateQueryString("end", self.raw_calendar_end, prefix=0)
                )

        period_limits = "".join(period_limits)

        download_dialogue_link += period_limits
        download_all_link += period_limits
        subscribe_dialogue_link += period_limits
        subscribe_all_link += period_limits

        # Pop-up descriptions of the downloadable calendars.

        shown_calendar_period = self.getCalendarPeriod()
        original_calendar_period = self.getOriginalCalendarPeriod()
        raw_calendar_period = self.getRawCalendarPeriod()

        # Write the controls.

        # Download controls.

        controls_target = "%s-controls" % self.getIdentifier()

        append(fmt.div(on=1, css_class="event-download-controls", id=controls_target))

        download_target = "%s-download" % self.getIdentifier()

        append(fmt.span(on=1, css_class="event-download", id=download_target))
        append(linkToPage(request, page, _("Download..."), anchor=download_target))
        append(fmt.div(on=1, css_class="event-download-popup"))

        append(fmt.div(on=1, css_class="event-download-item"))
        append(fmt.span(on=1, css_class="event-download-types"))
        append(fmt.span(on=1, css_class="event-download-webcal"))
        append(linkToResource(full_url.replace("http", "webcal", 1), request, _("webcal"), download_link))
        append(fmt.span(on=0))
        append(fmt.span(on=1, css_class="event-download-http"))
        append(linkToPage(request, page, _("http"), download_link, title=_("Download this view in the browser")))
        append(fmt.span(on=0))
        append(fmt.span(on=0)) # end types
        append(fmt.span(on=1, css_class="event-download-label"))
        append(fmt.text(_("Download this view")))
        append(fmt.span(on=0)) # end label
        append(fmt.span(on=1, css_class="event-download-period"))
        append(fmt.text(shown_calendar_period))
        append(fmt.span(on=0))
        append(fmt.div(on=0))

        append(fmt.div(on=1, css_class="event-download-item"))
        append(fmt.span(on=1, css_class="event-download-types"))
        append(fmt.span(on=1, css_class="event-download-webcal"))
        append(linkToResource(full_url.replace("http", "webcal", 1), request, _("webcal"), download_all_link))
        append(fmt.span(on=0))
        append(fmt.span(on=1, css_class="event-download-http"))
        append(linkToPage(request, page, _("http"), download_all_link, title=_("Download this calendar in the browser")))
        append(fmt.span(on=0))
        append(fmt.span(on=0)) # end types
        append(fmt.span(on=1, css_class="event-download-label"))
        append(fmt.text(_("Download this calendar")))
        append(fmt.span(on=0)) # end label
        append(fmt.span(on=1, css_class="event-download-period"))
        append(fmt.text(original_calendar_period))
        append(fmt.span(on=0))
        append(fmt.span(on=1, css_class="event-download-period-raw"))
        append(fmt.text(raw_calendar_period))
        append(fmt.span(on=0))
        append(fmt.div(on=0))

        append(fmt.div(on=1, css_class="event-download-item"))
        append(fmt.span(on=1, css_class="event-download-link"))
        append(linkToPage(request, page, _("Edit download options..."), download_dialogue_link))
        append(fmt.span(on=0)) # end label
        append(fmt.div(on=0))

        append(fmt.div(on=1, css_class="event-download-item focus-only"))
        append(fmt.span(on=1, css_class="event-download-link"))
        append(linkToPage(request, page, _("Cancel"), anchor=controls_target))
        append(fmt.span(on=0)) # end label
        append(fmt.div(on=0))

        append(fmt.div(on=0)) # end of pop-up
        append(fmt.span(on=0)) # end of download

        # Subscription controls.

        subscribe_target = "%s-subscribe" % self.getIdentifier()

        append(fmt.span(on=1, css_class="event-download", id=subscribe_target))
        append(linkToPage(request, page, _("Subscribe..."), anchor=subscribe_target))
        append(fmt.div(on=1, css_class="event-download-popup"))

        append(fmt.div(on=1, css_class="event-download-item"))
        append(fmt.span(on=1, css_class="event-download-label"))
        append(linkToPage(request, page, _("Subscribe to this view"), subscribe_link))
        append(fmt.span(on=0)) # end label
        append(fmt.span(on=1, css_class="event-download-period"))
        append(fmt.text(shown_calendar_period))
        append(fmt.span(on=0))
        append(fmt.div(on=0))

        append(fmt.div(on=1, css_class="event-download-item"))
        append(fmt.span(on=1, css_class="event-download-label"))
        append(linkToPage(request, page, _("Subscribe to this calendar"), subscribe_all_link))
        append(fmt.span(on=0)) # end label
        append(fmt.span(on=1, css_class="event-download-period"))
        append(fmt.text(original_calendar_period))
        append(fmt.span(on=0))
        append(fmt.span(on=1, css_class="event-download-period-raw"))
        append(fmt.text(raw_calendar_period))
        append(fmt.span(on=0))
        append(fmt.div(on=0))

        append(fmt.div(on=1, css_class="event-download-item"))
        append(fmt.span(on=1, css_class="event-download-link"))
        append(linkToPage(request, page, _("Edit subscription options..."), subscribe_dialogue_link))
        append(fmt.span(on=0)) # end label
        append(fmt.div(on=0))

        append(fmt.div(on=1, css_class="event-download-item focus-only"))
        append(fmt.span(on=1, css_class="event-download-link"))
        append(linkToPage(request, page, _("Cancel"), anchor=controls_target))
        append(fmt.span(on=0)) # end label
        append(fmt.div(on=0))

        append(fmt.div(on=0)) # end of pop-up
        append(fmt.span(on=0)) # end of download

        append(fmt.div(on=0)) # end of controls

        return "".join(output)

    def writeViewControls(self):

        """
        Return a representation of the view mode controls, permitting viewing of
        aggregated events in calendar, list or table form.
        """

        page = self.page
        request = page.request
        fmt = request.formatter
        _ = request.getText

        output = []
        append = output.append

        # For day view links to other views, the wider view parameters should
        # be used in order to be able to return to those other views.

        specific_start = self.calendar_start
        specific_end = self.calendar_end

        multiday = self.resolution == "date" and len(specific_start.days_until(specific_end)) > 1

        start = self.wider_calendar_start or self.original_calendar_start and specific_start
        end = self.wider_calendar_end or self.original_calendar_end and specific_end

        help_page = Page(request, "HelpOnEventAggregator")

        calendar_link = self.getNavigationLink(start and start.as_month(), end and end.as_month(), "calendar", "month")
        calendar_update_link = self.getUpdateLink(start and start.as_month(), end and end.as_month(), "calendar", "month")
        list_link = self.getNavigationLink(start, end, "list", "month")
        list_update_link = self.getUpdateLink(start, end, "list", "month")
        table_link = self.getNavigationLink(start, end, "table", "month")
        table_update_link = self.getUpdateLink(start, end, "table", "month")
        map_link = self.getNavigationLink(start, end, "map", "month")
        map_update_link = self.getUpdateLink(start, end, "map", "month")

        # Specific links permit date-level navigation.

        specific_day_link = self.getNavigationLink(specific_start, specific_end, "day", wider_start=start, wider_end=end)
        specific_day_update_link = self.getUpdateLink(specific_start, specific_end, "day", wider_start=start, wider_end=end)
        specific_list_link = self.getNavigationLink(specific_start, specific_end, "list", wider_start=start, wider_end=end)
        specific_list_update_link = self.getUpdateLink(specific_start, specific_end, "list", wider_start=start, wider_end=end)
        specific_table_link = self.getNavigationLink(specific_start, specific_end, "table", wider_start=start, wider_end=end)
        specific_table_update_link = self.getUpdateLink(specific_start, specific_end, "table", wider_start=start, wider_end=end)
        specific_map_link = self.getNavigationLink(specific_start, specific_end, "map", wider_start=start, wider_end=end)
        specific_map_update_link = self.getUpdateLink(specific_start, specific_end, "map", wider_start=start, wider_end=end)

        new_event_link = self.getNewEventLink(start)

        # Write the controls.

        append(fmt.div(on=1, css_class="event-view-controls"))

        append(fmt.span(on=1, css_class="event-view"))
        append(linkToPage(request, help_page, _("Help")))
        append(fmt.span(on=0))

        append(fmt.span(on=1, css_class="event-view"))
        append(linkToPage(request, page, _("New event"), new_event_link))
        append(fmt.span(on=0))

        if self.mode != "calendar":
            view_label = self.resolution == "date" and \
                (multiday and _("View days in calendar") or _("View day in calendar")) or \
                _("View as calendar")
            append(fmt.span(on=1, css_class="event-view"))
            append(linkToPage(request, page, view_label, calendar_link, onclick=calendar_update_link))
            append(fmt.span(on=0))

        if self.resolution == "date" and self.mode != "day":
            view_label = multiday and _("View days as calendar") or _("View day as calendar")
            append(fmt.span(on=1, css_class="event-view"))
            append(linkToPage(request, page, view_label, specific_day_link, onclick=specific_day_update_link))
            append(fmt.span(on=0))

        if self.resolution != "date" and self.mode != "list" or self.resolution == "date":
            view_label = self.resolution == "date" and \
                (multiday and _("View days in list") or _("View day in list")) or \
                _("View as list")
            append(fmt.span(on=1, css_class="event-view"))
            append(linkToPage(request, page, view_label, list_link, onclick=list_update_link))
            append(fmt.span(on=0))

        if self.resolution == "date" and self.mode != "list":
            view_label = multiday and _("View days as list") or _("View day as list")
            append(fmt.span(on=1, css_class="event-view"))
            append(linkToPage(request, page, view_label, specific_list_link, onclick=specific_list_update_link))
            append(fmt.span(on=0))

        if self.resolution != "date" and self.mode != "table" or self.resolution == "date":
            view_label = self.resolution == "date" and \
                (multiday and _("View days in table") or _("View day in table")) or \
                _("View as table")
            append(fmt.span(on=1, css_class="event-view"))
            append(linkToPage(request, page, view_label, table_link, onclick=table_update_link))
            append(fmt.span(on=0))

        if self.resolution == "date" and self.mode != "table":
            view_label = multiday and _("View days as table") or _("View day as table")
            append(fmt.span(on=1, css_class="event-view"))
            append(linkToPage(request, page, view_label, specific_table_link, onclick=specific_table_update_link))
            append(fmt.span(on=0))

        if self.map_name:
            if self.resolution != "date" and self.mode != "map" or self.resolution == "date":
                view_label = self.resolution == "date" and \
                    (multiday and _("View days in map") or _("View day in map")) or \
                    _("View as map")
                append(fmt.span(on=1, css_class="event-view"))
                append(linkToPage(request, page, view_label, map_link, onclick=map_update_link))
                append(fmt.span(on=0))

            if self.resolution == "date" and self.mode != "map":
                view_label = multiday and _("View days as map") or _("View day as map")
                append(fmt.span(on=1, css_class="event-view"))
                append(linkToPage(request, page, view_label, specific_map_link, onclick=specific_map_update_link))
                append(fmt.span(on=0))

        append(fmt.div(on=0))

        return "".join(output)

    def writeMapHeading(self):

        """
        Return the calendar heading for the current calendar, providing links
        permitting navigation to other periods.
        """

        label = self.getCalendarPeriod()

        if self.raw_calendar_start is None or self.raw_calendar_end is None:
            fmt = self.page.request.formatter
            output = []
            append = output.append
            append(fmt.span(on=1))
            append(fmt.text(label))
            append(fmt.span(on=0))
            return "".join(output)
        else:
            return self._writeCalendarHeading(label, self.calendar_start, self.calendar_end)

    def writeDateHeading(self, date):
        if isinstance(date, Date):
            return self.writeDayHeading(date)
        else:
            return self.writeMonthHeading(date)

    def writeMonthHeading(self, year_month):

        """
        Return the calendar heading for the given 'year_month' (a Month object)
        providing links permitting navigation to other months.
        """

        full_month_label = self.getFullMonthLabel(year_month)
        end_month = year_month.update(self.duration - 1)
        return self._writeCalendarHeading(full_month_label, year_month, end_month)

    def writeDayHeading(self, date):

        """
        Return the calendar heading for the given 'date' (a Date object)
        providing links permitting navigation to other dates.
        """

        full_date_label = self.getFullDateLabel(date)
        end_date = date.update(self.duration - 1)
        return self._writeCalendarHeading(full_date_label, date, end_date)

    def writeCalendarNavigation(self):

        "Return navigation links for a calendar."

        page = self.page
        request = page.request
        fmt = request.formatter
        _ = request.getText

        output = []
        append = output.append

        if self.calendar_name:
            calendar_name = self.calendar_name

            # Links to the previous set of months and to a calendar shifted
            # back one month.

            previous_set_link = self.getNavigationLink(
                self.previous_set_start, self.previous_set_end
                )
            previous_link = self.getNavigationLink(
                self.previous_start, self.previous_end
                )
            previous_set_update_link = self.getUpdateLink(
                self.previous_set_start, self.previous_set_end
                )
            previous_update_link = self.getUpdateLink(
                self.previous_start, self.previous_end
                )

            # Links to the next set of months and to a calendar shifted
            # forward one month.

            next_set_link = self.getNavigationLink(
                self.next_set_start, self.next_set_end
                )
            next_link = self.getNavigationLink(
                self.next_start, self.next_end
                )
            next_set_update_link = self.getUpdateLink(
                self.next_set_start, self.next_set_end
                )
            next_update_link = self.getUpdateLink(
                self.next_start, self.next_end
                )

            append(fmt.div(on=1, css_class="event-calendar-navigation"))

            append(fmt.span(on=1, css_class="previous"))
            append(linkToPage(request, page, "<<", previous_set_link, onclick=previous_set_update_link, title=_("Previous set")))
            append(fmt.text(" "))
            append(linkToPage(request, page, "<", previous_link, onclick=previous_update_link, title=_("Previous")))
            append(fmt.span(on=0))

            append(fmt.span(on=1, css_class="next"))
            append(linkToPage(request, page, ">", next_link, onclick=next_update_link, title=_("Next")))
            append(fmt.text(" "))
            append(linkToPage(request, page, ">>", next_set_link, onclick=next_set_update_link, title=_("Next set")))
            append(fmt.span(on=0))

            append(fmt.div(on=0))

        return "".join(output)

    def _writeCalendarHeading(self, label, start, end):

        """
        Write a calendar heading providing links permitting navigation to other
        periods, using the given 'label' along with the 'start' and 'end' dates
        to provide a link to a particular period.
        """

        page = self.page
        request = page.request
        fmt = request.formatter
        _ = request.getText

        output = []
        append = output.append

        if self.calendar_name:

            # A link leading to this date being at the top of the calendar.

            date_link = self.getNavigationLink(start, end)
            date_update_link = self.getUpdateLink(start, end)

            append(linkToPage(request, page, label, date_link, onclick=date_update_link, title=_("Show this period first")))

        else:
            append(fmt.text(label))

        return "".join(output)

    def writeDayNumberHeading(self, date, busy):

        """
        Return a link for the given 'date' which will activate the new event
        action for the given day. If 'busy' is given as a true value, the
        heading will be marked as busy.
        """

        page = self.page
        request = page.request
        fmt = request.formatter
        _ = request.getText

        output = []
        append = output.append

        year, month, day = date.as_tuple()
        new_event_link = self.getNewEventLink(date)

        # Prepare a link to the day view for this day.

        day_view_link = self.getNavigationLink(date, date, "day", "date", self.calendar_start, self.calendar_end)
        day_view_update_link = self.getUpdateLink(date, date, "day", "date", self.calendar_start, self.calendar_end)

        # Output the heading.

        day_target = "%s-day-%d" % (self.getIdentifier(), day)
        day_menu_target = "%s-menu" % day_target

        today_attr = date == getCurrentDate() and "event-day-current" or ""

        append(fmt.rawHTML("<th class='event-day-heading event-day-%s %s' colspan='3' axis='day' id='%s'>" % (
            busy and "busy" or "empty", escattr(today_attr), escattr(day_target))))

        # Output the number and pop-up menu.

        append(fmt.div(on=1, css_class="event-day-box", id=day_menu_target))

        append(fmt.span(on=1, css_class="event-day-number-popup"))
        append(fmt.span(on=1, css_class="event-day-number-link"))
        append(linkToPage(request, page, _("View day"), day_view_link, onclick=day_view_update_link))
        append(fmt.span(on=0))
        append(fmt.span(on=1, css_class="event-day-number-link"))
        append(linkToPage(request, page, _("New event on this day"), new_event_link))
        append(fmt.span(on=0))
        append(fmt.span(on=0))

        # Link the number to the day view.

        append(fmt.span(on=1, css_class="event-day-number"))
        append(linkToPage(request, page, unicode(day), anchor=day_menu_target, title=_("View day options")))
        append(fmt.span(on=0))

        append(fmt.div(on=0))

        # End of heading.

        append(fmt.rawHTML("</th>"))

        return "".join(output)

    # Common layout methods.

    def getEventStyle(self, colour_seed):

        "Generate colour style information using the given 'colour_seed'."

        bg = getColour(colour_seed)
        fg = getBlackOrWhite(bg)
        return "background-color: rgb(%d, %d, %d); color: rgb(%d, %d, %d);" % (bg + fg)

    def writeEventSummaryBox(self, event):

        "Return an event summary box linking to the given 'event'."

        page = self.page
        request = page.request
        fmt = request.formatter

        output = []
        append = output.append

        event_details = event.getDetails()
        event_summary = event.getSummary(self.parent_name)

        is_ambiguous = event.as_timespan().ambiguous()
        style = self.getEventStyle(event_summary)

        # The event box contains the summary, alongside
        # other elements.

        append(fmt.div(on=1, css_class="event-summary-box"))
        append(fmt.div(on=1, css_class="event-summary", style=style))

        if is_ambiguous:
            append(fmt.icon("/!\\"))

        append(event.linkToEvent(request, event_summary))
        append(fmt.div(on=0))

        # Add a pop-up element for long summaries.

        append(fmt.div(on=1, css_class="event-summary-popup", style=style))

        if is_ambiguous:
            append(fmt.icon("/!\\"))

        append(event.linkToEvent(request, event_summary))
        append(fmt.div(on=0))

        append(fmt.div(on=0))

        return "".join(output)

    # Calendar layout methods.

    def writeMonthTableHeading(self, year_month):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        # Using a caption for accessibility reasons.

        append(fmt.rawHTML('<caption class="event-month-heading">'))
        append(self.writeMonthHeading(year_month))
        append(fmt.rawHTML("</caption>"))

        return "".join(output)

    def writeWeekdayHeadings(self):
        page = self.page
        request = page.request
        fmt = request.formatter
        _ = request.getText

        output = []
        append = output.append

        append(fmt.table_row(on=1))

        for weekday in range(0, 7):
            append(fmt.rawHTML(u"<th class='event-weekday-heading' colspan='3' abbr='%s' scope='row'>" %
                escattr(_(getVerboseDayLabel(weekday)))))
            append(fmt.text(_(getDayLabel(weekday))))
            append(fmt.rawHTML("</th>"))

        append(fmt.table_row(on=0))
        return "".join(output)

    def writeDayNumbers(self, first_day, number_of_days, month, coverage):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        append(fmt.table_row(on=1))

        for weekday in range(0, 7):
            day = first_day + weekday
            date = month.as_date(day)

            # Output out-of-month days.

            if day < 1 or day > number_of_days:
                append(fmt.table_cell(on=1,
                    attrs={"class" : "event-day-heading event-day-excluded", "colspan" : "3"}))
                append(fmt.table_cell(on=0))

            # Output normal days.

            else:
                # Output the day heading, making a link to a new event
                # action.

                append(self.writeDayNumberHeading(date, date in coverage))

        # End of day numbers.

        append(fmt.table_row(on=0))
        return "".join(output)

    def writeEmptyWeek(self, first_day, number_of_days, month):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        append(fmt.table_row(on=1))

        for weekday in range(0, 7):
            day = first_day + weekday
            date = month.as_date(day)

            today_attr = date == getCurrentDate() and "event-day-current" or ""

            # Output out-of-month days.

            if day < 1 or day > number_of_days:
                append(fmt.table_cell(on=1,
                    attrs={"class" : "event-day-content event-day-excluded %s" % today_attr, "colspan" : "3"}))
                append(fmt.table_cell(on=0))

            # Output empty days.

            else:
                append(fmt.table_cell(on=1,
                    attrs={"class" : "event-day-content event-day-empty %s" % today_attr, "colspan" : "3"}))

        append(fmt.table_row(on=0))
        return "".join(output)

    def writeWeekSlots(self, first_day, number_of_days, month, week_end, week_slots):
        output = []
        append = output.append

        locations = week_slots.keys()
        locations.sort(sort_none_first)

        # Visit each slot corresponding to a location (or no location).

        for location in locations:

            # Visit each coverage span, presenting the events in the span.

            for events in week_slots[location]:

                # Output each set.

                append(self.writeWeekSlot(first_day, number_of_days, month, week_end, events))

                # Add a spacer.

                append(self.writeWeekSpacer(first_day, number_of_days, month))

        return "".join(output)

    def writeWeekSlot(self, first_day, number_of_days, month, week_end, events):
        page = self.page
        request = page.request
        fmt = request.formatter

        output = []
        append = output.append

        append(fmt.table_row(on=1))

        # Then, output day details.

        for weekday in range(0, 7):
            day = first_day + weekday
            date = month.as_date(day)

            # Skip out-of-month days.

            if day < 1 or day > number_of_days:
                append(fmt.table_cell(on=1,
                    attrs={"class" : "event-day-content event-day-excluded", "colspan" : "3"}))
                append(fmt.table_cell(on=0))
                continue

            # Output the day.
            # Where a day does not contain an event, a single cell is used.
            # Otherwise, multiple cells are used to provide space before, during
            # and after events.

            day_target = "%s-day-%d" % (self.getIdentifier(), day)
            today_attr = date == getCurrentDate() and "event-day-current" or ""

            if date not in events:
                append(fmt.rawHTML(u"<td class='event-day-content event-day-empty %s' colspan='3' headers='%s'>" % (
                    escattr(today_attr), escattr(day_target))))

            # Get event details for the current day.

            for event in events:
                event_details = event.getDetails()

                if date not in event:
                    continue

                # Get basic properties of the event.

                starts_today = event_details["start"] == date
                ends_today = event_details["end"] == date
                event_summary = event.getSummary(self.parent_name)

                style = self.getEventStyle(event_summary)

                # Determine if the event name should be shown.

                start_of_period = starts_today or weekday == 0 or day == 1

                if self.name_usage == "daily" or start_of_period:
                    hide_text = 0
                else:
                    hide_text = 1

                # Output start of day gap and determine whether
                # any event content should be explicitly output
                # for this day.

                if starts_today:

                    # Single day events...

                    if ends_today:
                        colspan = 3
                        event_day_type = "event-day-single"

                    # Events starting today...

                    else:
                        append(fmt.rawHTML(u"<td class='event-day-start-gap %s' headers='%s'>" % (
                            escattr(today_attr), escattr(day_target))))
                        append(fmt.table_cell(on=0))

                        # Calculate the span of this cell.
                        # Events whose names appear on every day...

                        if self.name_usage == "daily":
                            colspan = 2
                            event_day_type = "event-day-starting"

                        # Events whose names appear once per week...

                        else:
                            if event_details["end"] <= week_end:
                                event_length = event_details["end"].day() - day + 1
                                colspan = (event_length - 2) * 3 + 4
                            else:
                                event_length = week_end.day() - day + 1
                                colspan = (event_length - 1) * 3 + 2

                            event_day_type = "event-day-multiple"

                # Events continuing from a previous week...

                elif start_of_period:

                    # End of continuing event...

                    if ends_today:
                        colspan = 2
                        event_day_type = "event-day-ending"

                    # Events continuing for at least one more day...

                    else:

                        # Calculate the span of this cell.
                        # Events whose names appear on every day...

                        if self.name_usage == "daily":
                            colspan = 3
                            event_day_type = "event-day-full"

                        # Events whose names appear once per week...

                        else:
                            if event_details["end"] <= week_end:
                                event_length = event_details["end"].day() - day + 1
                                colspan = (event_length - 1) * 3 + 2
                            else:
                                event_length = week_end.day() - day + 1
                                colspan = event_length * 3

                            event_day_type = "event-day-multiple"

                # Continuing events whose names appear on every day...

                elif self.name_usage == "daily":
                    if ends_today:
                        colspan = 2
                        event_day_type = "event-day-ending"
                    else:
                        colspan = 3
                        event_day_type = "event-day-full"

                # Continuing events whose names appear once per week...

                else:
                    colspan = None

                # Output the main content only if it is not
                # continuing from a previous day.

                if colspan is not None:

                    # Colour the cell for continuing events.

                    attrs={
                        "class" : escattr("event-day-content event-day-busy %s %s" % (event_day_type, today_attr)),
                        "colspan" : str(colspan),
                        "headers" : escattr(day_target),
                        }

                    if not (starts_today and ends_today):
                        attrs["style"] = style

                    append(fmt.rawHTML(u"<td class='%(class)s' colspan='%(colspan)s' headers='%(headers)s'>" % attrs))

                    # Output the event.

                    if starts_today and ends_today or not hide_text:
                        append(self.writeEventSummaryBox(event))

                    append(fmt.table_cell(on=0))

                # Output end of day gap.

                if ends_today and not starts_today:
                    append(fmt.rawHTML("<td class='event-day-end-gap %s' headers='%s'>" % (escattr(today_attr), escattr(day_target))))
                    append(fmt.table_cell(on=0))

        # End of set.

        append(fmt.table_row(on=0))
        return "".join(output)

    def writeWeekSpacer(self, first_day, number_of_days, month):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        append(fmt.table_row(on=1))

        for weekday in range(0, 7):
            day = first_day + weekday
            date = month.as_date(day)
            today_attr = date == getCurrentDate() and "event-day-current" or ""

            css_classes = "event-day-spacer %s" % today_attr

            # Skip out-of-month days.

            if day < 1 or day > number_of_days:
                css_classes += " event-day-excluded"

            append(fmt.table_cell(on=1, attrs={"class" : css_classes, "colspan" : "3"}))
            append(fmt.table_cell(on=0))

        append(fmt.table_row(on=0))
        return "".join(output)

    # Day layout methods.

    def writeDayTableHeading(self, date, colspan=1):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        # Using a caption for accessibility reasons.

        append(fmt.rawHTML('<caption class="event-full-day-heading">'))
        append(self.writeDayHeading(date))
        append(fmt.rawHTML("</caption>"))

        return "".join(output)

    def writeEmptyDay(self, date):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        append(fmt.table_row(on=1))

        append(fmt.table_cell(on=1,
            attrs={"class" : "event-day-content event-day-empty"}))

        append(fmt.table_row(on=0))
        return "".join(output)

    def writeDaySlots(self, date, full_coverage, day_slots):

        """
        Given a 'date', non-empty 'full_coverage' for the day concerned, and a
        non-empty mapping of 'day_slots' (from locations to event collections),
        output the day slots for the day.
        """

        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        locations = day_slots.keys()
        locations.sort(sort_none_first)

        # Traverse the time scale of the full coverage, visiting each slot to
        # determine whether it provides content for each period.

        scale = getCoverageScale(full_coverage)

        # Define a mapping of events to rowspans.

        rowspans = {}

        # Populate each period with event details, recording how many periods
        # each event populates.

        day_rows = []

        for period, limit, times in scale:

            # Ignore timespans before this day.

            if period != date:
                continue

            # Visit each slot corresponding to a location (or no location).

            day_row = []

            for location in locations:

                # Visit each coverage span, presenting the events in the span.

                for events in day_slots[location]:
                    event = self.getActiveEvent(period, events)
                    if event is not None:
                        if not rowspans.has_key(event):
                            rowspans[event] = 1
                        else:
                            rowspans[event] += 1
                    day_row.append((location, event))

            day_rows.append((period, day_row, times))

        # Output the locations.

        append(fmt.table_row(on=1))

        # Add a spacer.

        append(self.writeDaySpacer(colspan=2, cls="location"))

        for location in locations:

            # Add spacers to the column spans.

            columns = len(day_slots[location]) * 2 - 1
            append(fmt.table_cell(on=1, attrs={"class" : "event-location-heading", "colspan" : str(columns)}))
            append(fmt.text(location or ""))
            append(fmt.table_cell(on=0))

            # Add a trailing spacer.

            append(self.writeDaySpacer(cls="location"))

        append(fmt.table_row(on=0))

        # Output the periods with event details.

        last_period = period = None
        events_written = set()

        for period, day_row, times in day_rows:

            # Write a heading describing the time.

            append(fmt.table_row(on=1))

            # Show times only for distinct periods.

            if not last_period or period.start != last_period.start:
                append(self.writeDayScaleHeading(times))
            else:
                append(self.writeDayScaleHeading([]))

            append(self.writeDaySpacer())

            # Visit each slot corresponding to a location (or no location).

            for location, event in day_row:

                # Output each location slot's contribution.

                if event is None or event not in events_written:
                    append(self.writeDaySlot(period, event, event is None and 1 or rowspans[event]))
                    if event is not None:
                        events_written.add(event)

                # Add a trailing spacer.

                append(self.writeDaySpacer())

            append(fmt.table_row(on=0))

            last_period = period

        # Write a final time heading if the last period ends in the current day.

        if period is not None:
            if period.end == date:
                append(fmt.table_row(on=1))
                append(self.writeDayScaleHeading(times))

                for slot in day_row:
                    append(self.writeDaySpacer())
                    append(self.writeEmptyDaySlot())

                append(fmt.table_row(on=0))

        return "".join(output)

    def writeDayScaleHeading(self, times):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        append(fmt.table_cell(on=1, attrs={"class" : "event-scale-heading"}))

        first = 1
        for t in times:
            if isinstance(t, DateTime):
                if not first:
                    append(fmt.linebreak(0))
                append(fmt.text(t.time_string()))
            first = 0

        append(fmt.table_cell(on=0))

        return "".join(output)

    def getActiveEvent(self, period, events):
        for event in events:
            if period not in event:
                continue
            return event
        else:
            return None

    def writeDaySlot(self, period, event, rowspan):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        if event is not None:
            event_summary = event.getSummary(self.parent_name)
            style = self.getEventStyle(event_summary)

            append(fmt.table_cell(on=1, attrs={
                "class" : "event-timespan-content event-timespan-busy",
                "style" : style,
                "rowspan" : str(rowspan)
                }))
            append(self.writeEventSummaryBox(event))
            append(fmt.table_cell(on=0))
        else:
            append(self.writeEmptyDaySlot())

        return "".join(output)

    def writeEmptyDaySlot(self):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        append(fmt.table_cell(on=1,
            attrs={"class" : "event-timespan-content event-timespan-empty"}))
        append(fmt.table_cell(on=0))

        return "".join(output)

    def writeDaySpacer(self, colspan=1, cls="timespan"):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        append(fmt.table_cell(on=1, attrs={
            "class" : "event-%s-spacer" % cls,
            "colspan" : str(colspan)}))
        append(fmt.table_cell(on=0))
        return "".join(output)

    # Map layout methods.

    def writeMapTableHeading(self):
        page = self.page
        fmt = page.request.formatter

        output = []
        append = output.append

        # Using a caption for accessibility reasons.

        append(fmt.rawHTML('<caption class="event-map-heading">'))
        append(self.writeMapHeading())
        append(fmt.rawHTML("</caption>"))

        return "".join(output)

    def showDictError(self, text, pagename):
        page = self.page
        request = page.request
        fmt = request.formatter

        output = []
        append = output.append

        append(fmt.div(on=1, attrs={"class" : "event-aggregator-error"}))
        append(fmt.paragraph(on=1))
        append(fmt.text(text))
        append(fmt.paragraph(on=0))
        append(fmt.paragraph(on=1))
        append(linkToPage(request, Page(request, pagename), pagename))
        append(fmt.paragraph(on=0))

        return "".join(output)

    def writeMapMarker(self, marker_x, marker_y, map_x_scale, map_y_scale, location, events):

        "Put a marker on the map."

        page = self.page
        request = page.request
        fmt = request.formatter

        output = []
        append = output.append

        append(fmt.listitem(on=1, css_class="event-map-label"))

        # Have a positioned marker for the print mode.

        append(fmt.div(on=1, css_class="event-map-label-only",
            style="left:%dpx; top:%dpx; min-width:%dpx; min-height:%dpx") % (
                marker_x, marker_y, map_x_scale, map_y_scale))
        append(fmt.div(on=0))

        # Have a marker containing a pop-up when using the screen mode,
        # providing a normal block when using the print mode.

        location_text = to_plain_text(location, request)
        label_target = "%s-maplabel-%s" % (self.getIdentifier(), location_text)

        append(fmt.div(on=1, css_class="event-map-label", id=label_target,
            style="left:%dpx; top:%dpx; min-width:%dpx; min-height:%dpx") % (
                marker_x, marker_y, map_x_scale, map_y_scale))

        label_target_url = page.url(request, anchor=label_target, relative=True)
        append(fmt.url(1, label_target_url, "event-map-label-link"))
        append(fmt.span(1))
        append(fmt.text(location_text))
        append(fmt.span(0))
        append(fmt.url(0))

        append(fmt.div(on=1, css_class="event-map-details"))
        append(fmt.div(on=1, css_class="event-map-shadow"))
        append(fmt.div(on=1, css_class="event-map-location"))

        # The location may have been given as formatted text, but this will not
        # be usable in a heading, so it must be first converted to plain text.

        append(fmt.heading(on=1, depth=2))
        append(fmt.text(location_text))
        append(fmt.heading(on=0, depth=2))

        append(self.writeMapEventSummaries(events))

        append(fmt.div(on=0))
        append(fmt.div(on=0))
        append(fmt.div(on=0))
        append(fmt.div(on=0))
        append(fmt.listitem(on=0))

        return "".join(output)

    def writeMapEventSummaries(self, events):

        "Write summaries of the given 'events' for the map."

        page = self.page
        request = page.request
        fmt = request.formatter

        # Sort the events by date.

        events.sort(sort_start_first)

        # Write out a self-contained list of events.

        output = []
        append = output.append

        append(fmt.bullet_list(on=1, attr={"class" : "event-map-location-events"}))

        for event in events:

            # Get the event details.

            event_summary = event.getSummary(self.parent_name)
            start, end = event.as_limits()
            event_period = self._getCalendarPeriod(
                start and self.getFullDateLabel(start),
                end and self.getFullDateLabel(end),
                "")

            append(fmt.listitem(on=1))

            # Link to the page using the summary.

            append(event.linkToEvent(request, event_summary))

            # Add the event period.

            append(fmt.text(" "))
            append(fmt.span(on=1, css_class="event-map-period"))
            append(fmt.text(event_period))
            append(fmt.span(on=0))

            append(fmt.listitem(on=0))

        append(fmt.bullet_list(on=0))

        return "".join(output)

    def render(self, all_shown_events):

        """
        Render the view, returning the rendered representation as a string.
        The view will show a list of 'all_shown_events'.
        """

        page = self.page
        request = page.request
        fmt = request.formatter
        _ = request.getText

        # Make a calendar.

        output = []
        append = output.append

        append(fmt.div(on=1, css_class="event-calendar", id=("EventAggregator-%s" % self.getIdentifier())))

        # Output download controls.

        append(fmt.div(on=1, css_class="event-controls"))
        append(self.writeDownloadControls())
        append(fmt.div(on=0))

        # Output a table.

        if self.mode == "table":

            # Start of table view output.

            append(fmt.table(on=1, attrs={"tableclass" : "event-table", "summary" : _("A table of events")}))

            append(fmt.table_row(on=1))
            append(fmt.table_cell(on=1, attrs={"class" : "event-table-heading"}))
            append(fmt.text(_("Event dates")))
            append(fmt.table_cell(on=0))
            append(fmt.table_cell(on=1, attrs={"class" : "event-table-heading"}))
            append(fmt.text(_("Event location")))
            append(fmt.table_cell(on=0))
            append(fmt.table_cell(on=1, attrs={"class" : "event-table-heading"}))
            append(fmt.text(_("Event details")))
            append(fmt.table_cell(on=0))
            append(fmt.table_row(on=0))

            # Show the events in order.

            all_shown_events.sort(sort_start_first)

            for event in all_shown_events:
                event_page = event.getPage()
                event_summary = event.getSummary(self.parent_name)
                event_details = event.getDetails()

                # Prepare CSS classes with category-related styling.

                css_classes = ["event-table-details"]

                for topic in event_details.get("topics") or event_details.get("categories") or []:

                    # Filter the category text to avoid illegal characters.

                    css_classes.append("event-table-category-%s" % "".join(filter(lambda c: c.isalnum(), topic)))

                attrs = {"class" : " ".join(css_classes)}

                append(fmt.table_row(on=1))

                # Start and end dates.

                append(fmt.table_cell(on=1, attrs=attrs))
                append(fmt.span(on=1))
                append(fmt.text(str(event_details["start"])))
                append(fmt.span(on=0))

                if event_details["start"] != event_details["end"]:
                    append(fmt.text(" - "))
                    append(fmt.span(on=1))
                    append(fmt.text(str(event_details["end"])))
                    append(fmt.span(on=0))

                append(fmt.table_cell(on=0))

                # Location.

                append(fmt.table_cell(on=1, attrs=attrs))

                if event_details.has_key("location"):
                    append(event_page.formatText(event_details["location"], fmt))

                append(fmt.table_cell(on=0))

                # Link to the page using the summary.

                append(fmt.table_cell(on=1, attrs=attrs))
                append(event.linkToEvent(request, event_summary))
                append(fmt.table_cell(on=0))

                append(fmt.table_row(on=0))

            # End of table view output.

            append(fmt.table(on=0))

        # Output a map view.

        elif self.mode == "map":

            # Special dictionary pages.

            maps_page = getMapsPage(request)
            locations_page = getLocationsPage(request)

            map_image = None

            # Get the maps and locations.

            maps = getWikiDict(maps_page, request)
            locations = getWikiDict(locations_page, request)

            # Get the map image definition.

            if maps is not None and self.map_name:
                try:
                    map_details = maps[self.map_name].split()

                    map_bottom_left_latitude, map_bottom_left_longitude, map_top_right_latitude, map_top_right_longitude = \
                        map(getMapReference, map_details[:4])
                    map_width, map_height = map(int, map_details[4:6])
                    map_image = map_details[6]

                    map_x_scale = map_width / (map_top_right_longitude - map_bottom_left_longitude).to_degrees()
                    map_y_scale = map_height / (map_top_right_latitude - map_bottom_left_latitude).to_degrees()

                except (KeyError, ValueError):
                    pass

            # Report errors.

            if maps is None:
                append(self.showDictError(
                    _("You do not have read access to the maps page:"),
                    maps_page))

            elif not self.map_name:
                append(self.showDictError(
                    _("Please specify a valid map name corresponding to an entry on the following page:"),
                    maps_page))

            elif map_image is None:
                append(self.showDictError(
                    _("Please specify a valid entry for %s on the following page:") % self.map_name,
                    maps_page))

            elif locations is None:
                append(self.showDictError(
                    _("You do not have read access to the locations page:"),
                    locations_page))

            # Attempt to show the map.

            else:

                # Get events by position.

                events_by_location = {}
                event_locations = {}

                for event in all_shown_events:
                    event_details = event.getDetails()

                    location = event_details.get("location")
                    geo = event_details.get("geo")

                    # Make a temporary location if an explicit position is given
                    # but not a location name.

                    if not location and geo:
                        location = "%s %s" % tuple(geo)

                    # Map the location to a position.

                    if location is not None and not event_locations.has_key(location):

                        # Get any explicit position of an event.

                        if geo:
                            latitude, longitude = geo

                        # Or look up the position of a location using the locations
                        # page.

                        else:
                            latitude, longitude = Location(location, locations).getPosition()

                        # Use a normalised location if necessary.

                        if latitude is None and longitude is None:
                            normalised_location = getNormalisedLocation(location)
                            if normalised_location is not None:
                                latitude, longitude = getLocationPosition(normalised_location, locations)
                                if latitude is not None and longitude is not None:
                                    location = normalised_location

                        # Only remember positioned locations.

                        if latitude is not None and longitude is not None:
                            event_locations[location] = latitude, longitude

                    # Record events according to location.

                    if not events_by_location.has_key(location):
                        events_by_location[location] = []

                    events_by_location[location].append(event)

                # Get the map image URL.

                map_image_url = AttachFile.getAttachUrl(maps_page, map_image, request)

                # Start of map view output.

                map_identifier = "map-%s" % self.getIdentifier()
                append(fmt.div(on=1, css_class="event-map", id=map_identifier))

                append(self.writeCalendarNavigation())

                append(fmt.table(on=1, attrs={"summary" : _("A map showing events")}))

                append(self.writeMapTableHeading())

                append(fmt.table_row(on=1))
                append(fmt.table_cell(on=1))

                append(fmt.div(on=1, css_class="event-map-container"))
                append(fmt.image(map_image_url))
                append(fmt.number_list(on=1))

                # Events with no location are unpositioned.

                if events_by_location.has_key(None):
                    unpositioned_events = events_by_location[None]
                    del events_by_location[None]
                else:
                    unpositioned_events = []

                # Events whose location is unpositioned are themselves considered
                # unpositioned.

                for location in set(events_by_location.keys()).difference(event_locations.keys()):
                    unpositioned_events += events_by_location[location]

                # Sort the locations before traversing them.

                event_locations = event_locations.items()
                event_locations.sort()

                # Show the events in the map.

                for location, (latitude, longitude) in event_locations:
                    events = events_by_location[location]

                    # Skip unpositioned locations and locations outside the map.

                    if latitude is None or longitude is None or \
                        latitude < map_bottom_left_latitude or \
                        longitude < map_bottom_left_longitude or \
                        latitude > map_top_right_latitude or \
                        longitude > map_top_right_longitude:

                        unpositioned_events += events
                        continue

                    # Get the position and dimensions of the map marker.
                    # NOTE: Use one degree as the marker size.

                    marker_x, marker_y = getPositionForCentrePoint(
                        getPositionForReference(map_top_right_latitude, longitude, latitude, map_bottom_left_longitude,
                            map_x_scale, map_y_scale),
                        map_x_scale, map_y_scale)

                    # Add the map marker.

                    append(self.writeMapMarker(marker_x, marker_y, map_x_scale, map_y_scale, location, events))

                append(fmt.number_list(on=0))
                append(fmt.div(on=0))
                append(fmt.table_cell(on=0))
                append(fmt.table_row(on=0))

                # Write unpositioned events.

                if unpositioned_events:
                    unpositioned_identifier = "unpositioned-%s" % self.getIdentifier()

                    append(fmt.table_row(on=1, css_class="event-map-unpositioned",
                        id=unpositioned_identifier))
                    append(fmt.table_cell(on=1))

                    append(fmt.heading(on=1, depth=2))
                    append(fmt.text(_("Events not shown on the map")))
                    append(fmt.heading(on=0, depth=2))

                    # Show and hide controls.

                    append(fmt.div(on=1, css_class="event-map-show-control"))
                    append(fmt.anchorlink(on=1, name=unpositioned_identifier))
                    append(fmt.text(_("Show unpositioned events")))
                    append(fmt.anchorlink(on=0))
                    append(fmt.div(on=0))

                    append(fmt.div(on=1, css_class="event-map-hide-control"))
                    append(fmt.anchorlink(on=1, name=map_identifier))
                    append(fmt.text(_("Hide unpositioned events")))
                    append(fmt.anchorlink(on=0))
                    append(fmt.div(on=0))

                    append(self.writeMapEventSummaries(unpositioned_events))

                # End of map view output.

                append(fmt.table_cell(on=0))
                append(fmt.table_row(on=0))
                append(fmt.table(on=0))
                append(fmt.div(on=0))

        # Output a list.

        elif self.mode == "list":

            # Start of list view output.

            append(fmt.bullet_list(on=1, attr={"class" : "event-listings"}))

            # Output a list.
            # NOTE: Make the heading depth configurable.

            for period in self.first.until(self.last):

                append(fmt.listitem(on=1, attr={"class" : "event-listings-period"}))
                append(fmt.heading(on=1, depth=2, attr={"class" : "event-listings-heading"}))

                # Either write a date heading or produce links for navigable
                # calendars.

                append(self.writeDateHeading(period))

                append(fmt.heading(on=0, depth=2))

                append(fmt.bullet_list(on=1, attr={"class" : "event-period-listings"}))

                # Show the events in order.

                events_in_period = getEventsInPeriod(all_shown_events, getCalendarPeriod(period, period))
                events_in_period.sort(sort_start_first)

                for event in events_in_period:
                    event_page = event.getPage()
                    event_details = event.getDetails()
                    event_summary = event.getSummary(self.parent_name)

                    append(fmt.listitem(on=1, attr={"class" : "event-listing"}))

                    # Link to the page using the summary.

                    append(fmt.paragraph(on=1))
                    append(event.linkToEvent(request, event_summary))
                    append(fmt.paragraph(on=0))

                    # Start and end dates.

                    append(fmt.paragraph(on=1))
                    append(fmt.span(on=1))
                    append(fmt.text(str(event_details["start"])))
                    append(fmt.span(on=0))
                    append(fmt.text(" - "))
                    append(fmt.span(on=1))
                    append(fmt.text(str(event_details["end"])))
                    append(fmt.span(on=0))
                    append(fmt.paragraph(on=0))

                    # Location.

                    if event_details.has_key("location"):
                        append(fmt.paragraph(on=1))
                        append(event_page.formatText(event_details["location"], fmt))
                        append(fmt.paragraph(on=1))

                    # Topics.

                    if event_details.has_key("topics") or event_details.has_key("categories"):
                        append(fmt.bullet_list(on=1, attr={"class" : "event-topics"}))

                        for topic in event_details.get("topics") or event_details.get("categories") or []:
                            append(fmt.listitem(on=1))
                            append(event_page.formatText(topic, fmt))
                            append(fmt.listitem(on=0))

                        append(fmt.bullet_list(on=0))

                    append(fmt.listitem(on=0))

                append(fmt.bullet_list(on=0))

            # End of list view output.

            append(fmt.bullet_list(on=0))

        # Output a month calendar. This shows month-by-month data.

        elif self.mode == "calendar":

            # Visit all months in the requested range, or across known events.

            for month in self.first.months_until(self.last):

                append(fmt.div(on=1, css_class="event-calendar"))
                append(self.writeCalendarNavigation())

                # Output a month.

                append(fmt.table(on=1, attrs={"tableclass" : "event-month", "summary" : _("A table showing a calendar month")}))

                # Either write a month heading or produce links for navigable
                # calendars.

                append(self.writeMonthTableHeading(month))

                # Weekday headings.

                append(self.writeWeekdayHeadings())

                # Process the days of the month.

                start_weekday, number_of_days = month.month_properties()

                # The start weekday is the weekday of day number 1.
                # Find the first day of the week, counting from below zero, if
                # necessary, in order to land on the first day of the month as
                # day number 1.

                first_day = 1 - start_weekday

                while first_day <= number_of_days:

                    # Find events in this week and determine how to mark them on the
                    # calendar.

                    week_start = month.as_date(max(first_day, 1))
                    week_end = month.as_date(min(first_day + 6, number_of_days))

                    full_coverage, week_slots = getCoverage(
                        getEventsInPeriod(all_shown_events, getCalendarPeriod(week_start, week_end)))

                    # Make a new table region.
                    # NOTE: Moin opens a "tbody" element in the table method.

                    append(fmt.rawHTML("</tbody>"))
                    append(fmt.rawHTML("<tbody>"))

                    # Output a week, starting with the day numbers.

                    append(self.writeDayNumbers(first_day, number_of_days, month, full_coverage))

                    # Either generate empty days...

                    if not week_slots:
                        append(self.writeEmptyWeek(first_day, number_of_days, month))

                    # Or generate each set of scheduled events...

                    else:
                        append(self.writeWeekSlots(first_day, number_of_days, month, week_end, week_slots))

                    # Process the next week...

                    first_day += 7

                # End of month.
                # NOTE: Moin closes a "tbody" element in the table method.

                append(fmt.table(on=0))
                append(fmt.div(on=0))

        # Output a day view.

        elif self.mode == "day":

            # Visit all days in the requested range, or across known events.

            for date in self.first.days_until(self.last):

                append(fmt.div(on=1, css_class="event-calendar"))
                append(self.writeCalendarNavigation())

                append(fmt.table(on=1, attrs={"tableclass" : "event-calendar-day", "summary" : _("A table showing a calendar day")}))

                full_coverage, day_slots = getCoverage(
                    getEventsInPeriod(all_shown_events, getCalendarPeriod(date, date)), "datetime")

                # Work out how many columns the day title will need.
                # Include spacers after the scale and each event column.

                colspan = sum(map(len, day_slots.values())) * 2 + 2

                append(self.writeDayTableHeading(date, colspan))

                # Either generate empty days...

                if not day_slots:
                    append(self.writeEmptyDay(date))

                # Or generate each set of scheduled events...

                else:
                    append(self.writeDaySlots(date, full_coverage, day_slots))

                # End of day.

                append(fmt.table(on=0))
                append(fmt.div(on=0))

        # Output view controls.

        append(fmt.div(on=1, css_class="event-controls"))
        append(self.writeViewControls())
        append(fmt.div(on=0))

        # Close the calendar region.

        append(fmt.div(on=0))

        # Add any scripts.

        if isinstance(fmt, request.html_formatter.__class__):
            append(self.update_script)

        return ''.join(output)

    update_script = """\
<script type="text/javascript">
function replaceCalendar(name, url) {
    var calendar = document.getElementById(name);

    if (calendar == null) {
        return true;
    }

    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open("GET", url, false);
    xmlhttp.send(null);

    var newCalendar = xmlhttp.responseText;

    if (newCalendar != null) {
        calendar.innerHTML = newCalendar;
        return false;
    }

    return true;
}
</script>
"""

# vim: tabstop=4 expandtab shiftwidth=4
