# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregatorSummary Action

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2003-2008 MoinMoin:ThomasWaldmann,
                2004-2006 MoinMoin:AlexanderSchremmer,
                2007 MoinMoin:ReimarBauer.
                2009 Cristian Rigamonti <rigamonti@fsfeurope.org>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from MoinDateSupport import *

from EventAggregatorSupport import *
from EventAggregatorSupport.Actions import ActionSupport

from MoinMoin.action import ActionBase
from MoinMoin import config
from MoinMoin.Page import Page
from MoinMoin import wikiutil

Dependencies = ['pages']

# Action class and supporting functions.

class EventAggregatorSummary(ActionBase, ActionSupport):

    "A summary dialogue requesting various parameters."

    def get_form_html(self, buttons_html):
        _ = self._
        request = self.request
        form = self.get_form()

        resolution = form.get("resolution", ["month"])[0]

        category_list = []
        category_pagenames = form.get("category", [])

        for category_name, category_pagename in getCategoryMapping(getCategories(request), request):

            selected = self._get_selected_for_list(category_pagename, category_pagenames)

            category_list.append('<option value="%s" %s>%s</option>' % (
                escattr(category_pagename), selected, escape(category_name)))

        sources_list = []
        sources = form.get("source", [])
        source_names = (getAllEventSources(request) or {}).keys()
        source_names.sort()

        for source_name in source_names:

            selected = self._get_selected_for_list(source_name, sources)

            sources_list.append('<option value="%s" %s>%s</option>' % (
                escattr(source_name), selected, escape(source_name)))

        # Initialise month lists and defaults.

        start_month_list, end_month_list = self.get_month_lists()
        start_day_default, end_day_default = self.get_day_defaults()
        start_year_default, end_year_default = self.get_year_defaults()

        # Criteria instead of months and years.

        start_criteria_default = form.get("start", [""])[0]
        end_criteria_default = form.get("end", [""])[0]

        if resolution == "date":
            get_parameter = getParameterDate
            get_label = getFullDateLabel
        else:
            get_parameter = getParameterMonth
            get_label = getFullMonthLabel

        start_criteria_evaluated = get_parameter(start_criteria_default)
        end_criteria_evaluated = get_parameter(end_criteria_default)

        start_criteria_evaluated = get_label(request, start_criteria_evaluated)
        end_criteria_evaluated = get_label(request, end_criteria_evaluated)

        # Descriptions.

        descriptions = form.get("descriptions", [None])[0]

        descriptions_list = [
            '<option value="%s" %s>%s</option>' % ("page", self._get_selected("page", descriptions), escape(_("page"))),
            '<option value="%s" %s>%s</option>' % ("comment", self._get_selected("comment", descriptions), escape(_("comment")))
            ]

        # Format.

        format = form.get("format", [None])[0]

        format_list = [
            '<option value="%s" %s>%s</option>' % ("iCalendar", self._get_selected("iCalendar", format), escape(_("iCalendar"))),
            '<option value="%s" %s>%s</option>' % ("RSS", self._get_selected("RSS", format), escape(_("RSS 2.0")))
            ]

        right_arrow = unicode('\xe2\x86\x92', "utf-8")

        d = {
            "buttons_html"          : buttons_html,
            "category_label"        : escape(_("Categories")),
            "category_list"         : "\n".join(category_list),
            "sources_label"         : escape(_("Sources")),
            "sources_list"          : "\n".join(sources_list),
            "search_label"          : escape(_("Search pattern")),
            "search_default"        : escattr(form.get("search", [""])[0]),
            "start_month_list"      : "\n".join(start_month_list),
            "start_label"           : escape(_("Start day (optional), month and year")),
            "start_day_default"     : escattr(start_day_default),
            "start_year_default"    : escattr(start_year_default),
            "start_criteria_label"  : escape(_("or special criteria")),
            "start_criteria_default": escattr(start_criteria_default),
            "start_eval_label"      : escattr(right_arrow),
            "start_criteria_eval"   : escape(start_criteria_evaluated),
            "end_month_list"        : "\n".join(end_month_list),
            "end_label"             : escape(_("End day (optional), month and year")),
            "end_day_default"       : escattr(end_day_default),
            "end_year_default"      : escattr(end_year_default),
            "end_criteria_label"    : escape(_("or special criteria")),
            "end_criteria_default"  : escattr(end_criteria_default),
            "end_eval_label"        : escattr(right_arrow),
            "end_criteria_eval"     : escape(end_criteria_evaluated),
            "descriptions_label"    : escape(_("Use descriptions from...")),
            "descriptions_list"     : "\n".join(descriptions_list),
            "format_label"          : escape(_("Summary format")),
            "format_list"           : "\n".join(format_list),
            "parent_label"          : escape(_("Parent page")),
            "parent_name"           : escattr(form.get("parent", [""])[0]),
            "resolution"            : escattr(resolution),
            }

        return '''
<input name="resolution" type="hidden" value="%(resolution)s" />
<table>
    <tr>
        <td class="label"><label>%(search_label)s</label></td>
        <td class="content">
            <input name="search" type="text" value="%(search_default)s" size="40" />
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(category_label)s</label></td>
        <td class="content">
            <select multiple="multiple" name="category">
                %(category_list)s
            </select>
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(sources_label)s</label></td>
        <td class="content">
            <select multiple="multiple" name="source">
                %(sources_list)s
            </select>
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(start_label)s</label></td>
        <td>
            <input name="start-day" type="text" value="%(start_day_default)s" size="2" />
            <select name="start-month">
                %(start_month_list)s
            </select>
            <input name="start-year" type="text" value="%(start_year_default)s" size="4" />
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(start_criteria_label)s</label></td>
        <td>
            <input name="start" type="text" value="%(start_criteria_default)s" size="12" />
            <input name="start-eval" type="submit" value="%(start_eval_label)s" />
            %(start_criteria_eval)s
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(end_label)s</label></td>
        <td>
            <input name="end-day" type="text" value="%(end_day_default)s" size="2" />
            <select name="end-month">
                %(end_month_list)s
            </select>
            <input name="end-year" type="text" value="%(end_year_default)s" size="4" />
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(end_criteria_label)s</label></td>
        <td>
            <input name="end" type="text" value="%(end_criteria_default)s" size="12" />
            <input name="end-eval" type="submit" value="%(end_eval_label)s" />
            %(end_criteria_eval)s
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(descriptions_label)s</label></td>
        <td class="content">
            <select name="descriptions">
                %(descriptions_list)s
            </select>
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(format_label)s</label></td>
        <td class="content">
            <select name="format">
                %(format_list)s
            </select>
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(parent_label)s</label></td>
        <td class="content">
            <input name="parent" type="text" size="40" value="%(parent_name)s" />
        </td>
    </tr>
    <tr>
        <td></td>
        <td class="buttons">
            %(buttons_html)s
        </td>
    </tr>
</table>
''' % d

    def do_action(self):

        "Write the iCalendar resource."

        _ = self._
        form = self.get_form()

        # If no category names or sources exist in the request, an error message
        # is returned.

        category_names = form.get("category")
        sources = form.get("source")
        search_pattern = form.get("search")

        if not (category_names or sources or search_pattern):
            return 0, _("No categories, sources or search patterns specified.")

        write_resource(self.request)
        return 1, None

    def render_success(self, msg, msgtype=None):

        """
        Render neither 'msg' nor 'msgtype' since a resource has already been
        produced.
        NOTE: msgtype is optional because MoinMoin 1.5.x does not support it.
        """

        pass

def write_resource(request):

    """
    For the given 'request', write an iCalendar summary of the event data found
    in the categories specified via the "category" request parameter, using the
    "start" and "end" parameters (if specified). Multiple "category" parameters
    can be specified.
    """

    form = get_form(request)

    category_names = form.get("category", [])
    remote_sources = form.get("source", [])
    search_pattern = form.get("search", [None])[0]
    format = form.get("format", ["iCalendar"])[0]
    descriptions = form.get("descriptions", ["page"])[0]
    parent = form.get("parent", [""])[0]
    resolution = form.get("resolution", ["month"])[0]

    # Look first for a single start and end parameter. If that fails to provide
    # dates, look for separate start and end parameters, either for complete
    # dates or for years and months.

    if resolution == "date":
        calendar_start = getFormDate(request, None, "start")
        calendar_end = getFormDate(request, None, "end")

        if calendar_start is None:
            calendar_start = getFormDateTriple(request, "start-year", "start-month", "start-day")
        if calendar_end is None:
            calendar_end = getFormDateTriple(request, "end-year", "end-month", "end-day")

    elif resolution == "month":
        calendar_start = getFormMonth(request, None, "start")
        calendar_end = getFormMonth(request, None, "end")

        if calendar_start is None:
            calendar_start = getFormMonthPair(request, "start-year", "start-month")
        if calendar_end is None:
            calendar_end = getFormMonthPair(request, "end-year", "end-month")

    # Determine the period and get the events involved.

    all_shown_events, first, last = getEventsUsingParameters(
        category_names, search_pattern, remote_sources, calendar_start, calendar_end,
        resolution, request)

    latest_timestamp = getLatestEventTimestamp(all_shown_events)

    # Output summary data...

    send_headers = get_send_headers(request)

    # Define headers.

    if format == "iCalendar":
        headers = ["Content-Type: text/calendar; charset=%s" % config.charset]
    elif format == "RSS":
        headers = ["Content-Type: application/rss+xml; charset=%s" % config.charset]

    # Define the last modified time.

    if latest_timestamp is not None:
        headers.append("Last-Modified: %s" % latest_timestamp.as_HTTP_datetime_string())

    send_headers(headers)

    # iCalendar output...

    if format == "iCalendar":
        mimetype = "text/calendar"

    # RSS output...

    elif format == "RSS":
        mimetype = "application/rss+xml"

    # Catch-all...

    else:
        mimetype = None

    formatEventsForOutputType(all_shown_events, request, mimetype, parent, descriptions, latest_timestamp)

# Action function.

def execute(pagename, request):
    EventAggregatorSummary(pagename, request).render()

# vim: tabstop=4 expandtab shiftwidth=4
