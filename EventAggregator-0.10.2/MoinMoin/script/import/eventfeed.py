# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Event feed importer, based on the FeedReader macro, the irclog
               script in MoinMoin, and the EventAggregatorNewEvent action

    @copyright: 2008, 2009, 2010 by Paul Boddie <paul@boddie.org.uk>
                2005-2007 MoinMoin:AlexanderSchremmer
                2006 MoinMoin:ThomasWaldmann

    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from MoinMoin.PageEditor import PageEditor
from MoinMoin.script import MoinScript
import EventAggregatorSupport
import urllib
import xml.dom.pulldom

# Utility class from the irclog script.

class IAmRoot(object):
    def __getattr__(self, name):
        return lambda *args, **kwargs: True

# The script's class.

class PluginScript(MoinScript):

    """\
Purpose:
========
This tool imports events from an RSS feed into event pages.

Detailed Instructions:
======================
General syntax: moin [options] import eventfeed [eventfeed-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[eventfeed-options] see below:
    0. To import events from the FSFE event feed
       moin ... import eventfeed --url=http://www.fsfe.org/events/events.en.rss ...

    1. To use a specific template such as 'EventTemplate'
       moin ... import eventfeed --template=EventTemplate ...

    2. To assign pages to specific categories such as 'CategoryEvents CategoryMeetings'
       moin ... import eventfeed --categories='CategoryEvents CategoryMeetings' ...

    3. To use a specific author such as 'EventImporter'
       moin ... import eventfeed --author=EventImporter ...

    4. To add pages under a common parent page such as 'Events'
       moin ... import eventfeed --parent=Events ...

    5. To overwrite existing event pages
       moin ... import eventfeed --overwrite ...

    6. To delete any event pages associated with the feed
       moin ... import eventfeed --delete ...
"""

    FIELDS = ("title", "link", "description")

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--url", dest="url", default="",
            help="Specify the location of the events RSS feed"
        )
        self.parser.add_option(
            "--template", dest="template", default="EventTemplate",
            help="Specify the template used to make the event pages"
        )
        self.parser.add_option(
            "--categories", dest="categories", default="CategoryEvents",
            help="Specify the categories to which the event pages will belong"
        )
        self.parser.add_option(
            "--author", dest="author", default="EventImporter",
            help="Specify the author of the event pages"
        )
        self.parser.add_option(
            "--parent", dest="parent", default="",
            help="Specify the parent page of the event pages"
        )
        self.parser.add_option(
            "--overwrite", dest="overwrite", action="store_true",
            help="Request that existing pages be overwritten"
        )
        self.parser.add_option(
            "--delete", dest="delete", action="store_true",
            help="Request that event pages associated with the feed be deleted"
        )

    def mainloop(self):
        self.init_request()
        if not self.options.url:
            print "No URL specified. Not importing any events!"
        else:
            self.read_events(self.options.url)

    def read_events(self, url):

        """
        Read events from the given events RSS feed, specified by 'url', creating
        new Wiki pages where appropriate.
        """

        request = self.request
        request.user.may = IAmRoot()
        category_pagenames = self.options.categories.split()

        # Locate the template for events.

        template_page = PageEditor(request, self.options.template)

        if not template_page.exists():
            print "Template %r cannot be found. Not importing any events!" % self.options.template
            return

        # Process the feed.

        feed = urllib.urlopen(url)

        try:
            nodes = xml.dom.pulldom.parse(feed)
            event_details = {}

            in_item = 0

            # Read the nodes from the feed.

            for node_type, value in nodes:
                if node_type == xml.dom.pulldom.START_ELEMENT:
                    if value.nodeName == "item":
                        in_item = 1

                    # Get the value of the important fields.

                    elif in_item and value.nodeName in self.FIELDS:
                        nodes.expandNode(value)
                        event_details[value.nodeName] = self.text(value)

                    # Where all fields have been read, make a new page.

                    if reduce(lambda x, y: x and event_details.has_key(y), self.FIELDS, 1):

                        # Define the page.

                        title = event_details["title"]

                        # Use any parent page information.

                        full_title = EventAggregatorSupport.getFullPageName(self.options.parent, title)

                        # Find the start and end dates.

                        dates = EventAggregatorSupport.getDateStrings(title)

                        # Require one or two dates.

                        if dates and 1 <= len(dates) <= 2:

                            # Deduce the end date.

                            if len(dates) == 2:
                                start_date, end_date = dates
                            elif len(dates) == 1:
                                start_date = end_date = dates[0]

                            # Load the new page and replace the event details in the body.

                            new_page = PageEditor(request, full_title,
                                uid_override=self.options.author)

                            # Delete the page if requested.

                            if new_page.exists() and self.options.delete:

                                try:
                                    new_page.deletePage()
                                except new_page.AccessDenied:
                                    print "Page %r has not been deleted." % full_title

                            # Complete the new page.

                            elif not new_page.exists() or self.options.overwrite:
                                event_details["summary"] = title
                                event_details["start"] = start_date
                                event_details["end"] = end_date

                                try:
                                    EventAggregatorSupport.fillEventPageFromTemplate(
                                        template_page, new_page, event_details,
                                        category_pagenames)

                                except new_page.Unchanged:
                                    print "Page %r is not changed." % full_title

                            else:
                                print "Not overwriting page %r." % full_title

                        else:
                            print "Could not deduce dates from %r." % title

                        event_details = {}

                elif node_type == xml.dom.pulldom.END_ELEMENT:
                    if value.nodeName == "item":
                        in_item = 0

        finally:
            feed.close()

    def text(self, element):

        "Return the text within the given 'element'."

        nodes = []
        for node in element.childNodes:
            if node.nodeType == node.TEXT_NODE:
                nodes.append(node.nodeValue)
        return "".join(nodes)

# vim: tabstop=4 expandtab shiftwidth=4
