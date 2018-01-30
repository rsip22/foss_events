# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator object types

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2005-2008 MoinMoin:ThomasWaldmann.
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from DateSupport import DateTime
from GeneralSupport import to_list
from LocationSupport import getMapReference
from MoinSupport import *

from email.utils import parsedate
import re

try:
    set
except NameError:
    from sets import Set as set

# Page parsing.

definition_list_regexp = re.compile(ur'(?P<wholeterm>^(?P<optcomment>#*)\s+(?P<term>.*?):: )(?P<desc>.*?)$', re.UNICODE | re.MULTILINE)
category_membership_regexp = re.compile(ur"^\s*(?:(Category\S+)(?:\s+(Category\S+))*)\s*$", re.MULTILINE | re.UNICODE)

# Event parsing from page texts.

def parseEvents(text, event_page, fragment=None):

    """
    Parse events in the given 'text', returning a list of event objects for the
    given 'event_page'. An optional 'fragment' can be specified to indicate a
    specific region of the event page.

    If the optional 'fragment' identifier is provided, the first heading may
    also be used to provide an event summary/title.
    """

    template_details = {}
    if fragment:
        template_details["fragment"] = fragment

    details = {}
    details.update(template_details)
    raw_details = {}

    # Obtain a heading, if requested.

    if fragment:
        for level, title, (start, end) in getHeadings(text):
            raw_details["title"] = text[start:end]
            details["title"] = getSimpleWikiText(title.strip())
            break

    # Start populating events.

    events = [Event(event_page, details, raw_details)]

    # Get any default raw details to modify.

    raw_details = events[-1].getRawDetails()

    for match in definition_list_regexp.finditer(text):

        # Skip commented-out items.

        if match.group("optcomment"):
            continue

        # Permit case-insensitive list terms.

        term = match.group("term").lower()
        raw_desc = match.group("desc")

        # Special value type handling.

        # Dates.

        if term in Event.date_terms:
            desc = getDateTime(raw_desc)

        # Lists (whose elements may be quoted).

        elif term in Event.list_terms:
            desc = map(getSimpleWikiText, to_list(raw_desc, ","))

        # Position details.

        elif term == "geo":
            try:
                desc = map(getMapReference, to_list(raw_desc, None))
                if len(desc) != 2:
                    continue
            except (KeyError, ValueError):
                continue

        # Labels which may well be quoted.

        elif term in Event.title_terms:
            desc = getSimpleWikiText(raw_desc.strip())

        # Plain Wiki text terms.

        elif term in Event.other_terms:
            desc = raw_desc.strip()

        else:
            desc = raw_desc

        if desc is not None:

            # Handle apparent duplicates by creating a new set of
            # details.

            if details.has_key(term):

                # Make a new event.

                details = {}
                details.update(template_details)
                raw_details = {}
                events.append(Event(event_page, details, raw_details))
                raw_details = events[-1].getRawDetails()

            details[term] = desc
            raw_details[term] = raw_desc

    return events

# Event resources providing collections of events.

class EventResource:

    "A resource providing event information."

    def __init__(self, url):
        self.url = url

    def getPageURL(self):

        "Return the URL of this page."

        return self.url

    def getFormat(self):

        "Get the format used by this resource."

        return "plain"

    def getMetadata(self):

        """
        Return a dictionary containing items describing the page's "created"
        time, "last-modified" time, "sequence" (or revision number) and the
        "last-comment" made about the last edit.
        """

        return {}

    def getEvents(self):

        "Return a list of events from this resource."

        return []

    def linkToPage(self, request, text, query_string=None, anchor=None):

        """
        Using 'request', return a link to this page with the given link 'text'
        and optional 'query_string' and 'anchor'.
        """

        return linkToResource(self.url, request, text, query_string, anchor)

    # Formatting-related functions.

    def formatText(self, text, fmt):

        """
        Format the given 'text' using the specified formatter 'fmt'.
        """

        # Assume plain text which is then formatted appropriately.

        return fmt.text(text)

class EventCalendar(EventResource):

    "An iCalendar resource."

    def __init__(self, url, calendar, metadata):
        EventResource.__init__(self, url)
        self.calendar = calendar
        self.metadata = metadata
        self.events = None

        if not self.metadata.has_key("created") and self.metadata.has_key("date"):
            self.metadata["created"] = DateTime(parsedate(self.metadata["date"])[:7])

        if self.metadata.has_key("last-modified") and not isinstance(self.metadata["last-modified"], DateTime):
            self.metadata["last-modified"] = DateTime(parsedate(self.metadata["last-modified"])[:7])

    def getMetadata(self):

        """
        Return a dictionary containing items describing the page's "created"
        time, "last-modified" time, "sequence" (or revision number) and the
        "last-comment" made about the last edit.
        """

        return self.metadata

    def getEvents(self):

        "Return a list of events from this resource."

        if self.events is None:
            self.events = []

            _calendar, _empty, calendar = self.calendar

            for objtype, attrs, obj in calendar:

                # Read events.

                if objtype == "VEVENT":
                    details = {}

                    for property, attrs, value in obj:

                        # Convert dates.

                        if property in ("DTSTART", "DTEND", "CREATED", "DTSTAMP", "LAST-MODIFIED"):
                            if property in ("DTSTART", "DTEND"):
                                property = property[2:]
                            if attrs.get("VALUE") == "DATE":
                                value = getDateFromCalendar(value)
                                if value and property == "END":
                                    value = value.previous_day()
                            else:
                                value = getDateTimeFromCalendar(value)

                        # Convert numeric data.

                        elif property == "SEQUENCE":
                            value = int(value)

                        # Convert lists.

                        elif property == "CATEGORIES":
                            value = to_list(value, ",")

                        # Convert positions (using decimal values).

                        elif property == "GEO":
                            try:
                                value = map(getMapReferenceFromDecimal, to_list(value, ";"))
                                if len(value) != 2:
                                    continue
                            except (KeyError, ValueError):
                                continue

                        # Accept other textual data as it is.

                        elif property in ("LOCATION", "SUMMARY", "URL"):
                            value = value or None

                        # Ignore other properties.

                        else:
                            continue

                        property = property.lower()
                        details[property] = value

                    self.events.append(CalendarEvent(self, details))

        return self.events

class EventPage:

    "An event page acting as an event resource."

    def __init__(self, page):
        self.page = page
        self.events = None
        self.body = None
        self.categories = None
        self.metadata = None

    def copyPage(self, page):

        "Copy the body of the given 'page'."

        self.body = page.getBody()

    def getPageURL(self):

        "Return the URL of this page."

        return getPageURL(self.page)

    def getFormat(self):

        "Get the format used on this page."

        return getFormat(self.page)

    def getMetadata(self):

        """
        Return a dictionary containing items describing the page's "created"
        time, "last-modified" time, "sequence" (or revision number) and the
        "last-comment" made about the last edit.
        """

        if self.metadata is None:
            self.metadata = getMetadata(self.page)
        return self.metadata

    def getRevisions(self):

        "Return a list of page revisions."

        return self.page.getRevList()

    def getPageRevision(self):

        "Return the revision details dictionary for this page."

        return getPageRevision(self.page)

    def getPageName(self):

        "Return the page name."

        return self.page.page_name

    def getPrettyPageName(self):

        "Return a nicely formatted title/name for this page."

        return getPrettyPageName(self.page)

    def getBody(self):

        "Get the current page body."

        if self.body is None:
            self.body = self.page.get_raw_body()
        return self.body

    def getEvents(self):

        "Return a list of events from this page."

        if self.events is None:
            self.events = []
            if self.getFormat() == "wiki":
                for format, attributes, region in getFragments(self.getBody(), True):
                    self.events += parseEvents(region, self, attributes.get("fragment"))

        return self.events

    def setEvents(self, events):

        "Set the given 'events' on this page."

        self.events = events

    def getCategoryMembership(self):

        "Get the category names from this page."

        if self.categories is None:
            body = self.getBody()
            match = category_membership_regexp.search(body)
            self.categories = match and [x for x in match.groups() if x] or []

        return self.categories

    def setCategoryMembership(self, category_names):

        """
        Set the category membership for the page using the specified
        'category_names'.
        """

        self.categories = category_names

    def flushEventDetails(self):

        "Flush the current event details to this page's body text."

        new_body_parts = []
        end_of_last_match = 0
        body = self.getBody()

        events = iter(self.getEvents())

        event = events.next()
        event_details = event.getDetails()
        replaced_terms = set()

        for match in definition_list_regexp.finditer(body):

            # Permit case-insensitive list terms.

            term = match.group("term").lower()
            desc = match.group("desc")

            # Check that the term has not already been substituted. If so,
            # get the next event.

            if term in replaced_terms:
                try:
                    event = events.next()

                # No more events.

                except StopIteration:
                    break

                event_details = event.getDetails()
                replaced_terms = set()

            # Add preceding text to the new body.

            new_body_parts.append(body[end_of_last_match:match.start()])

            # Get the matching regions, adding the term to the new body.

            new_body_parts.append(match.group("wholeterm"))

            # Special value type handling.

            if event_details.has_key(term):

                # Dates.

                if term in event.date_terms:
                    desc = desc.replace("YYYY-MM-DD", str(event_details[term]))

                # Lists (whose elements may be quoted).

                elif term in event.list_terms:
                    desc = ", ".join([getEncodedWikiText(item) for item in event_details[term]])

                # Labels which must be quoted.

                elif term in event.title_terms:
                    desc = getEncodedWikiText(event_details[term])

                # Position details.

                elif term == "geo":
                    desc = " ".join(map(str, event_details[term]))

                # Text which need not be quoted, but it will be Wiki text.

                elif term in event.other_terms:
                    desc = event_details[term]

                replaced_terms.add(term)

            # Add the replaced value.

            new_body_parts.append(desc)

            # Remember where in the page has been processed.

            end_of_last_match = match.end()

        # Write the rest of the page.

        new_body_parts.append(body[end_of_last_match:])

        self.body = "".join(new_body_parts)

    def flushCategoryMembership(self):

        "Flush the category membership to the page body."

        body = self.getBody()
        category_names = self.getCategoryMembership()
        match = category_membership_regexp.search(body)

        if match:
            self.body = "".join([body[:match.start()], " ".join(category_names), body[match.end():]])

    def saveChanges(self):

        "Save changes to the event."

        self.flushEventDetails()
        self.flushCategoryMembership()
        self.page.saveText(self.getBody(), 0)

    def linkToPage(self, request, text, query_string=None, anchor=None):

        """
        Using 'request', return a link to this page with the given link 'text'
        and optional 'query_string' and 'anchor'.
        """

        return linkToPage(request, self.page, text, query_string, anchor)

    # Formatting-related functions.

    def getParserClass(self, format):

        """
        Return a parser class for the given 'format', returning a plain text
        parser if no parser can be found for the specified 'format'.
        """

        return getParserClass(self.page.request, format)

    def formatText(self, text, fmt):

        """
        Format the given 'text' using the specified formatter 'fmt'.
        """

        fmt.page = page = self.page
        request = page.request

        parser_cls = self.getParserClass(self.getFormat())
        return formatText(text, request, fmt, parser_cls)

# Event details.

class Event(ActsAsTimespan):

    "A description of an event."

    title_terms = "title", "summary"
    date_terms  = "start", "end"
    list_terms  = "topics", "categories"
    other_terms = "description", "location", "link"
    geo_terms   = "geo",
    all_terms = title_terms + date_terms + list_terms + other_terms + geo_terms

    def __init__(self, page, details, raw_details=None):
        self.page = page
        self.details = details
        self.raw_details = raw_details or {}

        # Permit omission of the end of the event by duplicating the start.

        if self.details.has_key("start") and not self.details.get("end"):
            end = self.details["start"]

            # Make any end time refer to the day instead.

            if isinstance(end, DateTime):
                end = end.as_date()

            self.details["end"] = end

    def __repr__(self):
        return "<Event %r %r>" % (self.getSummary(), self.as_limits())

    def __hash__(self):

        """
        Return a dictionary hash, avoiding mistaken equality of events in some
        situations (notably membership tests) by including the URL as well as
        the summary.
        """

        return hash(self.getSummary() + self.getEventURL())

    def getPage(self):

        "Return the page describing this event."

        return self.page

    def setPage(self, page):

        "Set the 'page' describing this event."

        self.page = page

    def getEventURL(self):

        "Return the URL of this event."

        fragment = self.details.get("fragment")
        return self.page.getPageURL() + (fragment and "#" + fragment or "")

    def linkToEvent(self, request, text, query_string=None):

        """
        Using 'request', return a link to this event with the given link 'text'
        and optional 'query_string'.
        """

        return self.page.linkToPage(request, text, query_string, self.details.get("fragment"))

    def getMetadata(self):

        """
        Return a dictionary containing items describing the event's "created"
        time, "last-modified" time, "sequence" (or revision number) and the
        "last-comment" made about the last edit.
        """

        # Delegate this to the page.

        return self.page.getMetadata()

    def getSummary(self, event_parent=None):

        """
        Return either the given title or summary of the event according to the
        event details, or a summary made from using the pretty version of the
        page name.

        If the optional 'event_parent' is specified, any page beneath the given
        'event_parent' page in the page hierarchy will omit this parent information
        if its name is used as the summary.
        """

        event_details = self.details

        if event_details.has_key("title"):
            return event_details["title"]
        elif event_details.has_key("summary"):
            return event_details["summary"]
        else:
            # If appropriate, remove the parent details and "/" character.

            title = self.page.getPageName()

            if event_parent and title.startswith(event_parent):
                title = title[len(event_parent.rstrip("/")) + 1:]

            return getPrettyTitle(title)

    def getDetails(self):

        "Return the details for this event."

        return self.details

    def setDetails(self, event_details):

        "Set the 'event_details' for this event."

        self.details = event_details

    def getRawDetails(self):

        "Return the details for this event as they were written in a page."

        return self.raw_details

    # Timespan-related methods.

    def __contains__(self, other):
        return self == other

    def __eq__(self, other):
        if isinstance(other, Event):
            return self.getSummary() == other.getSummary() and self.getEventURL() == other.getEventURL() and self._cmp(other)
        else:
            return self._cmp(other) == 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self._cmp(other) == -1

    def __le__(self, other):
        return self._cmp(other) in (-1, 0)

    def __gt__(self, other):
        return self._cmp(other) == 1

    def __ge__(self, other):
        return self._cmp(other) in (0, 1)

    def _cmp(self, other):

        "Compare this event to an 'other' event purely by their timespans."

        if isinstance(other, Event):
            return cmp(self.as_timespan(), other.as_timespan())
        else:
            return cmp(self.as_timespan(), other)

    def as_timespan(self):
        details = self.details
        if details.has_key("start") and details.has_key("end"):
            return Timespan(details["start"], details["end"])
        else:
            return None

    def as_limits(self):
        ts = self.as_timespan()
        return ts and ts.as_limits()

class CalendarEvent(Event):

    "An event from a remote calendar."

    def getEventURL(self):

        """
        Return the URL of this event, fixing any misinterpreted or incorrectly
        formatted value in the event definition or returning the resource URL in
        the absence of any URL in the event details.
        """

        return self.details.get("url") and \
            self.valueToString(self.details["url"]) or \
            self.page.getPageURL()

    def getSummary(self, event_parent=None):

        """
        Return the event summary, fixing any misinterpreted or incorrectly
        formatted value in the event definition.
        """

        return self.valueToString(self.details["summary"])

    def valueToString(self, value):

        "Return the given 'value' converted to a string." 

        if isinstance(value, list):
            return ",".join(value)
        elif isinstance(value, tuple):
            return ";".join(value)
        else:
            return value

    def linkToEvent(self, request, text, query_string=None, anchor=None):

        """
        Using 'request', return a link to this event with the given link 'text'
        and optional 'query_string' and 'anchor'.
        """

        return linkToResource(self.getEventURL(), request, text, query_string, anchor)

    def getMetadata(self):

        """
        Return a dictionary containing items describing the event's "created"
        time, "last-modified" time, "sequence" (or revision number) and the
        "last-comment" made about the last edit.
        """

        metadata = self.page.getMetadata()

        return {
            "created" : self.details.get("created") or self.details.get("dtstamp") or metadata["created"],
            "last-modified" : self.details.get("last-modified") or self.details.get("dtstamp") or metadata["last-modified"],
            "sequence" : self.details.get("sequence") or 0,
            "last-comment" : ""
            }

# vim: tabstop=4 expandtab shiftwidth=4
