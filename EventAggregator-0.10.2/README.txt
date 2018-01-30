Introduction
------------

The EventAggregator macro for MoinMoin can be used to display event calendars
or listings which obtain their data from pages belonging to specific
categories (such as CategoryEvents) or from remote event sources. The start
and end dates are read from the page describing each event, and the calendar
is automatically filled out with the details of each event, colouring each
event period in a specially generated colour. Maps showing event locations are
also supported, given the availability of appropriate map images and location
information.

The EventAggregatorSummary action can be used to provide iCalendar and RSS
summaries of event data based on pages belonging to specific categories, as
described above. The category, start and end parameters are read directly from
the request as URL or form parameters: these restrict the extent of each
generated summary.

The EventAggregatorNewEvent action can be used to conveniently create new
event pages, displaying a simple form which can be filled out in order to
provide elementary event details such as the event title or summary, the
categories to which the page will be assigned, and the start and end dates of
the event.

The eventfeed script can be used to import events from RSS feeds, inserting
new pages into a Wiki.

Important Notices
-----------------

In release 0.10, the EventAggregatorSupport module has been converted into a
package. Upon upgrading, it may be necessary to locate the source and compiled
module files (EventAggregatorSupport.py and EventAggregatorSupport.pyc) and
remove them. Otherwise, these files may disrupt the functioning of the newly-
installed software.

In release 0.9, much of the common support code has been moved to the
MoinSupport distribution, thus introducing that distribution as a dependency
which must be installed for EventAggregator to work. See the documentation
regarding dependencies for further details.

Release 0.8.4 fixes time zone offset calculations for time regimes west of the
prime meridian.

Release 0.8.3 fixes end dates in events aggregated from remote iCalendar
sources.

Release 0.7.1 restores MoinMoin 1.9.x compatibility which was accidentally
lost in the 0.7 release.

Release 0.6.2 fixes various bugs in HTML production done by the actions. It is
strongly recommended to upgrade from earlier versions to this or a later
release.

In release 0.6.2, support for MoinMoin 1.5.x has been dropped. Since usage of
the Xapian search software is practically a necessary part of deploying this
solution, and yet Xapian only became integrated with MoinMoin from version 1.6
onwards, few deployments should have involved MoinMoin 1.5.x.

In release 0.6, support for event times has been introduced. Due to the
complicated nature of times, time zones, time regimes, and so on, the
behaviour of the software may change in future versions to support common
use-cases in a more convenient fashion. Please be aware that implicitly chosen
or generated time or time zone information may change for events, particularly
those whose times are ambiguous or ill-defined. It is highly recommended that
the pytz library be installed - see the documentation regarding dependencies
for more information.

In release 0.5, the "download this calendar" and "subscribe to this calendar"
links have been fixed to return only events within the specified period and to
work with day- and month-relative calendars. Users who have bookmarks in their
Web browser or feed reader should replace these bookmarks by visiting the
bookmarked page and acquiring new versions of these links, once
EventAggregator has been upgraded.

Installation
------------

To install the support library and MoinMoin-related scripts, consider using
the moinsetup tool. See the "Recommended Software" section below for more
information.

With moinsetup and a suitable configuration file, the installation is done as
follows with $EADIR referring to the EventAggregator distribution directory
containing this README.txt file:

  python moinsetup.py -f moinsetup.cfg -m install_extension_package $EADIR
  python moinsetup.py -f moinsetup.cfg -m install_actions $EADIR/actions
  python moinsetup.py -f moinsetup.cfg -m install_macros $EADIR/macros
  python moinsetup.py -f moinsetup.cfg -m install_parsers $EADIR/parsers
  python moinsetup.py -f moinsetup.cfg -m install_theme_resources $EADIR
  python moinsetup.py -f moinsetup.cfg -m edit_theme_stylesheet screen.css event-aggregator.css
  python moinsetup.py -f moinsetup.cfg -m edit_theme_stylesheet print.css event-aggregator.css
  python moinsetup.py -f moinsetup.cfg -m edit_theme_stylesheet print.css event-aggregator-print.css

The first command above uses the setup.py script provided as follows:

  python setup.py install --prefix=path-to-moin-prefix

The second, third and fourth commands install the actions, macros and parsers
respectively.

The fifth command installs the theme resources in the available theme
directories.

The remaining commands activate the styles provided by EventAggregator by
editing the screen.css and print.css files which are typically provided by
themes. These commands add imports of the following form to the theme
stylesheets:

  @import "event-aggregator.css";

Additional Installation Tasks
-----------------------------

See the "Dependencies" section below for details of the software featured in
this section.

EventAggregator depends on MoinSupport having been installed. This is because
a lot of useful functionality common to a number of MoinMoin extensions now
resides in the MoinSupport distribution.

The following command can be run with $MSDIR referring to the MoinSupport
distribution directory:

  python moinsetup.py -f moinsetup.cfg -m install_extension_package $MSDIR

To support iCalendar summary production for calendars as well as the
capability of aggregating iCalendar format event sources, the vContent
software needs to be obtained and installed.

The following command can be run with $VCDIR referring to the vContent
distribution directory:

  python moinsetup.py -f moinsetup.cfg -m install_extension_package $VCDIR

In each case, the install_extension_package method merely runs the setup.py
script provided by the software concerned, installing the software under the
configured installation "prefix".

Useful Pages
------------

The pages directory contains a selection of useful pages using a syntax
appropriate for use with MoinMoin 1.6 or later. These pages can be created
through the Wiki and their contents copied in from each of the files. An
easier installation method is to issue the following commands:

  python moinsetup.py -f moinsetup.cfg -m make_page_package $EADIR/pages pages.zip
  python moinsetup.py -f moinsetup.cfg -m install_page_package pages.zip

You may need to switch user in order to have sufficient privileges to copy the
page package into the Wiki. For example:

  sudo -u www-data python moinsetup.py -f moinsetup.cfg -m install_page_package pages.zip

Resource Pages
--------------

For the map view, some resource pages are provided with EventAggregator.
Unlike the help pages which are most likely to be left unedited, the resource
pages should be modified and updated with additional map and place details.
Consequently, upgrading these pages is not necessarily desirable when new
releases of EventAggregator are made available, and thus these pages are kept
separate from the help pages.

To install the resource pages, use the following commands:

  python moinsetup.py -f moinsetup.cfg -m make_page_package $EADIR/resource_pages resource_pages.zip
  python moinsetup.py -f moinsetup.cfg -m install_page_package resource_pages.zip

You may need to switch user in order to have sufficient privileges to copy the
page package into the Wiki. For example:

  sudo -u www-data python moinsetup.py -f moinsetup.cfg -m install_page_package resource_pages.zip

Using the Macro
---------------

It should now be possible to edit pages and use the macro as follows:

  <<EventAggregator(CategoryEvents)>>

As arguments to the macro, you must indicate a comma-separated list of
categories to be inspected for event data. For example:

  <<EventAggregator(CategoryEvents,CategoryTraining)>>

By default, this should display a calendar in a collection of tables, one for
each month containing events. To show a collection of month-by-month listings,
use the 'mode' argument as follows:

  <<EventAggregator(CategoryEvents,mode=list)>>

To use remote event sources instead of categories in the Wiki, specify each
source using explicit source parameters:

  <<EventAggregator(source=GriCal,source=FSFE)>>

This will aggregate events from the GriCal and FSFE calendars residing on
remote Web sites, provided that these sources have been defined in the event
sources dictionary.

To use a search pattern, use the search parameter and specify the search
criteria just as you would when using the standard search macros:

  <<EventAggregator(search="title:MonthCalendarEvents/")>>

This will aggregate events found on subpages of the MonthCalendarEvents page.

See pages/HelpOnEventAggregator for more detailed information.

Using the Actions
-----------------

To obtain an iCalendar summary, the EventAggregatorSummary action can be
selected from the actions menu on any page. Alternatively, a collection of
parameters can be specified in the URL of any Wiki page.

See pages/HelpOnEventAggregatorSummary for more detailed information.

To create new events using the EventAggregatorNewEvent action, the appropriate
menu entry can be selected in the actions menu. Alternatively, clicking on a
day number in a calendar view will invoke the action and pre-fill the form
with the start date set to the selected day from the calendar.

See pages/HelpOnEventAggregatorNewEvent for more detailed information.

Running the Scripts
-------------------

Note that remote event sources are likely to be more useful than the scripts
described below. However, these scripts may be useful for certain kinds of
application.

To import events from an RSS feed, the eventfeed script integrated with the
moin program can be used as follows:

moin --config-dir=path-to-wiki --wiki-url=example.com/ \
    import eventfeed --url=url-of-events-feed

Thus, to import events from the FSFE events RSS feed, the following command
could be used:

moin --config-dir=path-to-wiki --wiki-url=example.com/ \
    import eventfeed --url=http://www.fsfe.org/events/events.en.rss

If this command is being used with sudo, make sure to use the -u option so
that the script can operate as the appropriate user. For example:

sudo -u www-data moin --config-dir=path-to-wiki --wiki-url=example.com/ \
    import eventfeed --url=http://www.fsfe.org/events/events.en.rss

It may also be necessary to set PYTHONPATH directly before the moin program
name and even to explicitly use the path to that program.

Recommended Software
--------------------

See the "Dependencies" section below for essential software.

The moinsetup tool is recommended for installation since it aims to support
all versions of MoinMoin that are supported for use with this software.

See the following page for information on moinsetup:

http://moinmo.in/ScriptMarket/moinsetup

The Xapian search software is highly recommended, if not technically
essential, for the acceptable performance of the EventAggregator macro since
the macro makes use of search routines in MoinMoin that can dominate the time
spent processing requests.

See the following page for information on Xapian and MoinMoin:

http://moinmo.in/HelpOnXapian

Troubleshooting: Categories
---------------------------

See here for a bug related to category recognition:

http://moinmo.in/MoinMoinBugs/1.7TemplatesNotAppearing

This affects installations where migrations between versions have occurred,
yet the Wiki configuration retains old regular expression details.

Troubleshooting: Xapian
-----------------------

Xapian can be troublesome, especially where file permissions are concerned: if
something acquires a lock on the index (for example, the moin script, possibly
invoked via moinsetup) nothing else will be able to modify the index, and this
may cause pages to become detached from their categories in the index.

To resolve index issues, try and run the following command (with the appropriate
options):

moin --config-dir=path-to-wiki --wiki-url=example.com/ index build --mode=rebuild

It may be necessary to manually remove locks. This can be done as follows:

find path-to-wiki/data/cache/xapian -depth -name "*lock" -type d -exec rmdir '{}' \;

Troubleshooting: Plain Text Formatting
--------------------------------------

Plain text formatting is used in certain places in EventAggregator, but the
formatter is rather broken in MoinMoin 1.8 and in previous releases. See the
following page for a summary:

http://moinmo.in/FeatureRequests/TextPlainFormatterRewrite

A patch is supplied in the patches directory to fix link formatting in the
plain text formatter, and once copied into the root directory of the MoinMoin
1.8 sources it can be applied as follows:

patch -p1 < patch-plain-text-link-formatting-1.8.diff

Contact, Copyright and Licence Information
------------------------------------------

See the following Web pages for more information about this work:

http://moinmo.in/MacroMarket/EventAggregator
http://moinmo.in/ActionMarket/EventAggregator

The author can be contacted at the following e-mail address:

paul@boddie.org.uk

Copyright and licence information can be found in the docs directory - see
docs/COPYING.txt and docs/LICENCE.txt for more information.

Dependencies
------------

EventAggregator has the following basic dependencies:

Packages                    Release Information
--------                    -------------------

MoinSupport                 Tested with 0.4.1
                            Source: http://hgweb.boddie.org.uk/MoinSupport

vContent                    Tested with 0.2.1
                            Source: http://hgweb.boddie.org.uk/vContent

pytz                        Tested with 2007k (specifically 2007k-0ubuntu2)
                            Source: http://pytz.sourceforge.net/

If time zone handling is not required, pytz need not be installed, but this
may result in iCalendar summaries being produced that provide insufficient
time zone information for the correct interpretation of time information in
those summaries. Thus, it is highly recommended that pytz be installed.

New in EventAggregator 0.10.2 (Changes since EventAggregator 0.10.1)
--------------------------------------------------------------------

  * Fixed iCalendar event writing.
  * Added an iCalendar parser.
  * Accessibility improvements: introduced table captions for the display of
    table headings; added link titles; supported the opening of pop-up menus
    and map labels using links and link targets.
  * Fixed event parser formatting of wiki text from page-based events.
  * Removed the "pages" dependency from the macro, suggested by Marcel Häfner,
    permitting cached page content to be used where appropriate.

New in EventAggregator 0.10.1 (Changes since EventAggregator 0.10)
------------------------------------------------------------------

  * Properly removed the EventAggregatorSupport.py file from the project.
  * Fixed event region formatting when an alternative write function is
    provided.

New in EventAggregator 0.10 (Changes since EventAggregator 0.9)
---------------------------------------------------------------

  * Fixed quoting of special date parameters in navigation URLs and download
    dialogue URLs.
  * Fixed the resolution of whole calendar download/subscription links in day
    views.
  * Added support for showing events that occupy instants in time in day
    views, consolidating times in the timescale used for each day and showing
    the times specified for the events concerned for each common point in
    time.
  * Adjusted labels of navigation links to indicate multiple days where a day
    view shows many days.
  * Changed iCalendar serialisation to use the vContent library, making
    vContent a requirement of this software.
  * Refactored the library, replacing the support module with a package
    containing separate modules for the different library activities.

New in EventAggregator 0.9 (Changes since EventAggregator 0.8.5)
----------------------------------------------------------------

  * Moved much of the support library to the MoinSupport distribution, thus
    introducing a dependency on that software.
  * Added support for in-page updates of the event views so that navigation
    between days, months and different views does not cause a full-page
    reload if JavaScript is enabled.
  * Tidied up the new event form, showing a list of known locations for
    selection, making the event location affect the chosen time zone/regime if
    the location is known, and hiding latitude and longitude fields unless an
    unknown location is to be specified.
  * The EventLocationsDict or equivalent can now retain time zone/regime
    information about each location.
  * Added an event parser that can format special page regions in different
    ways and support links directly to such regions.
  * Permitted Wiki markup in the description and location metadata.
  * Added support for search patterns so that event pages can be obtained
    through arbitrary searches and do not have to belong to particular
    categories.
  * Encoded map location pop-up headings as plain text in order to handle
    locations specified using Wiki formatting.
  * Permitted events with map references but without location details to be
    positioned in maps.
  * Improved navigation between months and days, and between view modes for
    both levels of calendar view.

New in EventAggregator 0.8.5 (Changes since EventAggregator 0.8.4)
------------------------------------------------------------------

  * Fixed iCalendar quoting for newlines in calendar data.

New in EventAggregator 0.8.4 (Changes since EventAggregator 0.8.3)
------------------------------------------------------------------

  * The calculation of hour and minute offsets for time regimes west of the
    prime meridian was not producing correct results since the day offset
    provided by pytz was not being considered in the calculation. Such regimes
    should now produce the expected (hour, minute) offsets such that events
    employing these regimes can be positioned correctly on a UTC timescale.

New in EventAggregator 0.8.3 (Changes since EventAggregator 0.8.2)
------------------------------------------------------------------

  * The end dates defined in events from remote iCalendar event sources were
    not correctly adjusted when aggregating such events. Thus, events with a
    day-level resolution will have appeared one day longer in calendars and
    summaries than was actually specified in the source data. This adjustment
    has now been introduced.

New in EventAggregator 0.8.2 (Changes since EventAggregator 0.8.1)
------------------------------------------------------------------

  * Improved the error handling around remote event source data retrieval,
    introducing handling of missing resources and unsupported content types.
  * Improved the presentation of download and subscription links, adding
    webcal: URL links for suitable calendar clients.

New in EventAggregator 0.8.1 (Changes since EventAggregator 0.8)
----------------------------------------------------------------

  * Changed the EventAggregatorNewEvent action to not save new event pages
    directly, instead invoking the textual page editor for the page so that
    the page text can be changed and the page saved without a redundant
    initial version being created. Cancelling the editing operation will also
    avoid the creation of unwanted event pages.
  * Added a page break before each map in the print view, adding a page break
    after each map to fully isolate unpositioned events on separate pages.
  * Fixed errors where empty location fields were given in vCalendar events.
  * Reintroduced event sorting in the list and table views.
  * Fixed location positioning where some events employing an unknown location
    do not position that location whereas others do (using "geo" information).

New in EventAggregator 0.8 (Changes since EventAggregator 0.7.1)
----------------------------------------------------------------

  * Added remote event aggregation with support for iCalendar event sources.
  * Added support for explicit latitude and longitude event properties.
  * Added support for decimal latitude and longitude values.
  * Introduced in-page updates of the new event form, avoiding full-page
    reloads when editing the initial details of an event.

New in EventAggregator 0.7.1 (Changes since EventAggregator 0.7)
----------------------------------------------------------------

  * Restored MoinMoin 1.9.x compatibility around WikiDict access.

New in EventAggregator 0.7 (Changes since EventAggregator 0.6.4)
----------------------------------------------------------------

  * Added a day view which shows events ordered according to their timespans
    within each day.
  * Added a map view which shows events according to their location. This
    requires map images to be uploaded to a designated page, and map locations
    to be defined on a designated page.
  * Switched to using moinsetup for the installation procedure.
  * Introduced formatting of description, location and topic information in
    the list and table views and in RSS format summaries.
  * Introduced support for days as calendar period units in the list view.
  * Added "Help" and "New event" links alongside the calendar view controls,
    giving the download and view controls centre alignment.

New in EventAggregator 0.6.4 (Changes since EventAggregator 0.6.3)
------------------------------------------------------------------

  * Fixed pop-up element labels where one limit of a calendar has not been
    specified.

New in EventAggregator 0.6.3 (Changes since EventAggregator 0.6.2)
------------------------------------------------------------------

  * Fixed category membership parsing.
  * Fixed open-ended calendars and their pop-up summaries.

New in EventAggregator 0.6.2 (Changes since EventAggregator 0.6.1)
------------------------------------------------------------------

  * Fixed HTML encoding in the forms generated by the actions.
  * Dropped MoinMoin 1.5.x support, since Xapian search is not available for
    that version and is virtually a necessity.
  * Fixed form handling to be compatible with MoinMoin 1.9.x, since that
    particular release series introduced an incompatible request API that
    breaks existing code (no longer providing access to query string
    parameters via the form attribute, and only returning single values
    unless the new getlist method on form-like objects is used).
  * Fixed the direct writing of requests to be compatible with MoinMoin 1.9.
  * Added pop-up elements showing information about the calendar/view
    resources available for download or subscription.
  * Added download/subscription links which open the form associated with the
    EventAggregatorSummary action and permit editing of the supplied values.

New in EventAggregator 0.6.1 (Changes since EventAggregator 0.6)
----------------------------------------------------------------

  * Fixed HTML encoding in the forms generated by the actions.

New in EventAggregator 0.6 (Changes since EventAggregator 0.5)
--------------------------------------------------------------

  * Added print stylesheet rules in order to improve the printed versions of
    calendars.
  * Fixed definition list parsing to handle completely empty definitions
    (having no space after the "::" token) which previously captured text from
    subsequent lines, and merely empty definitions which previously would have
    produced a single empty value for definitions providing lists of values.
  * Added a script to import events from RSS feeds.
  * Added support for a link entry in event pages, although this does not
    replace the link information provided by the RSS and iCalendar summaries.
  * Fixed the production of the summaries when pages with no available edit
    log information are to be included.
  * Added support for event times and time zone/regime information. This is
    subject to revision.

New in EventAggregator 0.5 (Changes since EventAggregator 0.4)
--------------------------------------------------------------

  * Changed the EventAggregatorNewEvent action to substitute only the stated
    title, not the full page title, into the new page.
  * Changed event colouring to use the event summary as the basis for
    calculating the colour used in the calendar. This means that related
    events can be coloured identically if their summaries are the same.
  * Added support for multiple events on a single event page.
  * Introduced EventPage and Event abstractions in order to better support new
    features.
  * Introduced basic and advanced modes to the EventAggregatorNewEvent action,
    along with date swapping to correct cases where the start is given as
    being later than the end of an event.
  * Fixed the "download this calendar" and "subscribe to this calendar" links
    by propagating the "raw" calendar start and end values within the macro.
    These links should yield events only within the period defined for a
    calendar, not all events in a calendar's categories. This fix also ensures
    that the links for year- and month-relative calendars are correct, rather
    than the specific links generated previously. Thus, a "this year's events"
    link will now continue to produce a resource with the current year's
    events, rather than the events from the year when the link was generated.

New in EventAggregator 0.4 (Changes since EventAggregator 0.3)
--------------------------------------------------------------

  * Added a table view in the macro, using special topic/category styles to
    provide background colours for events.
  * Added category propagation from calendars to the new event form provided
    by the EventAggregatorNewEvent action.
  * Added a default template parameter to the macro, employed by the new event
    form.
  * Added a parent page parameter which is used by the new event form to place
    new event pages in a particular location specific to a calendar or
    collection of events.
  * Improved the presentation of pop-up event information elements.
  * Added navigation between display modes (calendar, list and table views).
  * Ensured that calendar settings are retained when creating new events for a
    calendar.
  * Fixed various problems with events not having topics.

New in EventAggregator 0.3 (Changes since EventAggregator 0.2)
--------------------------------------------------------------

  * Added a parameter to the EventAggregatorSummary action to select the
    source of event descriptions for the RSS feed.
  * Updated the documentation to cover the RSS support.
  * Added the EventAggregatorNewEvent action.

New in EventAggregator 0.2 (Changes since EventAggregator 0.1)
--------------------------------------------------------------

  * Improved the calendar view in the macro to use the fixed table layout
    algorithm and to provide cells spanning potentially many columns for
    continuing events. Introduced pop-up elements in order to show truncated
    event names.
  * Made the "weekly" naming policy the default in the calendar view.
  * Improved the list view in the macro.
  * Introduced RSS 2.0 feed support.
  * Improved the help pages. 

Release Procedures
------------------

Update the EventAggregatorSupport __version__ attribute and the setup.py
version details.
Change the version number and package filename/directory in the documentation.
Update the setup.py and PKG-INFO files.
Update the release notes (see above).
Tag, export.
Archive, upload.
Update the MacroMarket and ActionMarket (see above for the URLs).
