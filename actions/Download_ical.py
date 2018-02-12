"""
    Download_ical - allows to download EventCalendar data in icalendar format
    @copyright: 2018 Debian:RenataDAvila
    @license: AGPL-3.0.
"""
from MoinMoin.Page import Page
from MoinMoin.action import ActionBase, cache, AttachFile, do_show
from dateutil import parser
from datetime import datetime
import pytz
import icalendar
from MoinMoin import log
logging = log.getLogger(__name__)


class Download_ical(ActionBase):

    """ Export the EventCalendar data in icalendar format."""

    def __init__(self, pagename, request):
        ActionBase.__init__(self, pagename, request)
        self.request = request
        self.pagename = pagename

    def _get_events_from_macro():
        pass

    def _generate_ical():
        request.mimetype = "text/calendar"
        pass

    def _write_ics():
        pass


def execute(pagename, request):
    Download_ical(pagename, request).render()
    # Download_ical(pagename, request).send_raw()
