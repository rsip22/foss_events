# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - calendar (EventAggregator)

    @copyright: 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from MoinSupport import parseAttributes
from EventAggregatorSupport.Formatting import formatEventsForOutputType
from EventAggregatorSupport.Types import parseEvents, EventCalendar
from codecs import getreader
import vCalendar

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

Dependencies = ["pages"]

# Parser support.

class Parser:

    "Interpret and show calendar information in different ways."

    Dependencies = Dependencies
    extensions = [".ics"]

    # Input content types understood by this parser.

    input_mimetypes = ["text/calendar"]

    # Output content types preferred by this parser.

    output_mimetypes = ["text/html", "text/calendar"]

    def __init__(self, raw, request, **kw):

        """
        Initialise the parser with the given 'raw' data, 'request' and any
        keyword arguments that may have been supplied.
        """

        self.raw = raw
        self.request = request
        attrs = parseAttributes(kw.get("format_args", ""), False)

        self.fragment = attrs.get("fragment")

    def format(self, fmt, write=None):

        """
        Format a calendar using the given formatter 'fmt'. If the 'write'
        parameter is specified, use it to write output; otherwise, write output
        using the request.
        """

        (write or self.request.write)(fmt.text(self.raw))

    # Extra API methods.

    def formatForOutputType(self, mimetype, write=None):

        """
        Format a calendar for the given 'mimetype'. If the 'write' parameter is
        specified, use it to write output; otherwise, write output using the
        request.
        """

        # Write raw calendar information unchanged.

        if mimetype == "text/calendar":
            (write or request.write)(self.raw)
        else:
            # Make a Unicode-capable StringIO.

            f = getreader("utf-8")(StringIO(self.raw.encode("utf-8")))
            calendar = EventCalendar("", vCalendar.parse(f), {})
            formatEventsForOutputType(calendar.getEvents(), self.request, mimetype, write=write)

    # Class methods.

    def getOutputTypes(self):
        return self.output_mimetypes

    getOutputTypes = classmethod(getOutputTypes)

# vim: tabstop=4 expandtab shiftwidth=4
