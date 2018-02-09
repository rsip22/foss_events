### Some notes to help me with development

Event data from **cal_listhead()**:

* Title
* Start Date
* End Date
* Recurrence
* Label
* Description
* Reference

Info for one event, from **listshow_event(event)**:

* % converttext(event['title'])
* % formatcfgdatetime(event['startdate'], event['starttime'])
* % formatcfgdatetime(event['enddate'], event['endtime'])
* % recur_desc
* % showReferPageParsedForLabel(event['label'])
* % converttext(event['description'])
* % showReferPageParsed(event, 'refer')

From **showReferPageParsed**:
refer = event['refer']
targettext = event[targettext]
startdate = event['startdate']
enddate = event['enddate']
description = event['description']
starttime = event['starttime']
endtime = event['endtime']
hid = event['hid']

#### From EventAggregator:

if format == "iCalendar":

    headers = ["Content-Type: text/calendar; charset=%s" % config.charset]

// iCalendar output...

if format == "iCalendar":

    mimetype = "text/calendar"

### MoinMoin and MIMETYPES

To define supported mimetypes, moin/MoinMoin/wikiutil.py uses the Python [mimetype](https://docs.python.org/2/library/mimetypes.html) module, but for some reason wikiutil.py doesn't explicitly support .ics. I wondered if it was because Python 2 didn't have support for that, but it looks like it does:

```
renata@debian:~$ python
Python 2.7.13 (default, Nov 24 2017, 17:33:09)
[GCC 6.3.0 20170516] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import mimetypes
>>> mimetypes.init()
>>> mimetypes.types_map['.ics']
'text/calendar'
```
So wouldn't it be the ideal, if MoinMoin itself supported .ics? Or maybe it does natively, no need to express it on wikiutil.py?

### TYPES:
Calling function loadEvents() unpacks to dictionary variables (events, cal_events, labels) with info about events. Because of this, they can be interacted with events.values().

Each *events* item is an unicode object (e_Workshops_1, e_Conferences_1, e_Conferences_2...).

### VEVENT
canonical_order = ('SUMMARY', 'DTSTART', 'DTEND', 'DURATION', 'DTSTAMP', 'UID', 'RECURRENCE-ID', 'SEQUENCE', 'RRULE', 'RDATE', 'EXDATE')
required = ('UID', 'DTSTAMP')
singletons = ('CLASS', 'CREATED', 'DESCRIPTION', 'DTSTART', 'GEO', 'LAST-MODIFIED', 'LOCATION', 'ORGANIZER', 'PRIORITY', 'DTSTAMP', 'SEQUENCE', 'STATUS', 'SUMMARY', 'TRANSP', 'URL', 'RECURRENCE-ID', 'DTEND', 'DURATION', 'UID')

### Make dtstart
To add the DTSTART component, I had to create a new function to return proper dtstart data.

item['startdate'] and item['starttime'] had be combined and converted to time and date format. If there is no starttime specified, it shouldn't throw an error - it probably should assume that the event will be all day long (in the timezone of the calendar? Not the ideal, but events in EventCalendar don't usually get location data...).

item['startdate'] and item['starttime'] are unicode objects, so they must be converted to the proper time and date format. Because this is a very commom operation, there are tools that have already been developed to help with this taks. In this case, the [dateutil module](https://dateutil.readthedocs.io/en/stable/) provides to the standard datetime Python module, allowing this operation to be performed.


### cal_action
Actions can send almost anything you like intead of a page.
EventAggregator sets the content type and sends a different kind of resource.
action=EventAggregatorSummary&...
... => action providing in the iCalendar download. The browser will make a new request when the user follows the link and all the relevant information will need to be supplied again. 

### TODO:
* <del>Figure out how to link calaction=ical on the bottom menu bar. [http://localhost/MyStartingPage?calaction=ical](http://localhost/MyStartingPage?calaction=ical) works.</del> IT WORKS!
* Install the EventAggregator macro and make it work.
    - For that, install moinsetup and proceed with the instalation as described on EventAggregator README
* <del>Figure out how to allow the download to happen. (Check other macros' code, specially EventAggregator) => The 'download' or opening the ical file on the proper software *should happen* when the proper headers are set. But now I have to figure out how to do this, because EventCalendar doesn't seem to do that (set the headers) at any point. Does Moin Wiki? There should be a new global variable? A new function that returns the headers?</del> DONE! This helped: https://moinmo.in/MoinMoinBugs/EditorContentTypeHttpHeader
* <del>Install icalendar system-wide to import it to the EventCalendar module.</del> Done.
* <del>Parse the events data to set the output to proper icalendar format.</del> This is sort of done, but I still have to work on the event dates.
* How to return the .ics file and not the whole wiki page when cal_action is called. => This I am stuck with, I am thinking that maybe the only way to make this work is to turn the function into a new macro itself. But how to keep that from happening if the data for this new macro will be derivated from EventCalendar?
