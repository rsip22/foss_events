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

### More on actions

From my blog: "So maybe I will have to work a bit on this afterwards, to interact with the macro and customize the information to be displayed? I am not sure, I will have to look more into this."

* [Analyzing actions](https://moinmo.in/ActionsAsViewsOperationsAndExports)

> The action is what the MoinMoin code does with the client request (and the requested page).  Often, you write an action to extend MoinMoin to perform perform processing on a page (a page is given as the argument to the action), but any processing is allowed.
>
> "Actions either produce some output based on page contents (navigational actions like searching) or implement functions that are not related to viewing a page (like deleting or renaming a page).
>
>Actions are tools that work on a page or the whole wiki, but unlike macros they do not add to the page content when viewing a page, rather they work on that page content."

#### **Creating an action**
- New class with the name of the action
Note: the action name is the class name

> The request object is central and conects all the classes
> A page is requested by an Action request. Then goes through Page and then Theme adds additional content before finaly an HTML page is sent to your browser.

**print(help(request))**

**Help on AllContext in module MoinMoin.web.contexts object:**

class AllContext(HTTPContext, AuxilaryMixin)
|  Methods inherited from HTTPContext:
|  redirect(self, file=None)
|      Redirect output to file, or restore saved output
|  
|  redirectedOutput(self, function, *args, **kw)
|      Redirect output during function, return redirected output
|  
|  send_file(self, fileobj, bufsize=8192, do_flush=None)
|      Send a file to the output stream.

become(self, cls)
 |      Become another context, based on given class.
 |      
 |      @param cls: class to change to, must be a sister class
 |      @rtype: boolean
 |      @return: wether a class change took place

 dir request:
_
__class__
__delattr__
__dict__
__doc__
__format__
__getattr__
__getattribute__
__hash__
__init__
__module__
__new__
__reduce__
__reduce_ex__
__repr__
__setattr__
__sizeof__
__str__
__subclasshook__
__weakref__
_auth_redirected
_fmt_hd_counters
_login_messages
_login_multistage
_login_multistage_name
_setuid_real_user
_theme
action
become
cacheable
cfg
clock
content_lang
content_type
current_lang
dicts
disableHttpCaching
environ
finish
formatter
getBaseURL
getPragma
getQualifiedURL
getScriptname
getText
groups
html_formatter
http_redirect
http_referer
http_user_agent
initTheme
isSpiderAgent
lang
makeForbidden
mimetype
mode_getpagelinks
page
pages
parsePageLinks_running
personalities
pragma
read
redirect
redirectedOutput
request
reset
rev
rootpage
send_file
session
setContentLanguage
setHttpHeader
setPragma
status
status_code
theme
uid_generator
user
write
writestack

### TODO:
* <del>Figure out how to link calaction=ical on the bottom menu bar. [http://localhost/MyStartingPage?calaction=ical](http://localhost/MyStartingPage?calaction=ical) works.</del> IT WORKS!
* Install the EventAggregator macro and make it work.
    - For that, install moinsetup and proceed with the instalation as described on EventAggregator README
* <del>Figure out how to allow the download to happen. (Check other macros' code, specially EventAggregator) => The 'download' or opening the ical file on the proper software *should happen* when the proper headers are set. But now I have to figure out how to do this, because EventCalendar doesn't seem to do that (set the headers) at any point. Does Moin Wiki? There should be a new global variable? A new function that returns the headers?</del> DONE! This helped: https://moinmo.in/MoinMoinBugs/EditorContentTypeHttpHeader
* <del>Install icalendar system-wide to import it to the EventCalendar module.</del> Done.
* <del>Parse the events data to set the output to proper icalendar format.</del> This is sort of done, but I still have to work on the event dates.
* <del>How to return the .ics file and not the whole wiki page when cal_action is called. => This I am stuck with, I am thinking that maybe the only way to make this work is to turn the function into a new macro itself. But how to keep that from happening if the data for this new macro will be derivated from EventCalendar?</del> A new action must be created.
* 'How to create a moin action' -> create and document
    - Accessing the action
* <del>From the macro, call the action.</del> -> DONE
* Write a fuction that can be access both by the macro and the action. But... how? What about the formatter? -> The issue with the formatter is sort of resolved.
