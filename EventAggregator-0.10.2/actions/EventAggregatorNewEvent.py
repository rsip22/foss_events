# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregatorNewEvent Action

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2003-2008 MoinMoin:ThomasWaldmann,
                2004-2006 MoinMoin:AlexanderSchremmer,
                2007 MoinMoin:ReimarBauer.
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from EventAggregatorSupport import *
from EventAggregatorSupport.Actions import ActionSupport

from MoinMoin.action import ActionBase
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin import config
import re

try:
    import pytz
except ImportError:
    pytz = None

Dependencies = ['pages']

# Action class and supporting functions.

class EventAggregatorNewEvent(ActionBase, ActionSupport):

    "An event creation dialogue requesting various parameters."

    def get_form_html(self, buttons_html):
        _ = self._
        request = self.request
        form = self.get_form()

        # Handle advanced and basic forms, and enable/disable certain fields.

        show_advanced = form.get("advanced") and not form.get("basic")
        show_end_date = form.get("end-day") and not form.get("hide-end-date") or form.get("show-end-date")
        show_times = (form.get("start-hour") or form.get("end-hour")) and not form.get("hide-times") or form.get("show-times")
        show_location = form.get("show-location") or form.get("new-location") and not form.get("hide-location")
        choose_page_name = form.get("page-name") and not form.get("auto-page-name") or form.get("choose-page-name")

        # Define the overridden page name, if appropriate.

        page_name = choose_page_name and form.get("page-name", ["@PARENT@/@TITLE@"])[0] or ""

        # Prepare the category list.

        category_list = []
        category_pagenames = form.get("category", [])

        for category_name, category_pagename in getCategoryMapping(getCategories(request), request):

            selected = self._get_selected_for_list(category_pagename, category_pagenames)

            # In the advanced view, populate a menu.

            if show_advanced:
                category_list.append('<option value="%s" %s>%s</option>' % (
                    escattr(category_pagename), selected, escape(category_name)))

            # In the basic view, use hidden fields.

            elif selected:
                category_list.append('<input value="%s" name="category" type="hidden" />' % escattr(category_pagename))

        # Prepare the topics list.

        topics = form.get("topics", [])

        if form.get("add-topic"):
            topics.append("")
        else:
            for i in range(0, len(topics)):
                if form.get("remove-topic-%d" % i):
                    del topics[i]
                    break

        # Initialise month lists.

        start_month_list, end_month_list = self.get_month_lists(default_as_current=1)
        start_year_default, end_year_default = self.get_year_defaults(default_as_current=1)

        # Initialise the locations list.

        locations_page = getLocationsPage(request)
        locations = getWikiDict(locations_page, request)

        locations_list = []
        locations_list.append('<option value=""></option>')

        location = (form.get("location") or form.get("new-location") or [""])[0]

        # Prepare the locations list, selecting the specified location.

        if locations:
            locations_list += self.get_option_list(location, locations) or []

        locations_list.sort()

        # Initialise the time regime from the location.

        start_regime = form.get("start-regime", [None])[0]
        end_regime = form.get("end-regime", [None])[0]

        if not start_regime:
            start_regime = Location(location, locations).getTimeRegime()
        end_regime = end_regime or start_regime

        # Initialise regime lists.

        start_regime_list = []
        start_regime_list.append('<option value="">%s</option>' % escape(_("<The event location (if known)>")))
        end_regime_list = []
        end_regime_list.append('<option value="">%s</option>' % escape(_("<Same as start time>")))

        # Prepare regime lists, selecting specified regimes.

        if pytz is not None:
            start_regime_list += self.get_option_list(start_regime, pytz.common_timezones)
            end_regime_list += self.get_option_list(end_regime, pytz.common_timezones)

        # Show time zone-related information depending on various fields.

        show_zone_regime = (
            form.get("start-regime")            # have a regime
            and not form.get("show-offsets")    # are not switching to offsets
            and not form.get("hide-zone")       # are not removing zone information
            or form.get("show-regime")          # are switching to a regime
            or form.get("show-times") and start_regime # are showing times with a regime
            )
        show_zone_offsets = (
            form.get("start-offset")            # have an offset
            and not form.get("show-regime")     # are not switching to a regime
            and not form.get("hide-zone")       # are not removing zone information
            or form.get("show-offsets")         # are switching to offsets
            )

        show_zones = show_zone_regime or show_zone_offsets

        # Permitting configuration of the template name.

        template_default = getattr(request.cfg, "event_aggregator_new_event_template", "EventTemplate")

        # Help page location.

        help_page_name = getattr(request.cfg, "event_aggregator_new_event_help", "HelpOnEventAggregatorNewEvent")
        help_page_url = Page(request, help_page_name).url(request)

        # Substitution of parameters.

        d = {
            "buttons_html"          : buttons_html,
            "form_trigger"          : escattr(self.form_trigger),
            "form_cancel"           : escattr(self.form_cancel),

            "category_label"        : escape(_("Categories")),
            "category_list"         : "\n".join(category_list),

            "start_month_list"      : "\n".join(start_month_list),
            "end_month_list"        : "\n".join(end_month_list),

            "start_regime_list"     : "\n".join(start_regime_list),
            "end_regime_list"       : "\n".join(end_regime_list),
            "use_regime_label"      : escape(_("Using local time in...")),

            "show_end_date_label"   : escape(_("Specify end date")),
            "hide_end_date_label"   : escape(_("End event on same day")),

            "show_times_label"      : escape(_("Specify times")),
            "hide_times_label"      : escape(_("No start and end times")),

            "show_offsets_label"    : escape(_("Specify UTC offsets")),
            "show_regime_label"     : escape(_("Use local time")),
            "hide_zone_label"       : escape(_("Make times apply everywhere")),

            "start_label"           : escape(_("Start date (day, month, year)")),
            "start_day_default"     : escattr(form.get("start-day", [""])[0]),
            "start_year_default"    : escattr(start_year_default),
            "start_time_label"      : escape(_("Start time (hour, minute, second)")),
            "start_hour_default"    : escattr(form.get("start-hour", [""])[0]),
            "start_minute_default"  : escattr(form.get("start-minute", [""])[0]),
            "start_second_default"  : escattr(form.get("start-second", [""])[0]),
            "start_offset_default"  : escattr(form.get("start-offset", [""])[0]),

            "end_label"             : escape(_("End date (day, month, year) - if different")),
            "end_day_default"       : escattr(form.get("end-day", [""])[0].strip() or form.get("start-day", [""])[0]),
            "end_year_default"      : escattr(end_year_default),
            "end_time_label"        : escape(_("End time (hour, minute, second)")),
            "end_hour_default"      : escattr(form.get("end-hour", [""])[0]),
            "end_minute_default"    : escattr(form.get("end-minute", [""])[0]),
            "end_second_default"    : escattr(form.get("end-second", [""])[0]),
            "end_offset_default"    : escattr(form.get("end-offset", [""])[0].strip() or form.get("start-offset", [""])[0]),

            "title_label"           : escape(_("Event title/summary")),
            "title_default"         : escattr(form.get("title", [""])[0]),
            "choose_page_name_label": escape(_("Choose page name")),
            "auto_page_name_label"  : escape(_("Auto page name")),
            "page_name_label"       : escape(_("Page name")),
            "page_name_default"     : escattr(form.get("page-name", [page_name])[0]),
            "description_label"     : escape(_("Event description")),
            "description_default"   : escattr(form.get("description", [""])[0]),

            "location_label"        : escape(_("Event location")),
            "locations_list"        : "\n".join(locations_list),
            "show_location_label"   : escattr(_("Specify a different location")),
            "hide_location_label"   : escattr(_("Choose a known location")),
            "new_location"          : escattr(form.get("new-location", [location])[0]),

            "latitude_label"        : escape(_("Latitude")),
            "latitude_default"      : escattr(form.get("latitude", [""])[0]),
            "longitude_label"       : escape(_("Longitude")),
            "longitude_default"     : escattr(form.get("longitude", [""])[0]),
            "link_label"            : escape(_("External URL")),
            "link_default"          : escattr(form.get("link", [""])[0]),

            "topics_label"          : escape(_("Topics")),
            "add_topic_label"       : escape(_("Add topic")),
            "remove_topic_label"    : escape(_("Remove topic")),

            "template_label"        : escape(_("Event template")),
            "template_default"      : escattr(form.get("template", [""])[0].strip() or template_default),
            "parent_label"          : escape(_("Parent page")),
            "parent_default"        : escattr(form.get("parent", [""])[0]),

            "advanced_label"        : escape(_("Show advanced options")),
            "basic_label"           : escape(_("Hide advanced options")),

            "help_page_url"         : escattr(help_page_url),
            "help_page_label"       : escape(_("Help on creating events")),
            }

        # Prepare the output HTML.

        html = '''
<input name="update-form-only" value="false" type="hidden" />
<table>
    <tr>
        <td class="label"><label>%(title_label)s</label></td>
        <td colspan="2">
            <input name="title" type="text" size="40" value="%(title_default)s" />
        </td>
    </tr>''' % d

        # Page name options.

        if choose_page_name:
            html += '''
    <tr>
        <td class="label"><label>%(page_name_label)s</label></td>
        <td colspan="2">
            <input name="page-name" type="text" size="40" value="%(page_name_default)s" />
        </td>
    <tr>
        <td class="label">
            <input name="auto-page-name" type="submit" value="%(auto_page_name_label)s" />
        </td>
    </tr>''' % d
        else:
            html += '''
    <tr>
        <td class="label">
            <input name="choose-page-name" type="submit" value="%(choose_page_name_label)s" />
        </td>
    </tr>''' % d

        # Location options.

        html += '''
    <tr>
        <td class="label"><label>%(location_label)s</label></td>
        <td colspan="2">''' % d

        if not show_location:
            html += '''
            <select name="location">
                %(locations_list)s
            </select>
            <input name="show-location" type="submit" value="%(show_location_label)s" />''' % d

        else:
            html += '''
            <input name="new-location" type="text" size="30" value="%(new_location)s" />
            <input name="hide-location" type="submit" value="%(hide_location_label)s" />''' % d

        html += '''
        </td>
    </tr>''' % d

        # Latitude and longitude.

        if show_location:
            html += '''
    <tr>
        <td class="label"><label>%(latitude_label)s</label></td>
        <td colspan="2">
            <input name="latitude" type="text" size="40" value="%(latitude_default)s" />
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(longitude_label)s</label></td>
        <td colspan="2">
            <input name="longitude" type="text" size="40" value="%(longitude_default)s" />
        </td>
    </tr>''' % d

        # Start date controls.

        html += '''
    <tr>
        <td class="label"><label>%(start_label)s</label></td>
        <td colspan="2" style="white-space: nowrap">
            <input name="start-day" type="text" value="%(start_day_default)s" size="2" />
            <select name="start-month">
                %(start_month_list)s
            </select>
            <input name="start-year" type="text" value="%(start_year_default)s" size="4" />
        </td>
    </tr>''' % d

        # End date controls.

        if show_end_date:
            html += '''
    <tr>
        <td class="label"><label>%(end_label)s</label></td>
        <td colspan="2" style="white-space: nowrap">
            <input name="end-day" type="text" value="%(end_day_default)s" size="2" />
            <select name="end-month">
                %(end_month_list)s
            </select>
            <input name="end-year" type="text" value="%(end_year_default)s" size="4" />
        </td>
    </tr>
    <tr>
        <td class="label">
            <input name="hide-end-date" type="submit" value="%(hide_end_date_label)s" />
        </td>
    </tr>''' % d
        else:
            html += '''
    <tr>
        <td class="label">
            <input name="show-end-date" type="submit" value="%(show_end_date_label)s" />
        </td>
    </tr>''' % d

        # Generic time information.

        if show_times:

            # Start time controls.

            html += '''
    <tr>
        <td class="label event-time-selection"><label>%(start_time_label)s</label></td>
        <td style="white-space: nowrap" class="event-time-selection">
            <input name="start-hour" type="text" value="%(start_hour_default)s" size="2" maxlength="2" />
            <input name="start-minute" type="text" value="%(start_minute_default)s" size="2" maxlength="2" />
            <input name="start-second" type="text" value="%(start_second_default)s" size="2" maxlength="2" />
        </td>''' % d

            # Offset information displayed.

            if show_zone_offsets:
                html += '''
        <td class="event-zone-selection">
            UTC <input name="start-offset" type="text" value="%(start_offset_default)s" size="6" maxlength="6" />
        </td>''' % d

            # Regime information displayed.

            elif show_zone_regime:
                html += '''
        <td class="event-regime-selection">
            <label>%(use_regime_label)s</label><br/>
            <select name="start-regime">
                %(start_regime_list)s
            </select>
        </td>''' % d

            html += '''
    </tr>'''

            # End time controls.

            html += '''
    <tr>
        <td class="label event-time-selection"><label>%(end_time_label)s</label></td>
        <td style="white-space: nowrap" class="event-time-selection">
            <input name="end-hour" type="text" value="%(end_hour_default)s" size="2" maxlength="2" />
            <input name="end-minute" type="text" value="%(end_minute_default)s" size="2" maxlength="2" />
            <input name="end-second" type="text" value="%(end_second_default)s" size="2" maxlength="2" />
        </td>''' % d

            # Offset information displayed.

            if show_zone_offsets:
                html += '''
        <td class="event-zone-selection">
            UTC <input name="end-offset" type="text" value="%(end_offset_default)s" size="6" maxlength="6" />
        </td>''' % d

            # Regime information displayed.

            elif show_zone_regime:
                html += '''
        <td class="event-regime-selection event-end-time">
            <select name="end-regime">
                %(end_regime_list)s
            </select>
        </td>''' % d

            # Controls for removing times.

            html += '''
    </tr>
    <tr>
        <td class="label">
            <input name="hide-times" type="submit" value="%(hide_times_label)s" />
        </td>
        <td></td>
        <td>''' % d

            # Time zone controls.

            if show_zones:

                # To remove zone information.

                html += '''
            <input name="hide-zone" type="submit" value="%(hide_zone_label)s" />''' % d

            # No time zone information shown.

            else:
                html += '''
            <input name="show-regime" type="submit" value="%(show_regime_label)s" />
            <input name="show-offsets" type="submit" value="%(show_offsets_label)s" />''' % d

            html += '''
        </td>
    </tr>'''

        # Controls for adding times.

        else:
            html += '''
    <tr>
        <td class="label">
            <input name="show-times" type="submit" value="%(show_times_label)s" />
        </td>
    </tr>''' % d


        # Various basic controls.

        html += '''
    <tr>
        <td class="label"><label>%(description_label)s</label></td>
        <td colspan="2">
            <input name="description" type="text" size="40" value="%(description_default)s" />
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(link_label)s</label></td>
        <td colspan="2">
            <input name="link" type="text" size="40" value="%(link_default)s" />
        </td>
    </tr>''' % d

        # Topics.

        for i, topic in enumerate(topics):
            d["topic"] = escattr(topic)
            d["topic_number"] = i
            html += '''
    <tr>
        <td class="label"><label>%(topics_label)s</label></td>
        <td colspan="2">
            <input name="topics" type="text" size="20" value="%(topic)s" />
            <input name="remove-topic-%(topic_number)s" type="submit" value="%(remove_topic_label)s" />
        </td>
    </tr>''' % d

        html += '''
    <tr>
        <td></td>
        <td colspan="2">
            <input name="add-topic" type="submit" value="%(add_topic_label)s" />
        </td>
    </tr>''' % d

        # Advanced options.

        if show_advanced:
            html += '''
    <tr>
        <td></td>
        <td colspan="2">
            <input name="basic" type="submit" value="%(basic_label)s" />
            <input name="advanced" type="hidden" value="true" />
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(category_label)s</label></td>
        <td colspan="2" class="content">
            <select multiple="multiple" name="category">
                %(category_list)s
            </select>
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(template_label)s</label></td>
        <td colspan="2">
            <input name="template" type="text" size="40" value="%(template_default)s" />
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(parent_label)s</label></td>
        <td colspan="2">
            <input name="parent" type="text" size="40" value="%(parent_default)s" />
        </td>
    </tr>
    <tr>
        <td></td>
        <td colspan="2" class="buttons">
            %(buttons_html)s
        </td>
    </tr>
    <tr>
        <td></td>
        <td colspan="2">
            <a href="%(help_page_url)s" target="_blank">%(help_page_label)s</a>
        </td>
    </tr>
</table>''' % d
        else:
            html += '''
    <tr>
        <td></td>
        <td colspan="2">
            <input name="advanced" type="submit" value="%(advanced_label)s" />
            %(category_list)s
            <input name="parent" type="hidden" value="%(parent_default)s" />
            <input name="template" type="hidden" value="%(template_default)s" />
        </td>
    </tr>
    <tr>
        <td></td>
        <td colspan="2" class="buttons">
            %(buttons_html)s
        </td>
    </tr>
    <tr>
        <td></td>
        <td colspan="2">
            <a href="%(help_page_url)s" target="_blank">%(help_page_label)s</a>
        </td>
    </tr>
</table>
<script type="text/javascript">
function replaceDialog(url, button) {
    var form = findForm();
    var dialog = findDialog(document);
    if (form != null && dialog != null) {
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.open("POST", url, false);
        xmlhttp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        var requestBody = encodeURIComponent(button.name) + "=" + encodeURIComponent(button.value);
        for (var i = 0; i < form.elements.length; i++) {
            var element = form.elements[i];
            if (element.type != "submit") {
                requestBody += "&" + encodeURIComponent(element.name) + "=" + encodeURIComponent(element.value);
            }
        }
        xmlhttp.send(requestBody);

        var newDialog = xmlhttp.responseText;

        if (newDialog != null) {
            dialog.parentNode.innerHTML = newDialog;
            initForm();
            return false;
        }
    }
}

function findDialog(d) {
    var elements = d.getElementsByTagName("div");
    for (var i = 0; i < elements.length; i++) {
        var element = elements[i];
        var cls = element.getAttribute("class");
        if (cls == "dialog") {
            return element;
        }
    }
    return null;
}

function findForm() {
    for (var i = 0; i < document.forms.length; i++) {
        var form = document.forms[i];
        if (form["update-form-only"] != null) {
            return form;
        }
    }
    return null;
}

function initForm() {
    var form = findForm();
    var url = form.getAttribute("action");
    form["update-form-only"].value = "true";
    for (var i = 0; i < form.length; i++) {
        var element = form[i];
        if (element.type == "submit" && element.name != "%(form_trigger)s" && element.name != "%(form_cancel)s") {
            element.setAttribute("onclick", "return replaceDialog('" + url + "', this);");
        }
    }
}

initForm();
</script>''' % d

        return html

    def do_action(self):

        "Create the new event."

        _ = self._
        form = self.get_form()

        # If no title exists in the request, an error message is returned.

        title = form.get("title", [None])[0]
        template = form.get("template", [None])[0]

        if not title:
            return 0, _("No event title specified.")

        if not template:
            return 0, _("No page template specified.")

        return self.create_event(self.request)

    def render_msg(self, msg, msgtype):

        """
        Render 'msg' and 'msgtype'. If 'msgtype' is "dialog" then the form is
        rendered, and if only part of the form is being requested, the output
        will be only the form HTML fragment and not the entire page.
        """

        # Either render the form as a fragment of a page.

        form = self.get_form()
        update_form_only = form.get("update-form-only", ["false"])[0] == "true"
        action_attempted = form.has_key(self.form_trigger)

        if msgtype == "dialog" and update_form_only and not action_attempted:
            send_headers = get_send_headers(self.request)
            send_headers(["Content-Type: text/html; charset=%s" % config.charset])
            self.request.write(msg.render())

        # Or render the message/form within an entire page.

        else:
            ActionBase.render_msg(self, msg, msgtype)

    def render_success(self, msg, msgtype):

        """
        Render neither 'msg' nor 'msgtype' since redirection should occur
        instead.
        """

        pass

    def create_event(self, request):

        "Create an event page using the 'request'."

        _ = request.getText
        form = self.get_form()

        category_pagenames = form.get("category", [])
        description = form.get("description", [None])[0]
        location = (form.get("location") or form.get("new-location") or [""])[0]
        latitude = form.get("latitude", [None])[0]
        longitude = form.get("longitude", [None])[0]
        link = form.get("link", [None])[0]
        topics = form.get("topics", [])

        start_regime = form.get("start-regime", [None])[0]
        end_regime = form.get("end-regime", form.get("start-regime", [None]))[0]
        start_offset = form.get("start-offset", [None])[0]
        end_offset = form.get("end-offset", [None])[0]

        start_zone = start_regime or start_offset
        end_zone = end_regime or end_offset

        page_name = form.get("page-name", [None])[0]

        # Validate certain fields.

        title = form.get("title", [""])[0].strip()
        template = form.get("template", [""])[0].strip()
        parent = form.get("parent", [""])[0].strip()

        if not title:
            return 0, _("No event title specified.")
        if not template:
            return 0, _("No event template specified.")

        try:
            start_day = self._get_input(form, "start-day")
            start_month = self._get_input(form, "start-month")
            start_year = self._get_input(form, "start-year")

            if not start_day or not start_month or not start_year:
                return 0, _("A start date must be specified.")

            end_day = self._get_input(form, "end-day", start_day)
            end_month = self._get_input(form, "end-month", start_month)
            end_year = self._get_input(form, "end-year", start_year)

        except (TypeError, ValueError):
            return 0, _("Days and years must be numbers yielding a valid date!")

        try:
            start_hour = self._get_input(form, "start-hour")
            start_minute = self._get_input(form, "start-minute")
            start_second = self._get_input(form, "start-second")

            end_hour = self._get_input(form, "end-hour")
            end_minute = self._get_input(form, "end-minute")
            end_second = self._get_input(form, "end-second")

        except (TypeError, ValueError):
            return 0, _("Hours, minutes and seconds must be numbers yielding a valid time!")

        start_date = DateTime(
            (start_year, start_month, start_day, start_hour, start_minute, start_second, start_zone)
            )
        start_date.constrain()

        end_date = DateTime(
            (end_year, end_month, end_day, end_hour, end_minute, end_second, end_zone)
            )
        end_date.constrain()

        # An elementary date ordering check.

        if (start_date.as_date() != end_date.as_date() or start_date.has_time() and end_date.has_time()) and start_date > end_date:
            start_date, end_date = end_date, start_date

        event_details = {
            "start" : str(start_date), "end" : str(end_date),
            "title" : title, "summary" : title,
            "description" : description, "location" : location, "link" : link,
            "topics" : [topic for topic in topics if topic]
            }

        if latitude and longitude:
            event_details["geo"] = latitude, longitude

        # Copy the template.

        template_page = PageEditor(request, template)

        if not template_page.exists():
            return 0, _("Event template not available.")

        # Use any parent page information.

        full_title = getFullPageName(parent, title)

        if page_name:

            # Allow parameters in the page name. This permits a degree of
            # interoperability with MonthCalendar.

            page_name = page_name.replace("@PAGE@", request.page.page_name)
            page_name = page_name.replace("@DATE@", str(start_date.as_date()))
            page_name = page_name.replace("@STARTDATE@", str(start_date.as_date()))
            page_name = page_name.replace("@ENDDATE@", str(end_date.as_date()))
            page_name = page_name.replace("@PARENT@", parent)
            page_name = page_name.replace("@TITLE@", title)

            # Normalise any page hierarchy separators.

            page_name = re.sub("/+", "/", page_name)

        else:
            page_name = full_title

        # Load the new page and replace the event details in the body.

        new_page = PageEditor(request, page_name)

        if new_page.exists():
            return 0, _("The specified page already exists. Please choose another name.")

        # Complete the new page and return its body.

        body = fillEventPageFromTemplate(template_page, new_page, event_details, category_pagenames)

        # Open the page editor on the new page.
        # NOTE: Replacing the revision in the request to prevent Moin from
        # NOTE: attempting to use the queued changes page's revision.
        # NOTE: Replacing the action and page in the request to avoid issues
        # NOTE: with editing tickets.

        request.rev = 0
        request.action = "edit"
        request.page = new_page
        new_page.sendEditor(preview=body, staytop=True)

        # Return success.

        return 1, None

# Action function.

def execute(pagename, request):
    EventAggregatorNewEvent(pagename, request).render()

# vim: tabstop=4 expandtab shiftwidth=4
