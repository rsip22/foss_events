# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator action support library

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from DateSupport import *
from MoinSupport import *
from MoinDateSupport import getFormDate, getFormMonth, \
                            getParameterDate, getParameterMonth

from MoinMoin.wikiutil import escape

# Utility classes and associated functions.

class ActionSupport(ActionSupport):

    "Extend the generic action support."

    def get_month_lists(self, default_as_current=0):

        """
        Return two lists of HTML element definitions corresponding to the start
        and end month selection controls, with months selected according to any
        values that have been specified via request parameters.
        """

        _ = self._
        form = self.get_form()

        # Initialise month lists.

        start_month_list = []
        end_month_list = []

        start_month = self._get_input(form, "start-month", default_as_current and getCurrentMonth().month() or None)
        end_month = self._get_input(form, "end-month", start_month)

        # Prepare month lists, selecting specified months.

        if not default_as_current:
            start_month_list.append('<option value=""></option>')
            end_month_list.append('<option value=""></option>')

        for month in range(1, 13):
            month_label = escape(_(getMonthLabel(month)))
            selected = self._get_selected(month, start_month)
            start_month_list.append('<option value="%02d" %s>%s</option>' % (month, selected, month_label))
            selected = self._get_selected(month, end_month)
            end_month_list.append('<option value="%02d" %s>%s</option>' % (month, selected, month_label))

        return start_month_list, end_month_list

    def get_year_defaults(self, default_as_current=0):

        "Return defaults for the start and end years."

        form = self.get_form()

        start_year_default = form.get("start-year", [default_as_current and getCurrentYear() or ""])[0]
        end_year_default = form.get("end-year", [default_as_current and start_year_default or ""])[0]

        return start_year_default, end_year_default

    def get_day_defaults(self, default_as_current=0):

        "Return defaults for the start and end days."

        form = self.get_form()

        start_day_default = form.get("start-day", [default_as_current and getCurrentDate().day() or ""])[0]
        end_day_default = form.get("end-day", [default_as_current and start_day_default or ""])[0]

        return start_day_default, end_day_default

def get_date_functions(resolution):
    if resolution == "date":
        return getParameterDate, getFormDate
    else:
        return getParameterMonth, getFormMonth

def get_date_label_functions(resolution):
    if resolution == "date":
        return getParameterDate, getFullDateLabel
    else:
        return getParameterMonth, getFullMonthLabel

# vim: tabstop=4 expandtab shiftwidth=4
