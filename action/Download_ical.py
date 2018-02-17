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
import base64
from MoinMoin import log
logging = log.getLogger(__name__)


class Download_ical(ActionBase):

    """ Export the EventCalendar data in icalendar format."""

    page = None

    def __init__(self, pagename, request):
        ActionBase.__init__(self, pagename, request)
        # print('request', request)
        # print('pagename', pagename)
        self.request = request
        self.pagename = pagename
        self.page = request.page

    def get_events_from_macro(self, request):
        "Get the page in HTML format."
        request = self.request
        self.page = request.page
        print('dir request:')
        for i in dir(request):
            print i
        return str(self.page)
        # pass

    def _generate_ical(self):
        self.request.mimetype = "text/calendar"
        self.request.content_type = "text/calendar; charset=%s" % config.charset
        pass

    def _write_ics(self):
        pass

    def f(self):
        return u'hello world'

    def _write_ics(self, out):

        "Write the output 'out' to the request/response."

        request = self.request

        send_headers = get_send_headers(request)
        headers = ["Content-Type: application/pdf"]
        send_headers(headers)
        request.write(out)

    def __setitem__(self, page):
        self.get_events_from_macro(page)
        Download_ical.__setitem__(self, page)

def execute(pagename, request):
    # print 'f:', Download_ical(pagename, request).f()  # This also works
    # Download_ical(pagename, request).request.write('FUCK YEAH IT WORKS!!!')
    # test = Download_ical(pagename, request).get_events_from_macro(request)
    Download_ical(pagename, request).f()
    # Download_ical(pagename, request).request.write(test)
    # Download_ical(pagename, request).request.write(Download_ical(pagename, request).get_events_from_macro())
    # TypeError: Expected bytes
