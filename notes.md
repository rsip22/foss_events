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

#### From EventAggregator:

if format == "iCalendar":

    headers = ["Content-Type: text/calendar; charset=%s" % config.charset]

// iCalendar output...

if format == "iCalendar":

    mimetype = "text/calendar"

TODO:
* <del>Figure out how to link calaction=ical on the bottom menu bar. [http://localhost/MyStartingPage?calaction=ical](http://localhost/MyStartingPage?calaction=ical) works.</del> IT WORKS!
* Install the EventAggregator macro and make it work.
    - For that, install moinsetup and proceed with the instalation as described on EventAggregator README
* <del>Figure out how to allow the download to happen. (Check other macros' code, specially EventAggregator) => The 'download' or opening the ical file on the proper software *should happen* when the proper headers are set. But now I have to figure out how to do this, because EventCalendar doesn't seem to do that (set the headers) at any point. Does Moin Wiki? There should be a new global variable? A new function that returns the headers?/<del> DONE! This helped: https://moinmo.in/MoinMoinBugs/EditorContentTypeHttpHeader
* Install icalendar system-wide to import it to the EventCalendar module.
* Parse the events data to set the output to proper icalendar format.
