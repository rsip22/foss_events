# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - event (EventAggregator)

    @copyright: 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from MoinSupport import parseAttributes
from EventAggregatorSupport.Formatting import formatEvent, formatEventsForOutputType
from EventAggregatorSupport.Types import parseEvents, EventPage

Dependencies = ["pages"]

# Parser support.

class Parser:

    "Interpret and show event information in different ways."

    Dependencies = Dependencies
    extensions = []

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
        Format an event using the given formatter 'fmt'. If the 'write'
        parameter is specified, use it to write output; otherwise, write output
        using the request.
        """

        events = parseEvents(self.raw, EventPage(self.request.page), self.fragment)

        for event in events:
            formatEvent(event, self.request, fmt, write=write)

    # Extra API methods.

    def formatForOutputType(self, mimetype, write=None):

        """
        Format an event for the given 'mimetype'. If the 'write' parameter is
        specified, use it to write output; otherwise, write output using the
        request.
        """

        events = parseEvents(self.raw, EventPage(self.request.page), self.fragment)
        formatEventsForOutputType(events, self.request, mimetype, write=write)

    # Class methods.

    def getOutputTypes(self):
        return self.output_mimetypes

    getOutputTypes = classmethod(getOutputTypes)

# vim: tabstop=4 expandtab shiftwidth=4
