"""
    EventCalendar.py  Version 0.99  May 22, 2006

    This macro gives a list of the events recorded at the sub-pages in the form of various views:
        monthly, weekly, daily, simple-month, list, and upcoming.

    @copyright: 2006 by Seungik Lee <seungiklee<at>gmail.com>  http://www.silee.net/
    @license: GPL

    For more information, please visit http://moinmoin.wikiwikiweb.de/MacroMarket/EventCalendar

    <Usage>

        * To list the events in a page, just insert <<EventCalendar>>
        * To insert an event, insert the event information in any pages of specified category (CategoryEventCalendar by default).

    <Parameters>

        * category: the category of the event data to be used in the calendar. default: 'CategoryEventCalendar'
        * menubar: shows menubar or not (1: show, 0: no menubar). default: 1
        * monthlywidth: calendar width in pixel or percent (monthly view). default: '600' (pixel)
        * simplewidth: calendar width in pixel or percent (simpleview). default: '150' (pixel)
        * firstview: initial calendar view: monthly, weekly, daily, list, simple, upcoming. default: 'monthly'
        * curdate: initial calendar date (in YYYYMM format). default: current month
        * upcomingrange: # of days for the range of upcoming event list. default: 7 (days)
        * changeview: enables to change the calendar view or not (1: enalbed, 0: disabled). default: 1
        * numcal: # of calendar. default: 1
        * showlastweekday: shows the event at the last weekday if the recurred weekday is not available. (1: enalbed, 0: disabled). default: 0
        * showerror: shows error messages below the calendar if event data format is invalid. (1: enalbed, 0: disabled). default: 1
        * showweeknumber: shows the week number of the year (1: enalbed, 0: disabled). default: 0


    <Event Data Format>

        * Event data fields:
...

 [default_description:: [page_default_description_text]]
 [default_bgcolor:: [page_default_background_color]]
 [label_def:: [label_name], [label_background_color]]

== <title> ==
 start:: <startdate> [starttime]
 [end:: [enddate] [endtime]]
 [description:: [description_text]]
 [bgcolor:: [custom_background_color]]
 [recur:: <recur_freq> <recur_type> [until <recur_until>]]
 [label:: <label_name>]

...

----
CategoryEventCalendar

            * default_bgcolor, default_description: default values of bgcolor and description in the page if unavailable. optional
            * label_def: label definition with name, bgcolor. optional

            * title: event title. required
                * should be enclosed with heading marker ('='), Title cannot be omitted.

            * startdate: date of start. required
                * should be in date format or date format

            * starttime: time of start. optional
                * should be in time format

            * enddate: date of end. optional
                * should be in date format or date format. If omitted, it will be assigned equal to <startdate>.

            * endtime: time of end. optional
                * should be in time format. Both of start|end Time can be omitted but not either of them.

            * description: description of the event. optional
                * any text with no markup. should be in a line.

            * bgcolor: custom background color of the event in monthly view. optional
                * e.g., #abcdef

            * recur: recurrence information of the event. optional
                * recur_freq: how many intervals, digit or 'last' for weekday, required
                * recur_type: [day|week|weekday|month|year], required
                    * day: every [recur_freq] days
                    * week: every [recur_freq] weeks
                    * weekday: on the same weekday of [recur_freq]-th week of the month. or 'last weekday'
                    * month: on the same day of [recur_freq]-th month
                    * year: on the same day of [recur_freq]-th year
                * recur_until: recurred until when, date format, optional

                * e.g., 10 day, 2 week until 2006-06-31, 3 weekday, 6 month until 2007-12-31, 1 year

            * label: custom label for specific name, bgcolor. optional

            * The order of the fields after an event title does not matter.
            * Priority of bgcolor: bgcolor > default_bgcolor > label_bgcolor


        * Datetime format:

            * Date format:
                * YYYY/MM/DD, YYYY-MM-DD, YYYY.MM.DD: 2006/05/12; 2006-05-12; 2006.05.12; 2006-5-12; 06/5/12
                * B DD, YYYY: May 12, 2006; May 5th, 2006; January 1st, 2006; Jan 5, 06
                * YYYYMMDD, YYMMDD: 20060512; 060512

                * Year: YY = 20YY. e.g., 06-2-2 = 2006-02-02, allowed 1900 ~ 2099 only.

            * Time format:
                * H:M, HHMM: 12:00; 22:00; 2:00; 2 (= 2 o'clock); 2200; 12:0; 2:0
                * I:M PP, IIMM PP: 12:00 PM; 3:00p; 2a (= 2 o'clock AM); 3:0pm; 0200 am; 10pm



    <Event Data Examples>

== Default values ==
 default_bgcolor:: #c0c0c0
 default_description:: testing...

== Labels ==
 label_def:: Holiday, #ff0000
 label_def:: Meeting, #00ff00

=== Test event ===
 start:: 2006-01-10 02:00p
 end:: 2006-01-12 17:00
 description:: test event
 bgcolor:: #cfcfcf

=== Jinah's Birthday ===
 start:: 1977-10-20
 recur:: 1 year
 label:: Holiday

=== Weekly meeting ===
 start:: Jan 17, 2006 7:00pm
 end:: 21:00
 recur:: 1 week until 061231
 label:: Meeting

----
CategoryEventCalendar


    <Notes>

        * It caches all the page list of the specified category and the event information.
        * If you added/removed a page into/from a category, you need to do 'Delete cache' in the macro page.

        * 'MonthCalendar.py' developed by Thomas Waldmann <ThomasWaldmann@gmx.de> has inspired this macro.
        * Much buggy.. : please report bugs and suggest your ideas.
        * If you missed to add css for EventCalender, monthly view may not be readable.
            * Insert the EventCalendar css classes into the screen.css of an appropriate theme.

"""
from MoinMoin import wikiutil, config, search, caching
from MoinMoin.Page import Page
from MoinMoin.action import Download_ical
from MoinMoin.action import AttachFile
from dateutil import parser
from datetime import datetime
import pytz
import icalendar
import re, calendar, time, datetime
import tempfile
import codecs, os, urllib, sha
import json
from MoinMoin import log
logging = log.getLogger(__name__)

try:
    import cPickle as pickle
except ImportError:
    import pickle

# Set pickle protocol, see http://docs.python.org/lib/node64.html
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL


# The following line sets the calendar to have either Sunday or Monday as
# the first day of the week. Only SUNDAY or MONDAY (case sensitive) are
# valid here.  All other values will not make good calendars.
# XXX change here ----------------vvvvvv
calendar.setfirstweekday(calendar.SUNDAY)


class Globs:
    month_style_us = 1  # 1: October 2005; 2: 2005 / 10
    defaultcategory = 'CategoryEventCalendar'
    upcomingrange = 40   # days
    dailystart = 9
    dailyend = 18
    pagename = ''
    baseurl = ''
    subname = ''
    wkend = ''
    months = ''
    wkdays = ''
    today = ''
    now = ''
    request = None
    formatter = None
    cal_action = ''
    debugmsg = ''
    errormsg = ''
    page_action = ''
    form_vals = {}
    events = None
    labels = None


class Params:
    menubar = 0
    monthlywidth = ''
    weeklywidth = ''
    dailywidth = ''
    simplewidth = ''
    firstview = ''
    curdate = ''
    bgcolor = ''
    category = ''
    upcomingrange = 0
    changeview = 0
    numcal = 1
    showlastweekday = 0
    showerror = 1
    showweeknumber = 0
    debug = 0


class EventcalError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def execute(macro, args):

    request = macro.request
    formatter = macro.formatter

    # INITIALIZATION ----------------------------------------
    setglobalvalues(macro)
    getparams(args)

    # allowed actions
    allowed_action = ['monthly',
                      'list',
                      'simple',
                      'upcoming',
                      'daily',
                      'weekly',
                      'ical']
    default_action = Params.firstview

    # Internal variables
    cal_action = ''
    form_vals = {}

    # PROCESSING ARGUEMENTS ----------------------------------------
    if args:
        args=request.getText(args)

    for item in macro.request.values.items():
         if not form_vals.has_key(item[0]):
            try:
                   form_vals[item[0]]=item[1]
            except AttributeError:
                pass

    # PROCESSING ACTIONS ----------------------------------------
    cal_action = form_vals.get('calaction', default_action)
    page_action = form_vals.get('action', 'show')

    if not cal_action in allowed_action:
        cal_action = default_action

    form_vals['calaction'] = cal_action

    Globs.form_vals = form_vals

    # CONTROL FUNCTIONS ----------------------------------------

    html = []
    html_result = ''

    Globs.cal_action = cal_action
    Globs.page_action = page_action


    # redirect to the appropriate view
    if cal_action == 'monthly':
        html_result = showcalendar()

    if cal_action == 'list':
        html_result = showeventlist()

    if cal_action == 'simple':
        html_result = showsimplecalendar()

    if cal_action == 'upcoming':
        html_result = showupcomingeventlist()

    if cal_action == 'daily':
        html_result = showdailycalendar()

    if cal_action == 'weekly':
        html_result = showweeklycalendar()

    if cal_action == 'ical':
        download_events_ical()

    # format output
    html.append( html_result )
    html.append( showmenubar() )

    if Params.showerror and Globs.errormsg:
        html.append(u'<p><i><font size="2" color="#aa0000"><ol>%s</ol></font></i>' % Globs.errormsg)

    if Params.debug and Globs.debugmsg:
        html.append(u'<p><b>Debug messages:</b><font color="#000099"><ol>%s</ol></font>' % Globs.debugmsg)

    return formatter.rawHTML(u''.join(html))


def getparams(args):
    """ process arguments """

    params = {}
    if args:
        # Arguments are comma delimited key=value pairs
        sargs = args.split(',')

        for item in sargs:
            sitem = item.split('=')

            if len(sitem) == 2:
                key, value = sitem[0], sitem[1]
                params[key.strip()] = value.strip()

    # category name:
    # default: 'CategoryEventCalendar'
    Params.category = params.get('category', Globs.defaultcategory)

    # menu bar: shows menubar or not (1: show, 0: no menubar)
    # default: 1
    try:
        Params.menubar = int(params.get('menubar', 1))
    except (TypeError, ValueError):
        Params.menubar = 1

    # calendar width in pixel or percent (monthly)
    # default: 600px
    Params.monthlywidth = params.get('monthlywidth', '600')
    if Params.monthlywidth:
        Params.monthlywidth = ' width="%s" ' % Params.monthlywidth

    # calendar width in pixel or percent (weekly)
    # default: 600px
    Params.weeklywidth = params.get('weeklywidth', '600')
    if Params.weeklywidth:
        Params.weeklywidth = ' width="%s" ' % Params.weeklywidth

    # calendar width in pixel or percent (daily)
    # default: 600px
    Params.dailywidth = params.get('dailywidth', '600')
    if Params.monthlywidth:
        Params.dailywidth = ' width="%s" ' % Params.dailywidth

    # calendar width in pixel or percent (simply)
    # default: 150px
    Params.simplewidth = params.get('simplewidth', '150')
    if Params.simplewidth:
        # Params.simplewidth = Params.simplewidth.replace('%', '%%')
        Params.simplewidth = ' width="%s" ' % Params.simplewidth

    # calendar view: monthly, list, simple
    # default: 'monthly'
    Params.firstview = params.get('firstview', 'monthly')

    # calendar date: in YYYYMM format (in monthly, simple view)
    # default: current month
    Params.curdate = params.get('curdate', '')

    # upcoming range: # of days for upcoming event list
    # default: 7
    try:
        Params.upcomingrange = int(params.get('upcomingrange', Globs.upcomingrange))
    except (TypeError, ValueError):
        Params.upcomingrange = Globs.upcomingrange

    # number of calendar: # of calendar for monthly & simple view
    # default: 1
    try:
        Params.numcal = int(params.get('numcal', '1'))
    except (TypeError, ValueError):
        Params.numcal = 1

    # change view enabled?
    # default: 1
    try:
        Params.changeview = int(params.get('changeview', '1'))
    except (TypeError, ValueError):
        Params.changeview = 1

    # shows the event at the last weekday if the recurred weekday is not available.
    # default: 0
    try:
        Params.showlastweekday = int(params.get('showlastweekday', '0'))
    except (TypeError, ValueError):
        Params.showlastweekday = 0

    # show error message?
    # default: 1
    try:
        Params.showerror = int(params.get('showerror', '1'))
    except (TypeError, ValueError):
        Params.showerror = 1

    # show week number?
    # default: 0
    try:
        Params.showweeknumber = int(params.get('showweeknumber', '0'))
    except (TypeError, ValueError):
        Params.showweeknumber = 0

    # default bgcolor
    Params.bgcolor = '#ddffdd'


def setglobalvalues(macro):

    request = macro.request
    formatter = macro.formatter

    # Useful variables
    Globs.baseurl = request.getBaseURL() + '/'
    Globs.pagename = formatter.page.page_name
    Globs.request = request
    Globs.formatter = formatter
    Globs.pageurl = '%s/%s' % (request.getScriptname(), wikiutil.quoteWikinameURL(formatter.page.page_name))

    # This fixes the subpages bug. subname is now used instead of pagename when creating certain urls
    Globs.subname = Globs.pagename.split('/')[-1]

    pagepath = formatter.page.getPagePath()
    Globs.pagepath = formatter.page.getPagePath()

    # european / US differences
    months = ('January','February','March','April','May','June','July','August','September','October','November','December')

    # Set things up for Monday or Sunday as the first day of the week
    if calendar.firstweekday() == calendar.MONDAY:
        wkend = 6
        wkdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
    elif calendar.firstweekday() == calendar.SUNDAY:
        wkend = 0
        wkdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

    Globs.months = months
    Globs.wkdays = wkdays
    Globs.wkend = wkend

    year, month, day, h, m, s, wd, yd, ds = request.user.getTime(time.time())
    Globs.today = datetime.date(year, month, day)
    Globs.now = datetime.time(h, m, s)

    Globs.debugmsg = ''
    Globs.errormsg = ''


def showReferPageParsed(event, targettext='title', showdesc=0):
    request = Globs.request
    pagename = Globs.pagename

    refer = event['refer']
    targettext = event[targettext]
    startdate = event['startdate']
    enddate = event['enddate']
    description = event['description']
    starttime = event['starttime']
    endtime = event['endtime']
    hid = event['hid']

    refer_url = '%s/%s' % (request.getScriptname(), wikiutil.quoteWikinameURL(refer))

    if not Params.changeview:
        refer_url = ''
        hid = ''

    if showdesc:
        if (startdate == enddate) and (starttime and endtime):
            timedescription = '(%s:%s ~ %s:%s)' % (starttime[:2], starttime[2:], endtime[:2], endtime[2:])
            if description:
                timedescription = '%s ' % timedescription
        else:
            timedescription = ''

        targetlink = '<a href="%s#%s" title="%s%s">%s</a>' % ( refer_url, hid, timedescription, wikiutil.escape(description), wikiutil.escape(targettext) )

    else:
        targetlink = '<a href="%s#%s">%s</a>' % ( refer_url, hid, wikiutil.escape(targettext))

    return targetlink


def showReferPageParsedForLabel(thelabel, targettext='name', showdesc=1):
    request = Globs.request
    pagename = Globs.pagename

    labels = Globs.labels

    label_bgcolor = ''
    refer = ''

    if labels and labels.has_key(thelabel):
        targettext = labels[thelabel][targettext]
        refer = labels[thelabel]['refer']
        if showdesc:
            label_bgcolor = labels[thelabel]['bgcolor']

    if not refer:
        return '<i>%s</i>' % thelabel

    refer_url = '%s/%s' % (request.getScriptname(), wikiutil.quoteWikinameURL(refer))

    if showdesc:
        targetlink = '<a href="%s" title="%s">%s</a>' % ( refer_url, label_bgcolor, wikiutil.escape(targettext) )
    else:
        targetlink = '<a href="%s">%s</a>' % ( refer_url, wikiutil.escape(targettext))

    return targetlink


def getheadingid(request, referpage, title):

    pntt = (referpage + title).encode(config.charset)
    hid = "head-" + sha.new(pntt).hexdigest()

    if not hasattr(request, '_eventcal_headings'):
        request._eventcal_headings = {}

    request._eventcal_headings.setdefault(pntt, 0)
    request._eventcal_headings[pntt] += 1
    if request._eventcal_headings[pntt] > 1:
        hid += '-%d'%(request._eventcal_headings[pntt],)

    return hid


def getquerystring(req_fields):

    m_query = []
    tmp_form_vals = Globs.form_vals

    # format querystring
    # action should be poped out
    for field in req_fields:
        if tmp_form_vals.has_key(field):
            m_query.append(u'%s=%s' % (field, tmp_form_vals[field]) )

    if 'prevcalaction' in req_fields:
        if not tmp_form_vals.has_key('prevcalaction'):
            m_query.append(u'%s=%s' % ('prevcalaction', tmp_form_vals['calaction']) )

    m_query = u'&'.join(m_query)

    if m_query:
        m_query = '&%s' % m_query

    return m_query


def showmenubar():
    """ Bottom menu bar """

    request = Globs.request
    cal_action = Globs.cal_action
    page_name = Globs.pagename

    page_url = Globs.pageurl

    if not Params.menubar: return ''

    if cal_action == 'simple':
        menuwidth = Params.simplewidth
    elif cal_action == 'monthly':
        menuwidth = Params.monthlywidth
    else:
        menuwidth = ''

    left_menu_selected = []
    right_menu_selected = []

    # Go Today
    year, month, day = gettodaydate()
    mnu_curmonthcal = u'<a href="%s?calaction=%s&caldate=%d%02d%02d%s" title="Go Today">[Today]</a>' % (page_url, cal_action, year, month, day, getquerystring(['numcal']))

    # List View
    mnu_listview = u'<a href="%s?calaction=list%s" title="List of all events">[List]</a>' % (page_url, getquerystring(['caldate', 'numcal']))

    # Monthly View
    mnu_monthview = u'<a href="%s?calaction=monthly%s" title="Monthly view">[Monthly]</a>' % (page_url, getquerystring(['caldate', 'numcal']) )

    # Simple Calendar View
    mnu_simpleview = u'<a href="%s?calaction=simple%s" title="Simple calendar view">[Simple]</a>' % (page_url, getquerystring(['caldate', 'numcal']) )

    # Upcoming Event List
    mnu_upcomingview = u'<a href="%s?calaction=upcoming%s" title="Upcoming event list">[Upcoming]</a>' % (page_url, getquerystring(['caldate', 'numcal']) )

    # Daily View
    mnu_dayview = u'<a href="%s?calaction=daily%s" title="Daily view">[Daily]</a>' % (page_url, getquerystring(['caldate', 'numcal']) )

    # Weekly View
    mnu_weekview = u'<a href="%s?calaction=weekly%s" title="Weekly view">[Weekly]</a>' % (page_url, getquerystring(['caldate', 'numcal']) )

    # iCalendar download
    mnu_ical = u'<a href="%s/?calaction=%s&action=AttachFile&do=get&target=events.ics" title="icalendar download">[ical]</a>' % (page_url, cal_action)

    html = [
        u'\r\n',
        u'<table class="eventcalendar_menubar" %s>',
        u'  <tr>',
        u'  <td class="eventcalendar_menubar" align="left">%s</td>',
        u'  <td class="eventcalendar_menubar" align="right">%s</td>',
        u'  </tr>',
        u'</table>',
        ]

    if cal_action == 'list':
        left_menu_selected.append(mnu_monthview)
        left_menu_selected.append(mnu_weekview)
        left_menu_selected.append(mnu_dayview)
        left_menu_selected.append(mnu_simpleview)
        left_menu_selected.append(mnu_ical)
        right_menu_selected.append(mnu_upcomingview)

    elif cal_action == 'simple':
        left_menu_selected.append(mnu_monthview)
        left_menu_selected.append(mnu_weekview)
        left_menu_selected.append(mnu_dayview)
        left_menu_selected.append(mnu_ical)
        right_menu_selected.append(mnu_listview)
        right_menu_selected.append(mnu_upcomingview)
        right_menu_selected.append(mnu_curmonthcal)

    elif cal_action == 'upcoming':
        left_menu_selected.append(mnu_monthview)
        left_menu_selected.append(mnu_weekview)
        left_menu_selected.append(mnu_dayview)
        left_menu_selected.append(mnu_simpleview)
        left_menu_selected.append(mnu_ical)
        right_menu_selected.append(mnu_listview)

    elif cal_action == 'weekly':
        left_menu_selected.append(mnu_monthview)
        left_menu_selected.append(mnu_dayview)
        left_menu_selected.append(mnu_simpleview)
        left_menu_selected.append(mnu_ical)
        right_menu_selected.append(mnu_upcomingview)
        right_menu_selected.append(mnu_listview)
        right_menu_selected.append(mnu_curmonthcal)

    elif cal_action == 'daily':
        left_menu_selected.append(mnu_monthview)
        left_menu_selected.append(mnu_weekview)
        left_menu_selected.append(mnu_simpleview)
        left_menu_selected.append(mnu_ical)
        right_menu_selected.append(mnu_upcomingview)
        right_menu_selected.append(mnu_listview)
        right_menu_selected.append(mnu_curmonthcal)

    else:
        left_menu_selected.append(mnu_weekview)
        left_menu_selected.append(mnu_dayview)
        left_menu_selected.append(mnu_simpleview)
        left_menu_selected.append(mnu_ical)
        right_menu_selected.append(mnu_upcomingview)
        right_menu_selected.append(mnu_listview)
        right_menu_selected.append(mnu_curmonthcal)

    left_menu_selected = u'\r\n'.join(left_menu_selected)
    right_menu_selected = u'\r\n'.join(right_menu_selected)

    html = u'\r\n'.join(html)
    html = html % (menuwidth, left_menu_selected, right_menu_selected)

    return html


def getdatefield(str_date):
    str_year = ''
    str_month = ''
    str_day = ''

    if len(str_date) == 6:
        # year+month
        str_year = str_date[:4]
        str_month = str_date[4:]
        str_day = '1'

    elif len(str_date) == 8:
        # year+month+day
        str_year = str_date[:4]
        str_month = str_date[4:6]
        str_day = str_date[6:]

    elif len(str_date) == 10:
        # year+?+month+?+day
        str_year = str_date[:4]
        str_month = str_date[5:7]
        str_day = str_date[8:]

    else:
        raise ValueError

    # It raises exception if the input date is incorrect
    temp = datetime.date(int(str_year), int(str_month), int(str_day))

    return temp.year, temp.month, temp.day


def gettimefield(str_time):
    str_hour = ''
    str_min = ''

    if len(str_time) == 4:
        # hour+minute
        str_hour = str_time[:2]
        str_min = str_time[2:]

    elif len(str_time) == 5:
        # hour+?+minute
        str_hour = str_time[:2]
        str_min = str_time[3:]

    else:
        raise ValueError

    # It raises exception if the input date is incorrect
    temp = datetime.time(int(str_hour), int(str_min))

    return temp.hour, temp.minute


def gettodaydate():
    today = Globs.today
    return today.year, today.month, today.day


def cal_listhead():

    html = [
        u'  <tr>',
        u'      <td class="list_head">Title</td>',
        u'      <td class="list_head">Start Date</td>',
        u'      <td class="list_head">End Date</td>',
        u'      <td class="list_head">Recurrence</td>',
        u'      <td class="list_head">Label</td>',
        u'      <td class="list_head">Description</td>',
        u'      <td class="list_head">Reference</td>',
        u'  </tr>',
        ]

    return u'\r\n'.join(html)


def showeventlist():

    debug('Show Calendar: List view')

    request = Globs.request
    formatter = Globs.formatter

    html_event_rows = []
    html_list_header = cal_listhead()

    # read all the events
    events, cal_events, labels = loadEvents()

    # sort events
    sorted_eventids = events.keys()
    sorted_eventids.sort(comp_list_events)

    for eid in sorted_eventids:
        if not events[eid]['clone']:
            html_event_rows.append( listshow_event(events[eid]) )

    html_event_rows = u'\r\n'.join(html_event_rows)

    html_list_table = [
        u'\r\n<div id="eventlist">',
        u'<table class="eventlist">',
        u'%s' % html_list_header,
        u'%s' % html_event_rows,
        u'</table>',
        u'</div>',
        ]
    html_list_table = u'\r\n'.join(html_list_table)

    return html_list_table


def listshow_event(event):

    if event['recur_freq']:
        if event['recur_freq'] == -1:
            recur_desc = 'last %s' % event['recur_type']
        else:
            recur_desc = 'every %d %s' % (event['recur_freq'], event['recur_type'])

        if event['recur_until']:
             recur_desc = '%s until %s' % (recur_desc, formatcfgdatetime(event['recur_until']))
    else:
        recur_desc = ''

    html = [
        u'  <tr>',
        u'  <td class="list_entry">%s</td>' % converttext(event['title']),
        u'  <td class="list_entry">%s</td>' % formatcfgdatetime(event['startdate'], event['starttime']),
        u'  <td class="list_entry">%s</td>' % formatcfgdatetime(event['enddate'], event['endtime']),
        u'  <td class="list_entry">%s</td>' % recur_desc,
        u'  <td class="list_entry">%s</td>' % showReferPageParsedForLabel(event['label']),
        u'  <td class="list_entry">%s</td>' % converttext(event['description']),
        u'  <td class="list_entry">%s</td>' % showReferPageParsed(event, 'refer'),
        u'  </tr>',
        ]

    return u'\r\n'.join(html)


def showupcomingeventlist():

    debug('Show Calendar: Upcoming Event View')

    request = Globs.request
    formatter = Globs.formatter

    html_event_rows = []
    html_list_header = cal_listhead()

    year, month, day = gettodaydate()
    day_delta = datetime.timedelta(days=Params.upcomingrange)
    cur_date = datetime.date(year, month, day)
    next_range = cur_date + day_delta

    # set ranges of events
    datefrom = u'%04d%02d%02d' % (year, month, day)
    dateto = u'%04d%02d%02d' % (next_range.year, next_range.month, next_range.day)

    # read all the events (no cache)
    events, cal_events, labels = loadEvents(datefrom, dateto, 1)

    nowtime = formattimeobject(Globs.now)

    datefrom = formatcfgdatetime(cur_date, nowtime)
    #u'%04d-%02d-%02d %s:%s' % (year, month, day, nowtime[:2], nowtime[2:])
    dateto = formatcfgdatetime(formatdateobject(next_range))
    #u'%04d-%02d-%02d' % (next_range.year, next_range.month, next_range.day)

    # sort events
    sorted_eventids = events.keys()
    sorted_eventids.sort(comp_list_events)

    for eid in sorted_eventids:
        if events[eid]['enddate'] >= formatdateobject(Globs.today):
            if (not events[eid]['endtime']) or events[eid]['endtime'] >= formattimeobject(Globs.now):
                html_event_rows.append( listshow_event(events[eid]) )

    html_event_rows = u'\r\n'.join(html_event_rows)

    html_list_table = [
        u'\r\n<div id="eventlist">',
        u'<table class="eventlist">',
        u'<tr><td colspan="7" class="list_entry" style="border-width: 0px;"><b>Upcoming Event List: %s ~ %s</b><p><br><p></td></tr>' % (datefrom, dateto),
        u'%s' % html_list_header,
        u'%s' % html_event_rows,
        u'</table>',
        u'</div>',
        ]
    html_list_table = u'\r\n'.join(html_list_table)

    return html_list_table


def showcalendar():

    request = Globs.request
    formatter = Globs.formatter
    form_vals = Globs.form_vals

    html = []

    if form_vals.has_key('caldate'):
        try:
            year, month, str_temp = getdatefield(form_vals['caldate'])
        except (TypeError, ValueError):
            errormsgcode('invalid_caldate')
            year, month, dy = gettodaydate()

    elif Params.curdate:
        try:
            year, month, str_temp = getdatefield(Params.curdate)
        except (TypeError, ValueError):
            errormsgcode('invalid_curdate')
            year, month, dy = gettodaydate()

    else:
        year, month, dy = gettodaydate()

    # check number of calendar
    numcal = Params.numcal

    if form_vals.has_key('numcal'):
        try:
            numcal = int(form_vals['numcal'])
        except (TypeError, ValueError):
            errormsgcode('invalid_numcal')

    if numcal < 1:
        numcal = 1
    elif numcal > 12:
        numcal = 12

    for index in range(numcal):

        cyear, cmonth = yearmonthplusoffset(year, month, index)

        cal_html = showeventcalendar(cyear, cmonth)
        html.append(cal_html)

    return u''.join(html)


def showdailycalendar():

    request = Globs.request
    formatter = Globs.formatter

    form_vals = Globs.form_vals

    if form_vals.has_key('caldate'):
        try:
            year, month, dy = getdatefield(form_vals['caldate'])

            if len(form_vals['caldate']) <= 6:
                tyear, tmonth, tdy = gettodaydate()
                if tyear == year and month == tmonth:
                    dy = tdy

        except (TypeError, ValueError):
            errormsgcode('invalid_caldate')
            year, month, dy = gettodaydate()

    elif Params.curdate:
        try:
            year, month, dy = getdatefield(Params.curdate)
        except (TypeError, ValueError):
            errormsgcode('invalid_curdate')
            year, month, dy = gettodaydate()

    else:
        year, month, dy = gettodaydate()

    html = showdailyeventcalendar(year, month, dy)

    return u''.join(html)


def showweeklycalendar():

    request = Globs.request
    formatter = Globs.formatter

    form_vals = Globs.form_vals

    if form_vals.has_key('caldate'):
        try:
            year, month, dy = getdatefield(form_vals['caldate'])

            if len(form_vals['caldate']) <= 6:
                tyear, tmonth, tdy = gettodaydate()
                if tyear == year and month == tmonth:
                    dy = tdy

        except (TypeError, ValueError):
            errormsgcode('invalid_caldate')
            year, month, dy = gettodaydate()

    elif Params.curdate:
        try:
            year, month, dy = getdatefield(Params.curdate)
        except (TypeError, ValueError):
            errormsgcode('invalid_curdate')
            year, month, dy = gettodaydate()
    else:
        year, month, dy = gettodaydate()

    html = showweeklyeventcalendar(year, month, dy)

    return u''.join(html)


def download_events_ical():
    """ Download events' data in icalendar format """
    debug('Download events: icalendar')

    request = Globs.request
    formatter = None

    # read all the events
    events, cal_events, labels = loadEvents()

    # sort events
    sorted_eventids = events.keys()
    sorted_eventids.sort(comp_list_events)

    cal = icalendar.Calendar()
    cal.add('prodid', '-//moinmo.in//EventCalendar/')
    cal.add('version', '1.0')

    def display(cal):
        return cal.to_ical()
        # return cal.to_ical().replace('\r\n', '\n').strip()

    def make_date_time(event, arg_date, arg_time):
        try:
            event[arg_time]
        except NameError:
            event[arg_time] = u'0000'
        event_date_time = event[arg_date]+event[arg_time]
        return parser.parse(event_date_time)

    def make_event(event):
        new_event = icalendar.Event()
        new_event.add('summary', item['title'])
        new_event.add('DTSTART', make_date_time(event,
                                                'startdate',
                                                'starttime'))
        new_event.add('DTEND', make_date_time(event, 'enddate', 'endtime'))
        new_event.add('description', item['description'])
        if item['label']:
            new_event.add('labels', item['label'])
        if item['refer']:
            new_event.add('url', item['refer'])  # This doesn't give an URL, just the name of the page
        # eventitem['bgcolor'] = e_bgcolor
        # eventitem['recur_freq'] = e_recur_freq
        # eventitem['recur_type'] = e_recur_type
        # eventitem['recur_until'] = e_recur_until
        # new_event['uid'] = make_uid(event)
        # new_event['DTSTAMP'] = formatcfgdatetime(event['startdate'], event['starttime'])
        # new_event['url'] = 'issue.html_url'
        # new_event['status'] = 'NEEDS-ACTION'
        # new_event.add('labels', item['label'])
        # new_event.add('title', item['title'])
        # new_event.add('category', item['refer'])
        # new_event.add('dtstamp', datetime.datetime(2018,1,24,0,10,0,tzinfo=pytz.utc))
        cal.add_component(new_event)
        return new_event

    for item in events.values():
        make_event(item)
        # print '~~~ Item title: ', item['title']

        # eventitem['recur_freq'] = e_recur_freq
        # eventitem['recur_type'] = e_recur_type
        # eventitem['recur_until'] = e_recur_until

        if item['recur_freq']:
            if item['recur_freq'] == -1:
                recur_desc = 'last %s' % item['recur_type']
                print "item['recur_freq'] 1" + str(item['recur_freq'])
                print "item['recur_type'] 1" + str(item['recur_type'])
                # print "item['recur_freq'] == -1 " + recur_desc
            else:
                recur_desc = 'every %d %s' % (item['recur_freq'], item['recur_type'])
                print "item['recur_freq'] 2" + str(item['recur_freq'])
                print "item['recur_type'] 1" + str(item['recur_type'])
                # print 'ELSE: '+ recur_desc

            if item['recur_until']:
                 recur_desc = '%s until %s' % (recur_desc, formatcfgdatetime(item['recur_until']))
                 print "item['recur_freq'] 3" + str(item['recur_until'])
                 # print "item['recur_until'] "+ recur_desc

    # request.content_type = "text/calendar; charset=%s" % config.charset
    html = display(cal)

    pagename = Globs.pagename

    attach_dir = AttachFile.getAttachDir(request, pagename)
    new_ics_file = AttachFile.add_attachment(request, pagename, 'events.ics', display(cal), overwrite=1)

    return display(cal)


def showsimplecalendar():

    request = Globs.request
    formatter = Globs.formatter
    form_vals = Globs.form_vals

    html = []

    if form_vals.has_key('caldate'):
        try:
            year, month, str_temp = getdatefield(form_vals['caldate'])
        except (TypeError, ValueError):
            errormsgcode('invalid_caldate')
            year, month, dy = gettodaydate()
    elif Params.curdate:
        try:
            year, month, str_temp = getdatefield(Params.curdate)
        except (TypeError, ValueError):
            errormsgcode('invalid_curdate')
            year, month, dy = gettodaydate()
    else:
        year, month, dy = gettodaydate()

    # check number of calendar
    numcal = Params.numcal

    if form_vals.has_key('numcal'):
        try:
            numcal = int(form_vals['numcal'])
        except (TypeError, ValueError):
            errormsgcode('invalid_numcal')


    if numcal < 1:
        numcal = 1
    elif numcal > 12:
        numcal = 12

    for index in range(numcal):

        cyear, cmonth = yearmonthplusoffset(year, month, index)

        cal_html = showsimpleeventcalendar(cyear, cmonth)
        html.append(cal_html)

    return u''.join(html)


def comp_cal_events(xid, yid):
    """Sort events in cal_events by length of days of the event"""

    events = Globs.events

    if events[xid]['date_len'] > events[yid]['date_len']:
        return -1
    elif events[xid]['date_len'] == events[yid]['date_len']:
        if events[xid]['date_len'] == 1:
            if events[xid]['starttime'] == events[yid]['starttime']:
                return cmp(events[yid]['time_len'], events[xid]['time_len'])
            else:
                return cmp(events[xid]['starttime'], events[yid]['starttime'])
        else:
            return 0
    else:
        return 1


def comp_list_events(xid, yid):
    """ Sort events in the list by start date of the event """
    events = Globs.events

    return cmp(events[xid]['startdate'], events[yid]['startdate'])


def loadEvents(datefrom='', dateto='', nocache=0):
    """ load events from wiki pages """

    request = Globs.request

    debug('Loading event information.')

    events = {}
    labels = {}
    cal_events = {}
    raw_events = {}

    raw_events, labels = loadEventsFromWikiPages()

    # handling cal_events
    if datefrom or dateto:

        # cache configurations
        arena = Page(request, Globs.pagename)
        eventkey = 'events'
        filteredeventkey = 'events_%s-%s' % (datefrom, dateto)
        caleventkey = 'calevents_%s-%s' % (datefrom, dateto)

        cache_events = caching.CacheEntry(request, arena, eventkey,scope='item')
        cache_filteredevents = caching.CacheEntry(request, arena, filteredeventkey,scope='item')
        cache_calevents = caching.CacheEntry(request, arena, caleventkey,scope='item')

        dirty = 1

        debug('Checking cal_events cache')

        if not (cache_calevents.needsUpdate(cache_events._filename()) or cache_filteredevents.needsUpdate(cache_events._filename())):

            try:
                events = pickle.loads(cache_filteredevents.content())
                cal_events = pickle.loads(cache_calevents.content())
                debug('Cached event (filtered) information is used: total %d events' % len(events))
                dirty = 0
            except (pickle.UnpicklingError, IOError, EOFError, ValueError):
                debug('Picke error at fetching cached events (filtered)')
                events = {}
                cal_events = {}


        # if cache is dirty, update the cache
        if dirty:

            debug('Checking event cache: it\'s dirty or requested to refresh')
            debug('Building new cal_event information')

            try:
                datefrom, dateto = int(datefrom), int(dateto)
            except (TypeError, ValueError):
                datefrom, dateto = 0, 0

            clone_num = 0

            for e_id in raw_events.keys():

                cur_event = raw_events[e_id]

                # handling event recurrence
                recur_freq = cur_event['recur_freq']

                if recur_freq or recur_freq == -1:

                    if not (cur_event['recur_until'] and int(cur_event['recur_until']) < datefrom) or int(cur_event['startdate']) > dateto:

                        if not (int(cur_event['enddate']) < datefrom or int(cur_event['startdate']) > dateto):
                            # generating cal_events for iteself
                            events[e_id] = cur_event.copy()
                            insertcalevents(cal_events, datefrom, dateto, e_id, cur_event['startdate'], cur_event['enddate'])

                        delta_date_len = datetime.timedelta(days = int(cur_event['date_len']) - 1 )

                        if cur_event['recur_type'] == 'day':

                            day_delta = int(recur_freq)
                            startdate = getdatetimefromstring(cur_event['startdate'])
                            datefrom_date = getdatetimefromstring(datefrom)

                            if int(datefrom) > int(cur_event['startdate']):
                                diffs = datefrom_date - startdate
                                q_delta = diffs.days / day_delta
                                if diffs.days % day_delta > 0:
                                    q_delta += 1
                            else:
                                q_delta = 1

                            while 1:

                                if q_delta == 0:
                                    q_delta += 1
                                    continue

                                recurred_startdate = startdate + datetime.timedelta(days = q_delta * day_delta )
                                recurred_enddate = recurred_startdate + delta_date_len

                                new_startdate = formatdateobject(recurred_startdate)
                                new_enddate = formatdateobject(recurred_enddate)

                                if int(new_startdate) > dateto or (cur_event['recur_until'] and int(cur_event['recur_until']) < int(new_startdate)):
                                    break

                                clone_num += 1
                                clone_id = 'c%d' % clone_num

                                events[clone_id] = cur_event.copy()
                                events[clone_id]['id'] = clone_id
                                events[clone_id]['startdate'] = new_startdate
                                events[clone_id]['enddate'] = new_enddate
                                events[clone_id]['clone'] = 1

                                insertcalevents(cal_events, datefrom, dateto, clone_id, new_startdate, new_enddate)

                                q_delta += 1

                        elif cur_event['recur_type'] == 'week':

                            day_delta = int(recur_freq) * 7

                            startdate = getdatetimefromstring(cur_event['startdate'])
                            datefrom_date = getdatetimefromstring(datefrom)

                            if int(datefrom) > int(cur_event['startdate']):
                                diffs = datefrom_date - startdate
                                q_delta = diffs.days / day_delta
                                if diffs.days % day_delta > 0:
                                    q_delta += 1
                            else:
                                q_delta = 1

                            while 1:

                                if q_delta == 0:
                                    q_delta += 1
                                    continue

                                recurred_startdate = startdate + datetime.timedelta(days = q_delta * day_delta )
                                recurred_enddate = recurred_startdate + delta_date_len

                                new_startdate = formatdateobject(recurred_startdate)
                                new_enddate = formatdateobject(recurred_enddate)

                                if int(new_startdate) > dateto or (cur_event['recur_until'] and int(cur_event['recur_until']) < int(new_startdate)):
                                    break

                                clone_num += 1
                                clone_id = 'c%d' % clone_num

                                events[clone_id] = cur_event.copy()
                                events[clone_id]['id'] = clone_id
                                events[clone_id]['startdate'] = new_startdate
                                events[clone_id]['enddate'] = new_enddate
                                events[clone_id]['clone'] = 1

                                insertcalevents(cal_events, datefrom, dateto, clone_id, new_startdate, new_enddate)

                                q_delta += 1


                        elif cur_event['recur_type'] == 'weekday':

                            syear, smonth, sday = getdatefield(cur_event['startdate'])
                            cyear, cmonth, cday = getdatefield(str(datefrom))

                            recur_weekday = calendar.weekday(syear, smonth, sday)

                            while 1:

                                firstweekday, daysinmonth = calendar.monthrange(cyear, cmonth)
                                firstmatch = (recur_weekday - firstweekday) % 7 + 1

                                if recur_freq == -1:
                                    therecur_day = xrange(firstmatch, daysinmonth + 1, 7)[-1]
                                else:
                                    #XXX should handle error
                                    try:
                                        therecur_day = xrange(firstmatch, daysinmonth + 1, 7)[recur_freq-1]
                                    except IndexError:
                                        if Params.showlastweekday:
                                            # if no matched weekday, the last weekday will be displayed
                                            therecur_day = xrange(firstmatch, daysinmonth + 1, 7)[-1]
                                        else:
                                            # if no matched weekday, no event will be displayed
                                            cyear, cmonth = yearmonthplusoffset(cyear, cmonth, 1)
                                            continue


                                recurred_startdate = datetime.date(cyear, cmonth, therecur_day)
                                recurred_enddate = recurred_startdate + delta_date_len

                                new_startdate = formatdateobject(recurred_startdate)
                                new_enddate = formatdateobject(recurred_enddate)

                                if int(new_startdate) < int(datefrom) or new_startdate == cur_event['startdate']:
                                    cyear, cmonth = yearmonthplusoffset(cyear, cmonth, 1)
                                    continue

                                if int(new_startdate) > dateto or (cur_event['recur_until'] and int(cur_event['recur_until']) < int(new_startdate)):
                                    break

                                clone_num += 1
                                clone_id = 'c%d' % clone_num

                                events[clone_id] = cur_event.copy()
                                events[clone_id]['id'] = clone_id
                                events[clone_id]['startdate'] = new_startdate
                                events[clone_id]['enddate'] = new_enddate
                                events[clone_id]['clone'] = 1

                                insertcalevents(cal_events, datefrom, dateto, clone_id, new_startdate, new_enddate)

                                cyear, cmonth = yearmonthplusoffset(cyear, cmonth, 1)


                        elif cur_event['recur_type'] == 'month':

                            cyear, cmonth, therecurday = getdatefield(cur_event['startdate'])

                            while 1:

                                cyear, cmonth = yearmonthplusoffset(cyear, cmonth, recur_freq)
                                firstweekday, daysinmonth = calendar.monthrange(cyear, cmonth)
                                recur_day = therecurday
                                if daysinmonth < recur_day:
                                    recur_day = daysinmonth
                                new_startdate = formatDate(cyear, cmonth, recur_day)

                                if int(new_startdate) < int(datefrom):
                                    continue

                                recurred_startdate = datetime.date(cyear, cmonth, recur_day)
                                recurred_enddate = recurred_startdate + delta_date_len

                                new_startdate = formatdateobject(recurred_startdate)
                                new_enddate = formatdateobject(recurred_enddate)

                                if int(new_startdate) > dateto or (cur_event['recur_until'] and int(cur_event['recur_until']) < int(new_startdate)):
                                    break

                                clone_num += 1
                                clone_id = 'c%d' % clone_num

                                events[clone_id] = cur_event.copy()
                                events[clone_id]['id'] = clone_id
                                events[clone_id]['startdate'] = new_startdate
                                events[clone_id]['enddate'] = new_enddate
                                events[clone_id]['clone'] = 1

                                insertcalevents(cal_events, datefrom, dateto, clone_id, new_startdate, new_enddate)

                        elif cur_event['recur_type'] == 'year':

                            ryear, rmonth, rday = getdatefield(cur_event['startdate'])
                            cyear, cmonth, cday = getdatefield(str(datefrom))

                            while 1:

                                ryear += recur_freq
                                new_startdate = formatDate(ryear, rmonth, rday)

                                if int(new_startdate) < int(datefrom):
                                    continue

                                if int(new_startdate) > dateto or (cur_event['recur_until'] and int(cur_event['recur_until']) < int(new_startdate)):
                                    break

                                recurred_startdate = datetime.date(ryear, rmonth, rday)
                                recurred_enddate = recurred_startdate + delta_date_len

                                new_startdate = formatdateobject(recurred_startdate)
                                new_enddate = formatdateobject(recurred_enddate)

                                clone_num += 1
                                clone_id = 'c%d' % clone_num

                                events[clone_id] = cur_event.copy()
                                events[clone_id]['id'] = clone_id
                                events[clone_id]['startdate'] = new_startdate
                                events[clone_id]['enddate'] = new_enddate
                                events[clone_id]['clone'] = 1

                                insertcalevents(cal_events, datefrom, dateto, clone_id, new_startdate, new_enddate)

                else:

                    if not (int(cur_event['enddate']) < datefrom or int(cur_event['startdate']) > dateto):
                        events[e_id] = cur_event.copy()
                        insertcalevents(cal_events, datefrom, dateto, e_id, cur_event['startdate'], cur_event['enddate'])


            # sort cal_events
            # store event list into global variables in order to sort them
            Globs.events = events

            for eachdate in cal_events.keys():
                cal_events[eachdate].sort(comp_cal_events)

            # cache update
            if not nocache:
                cache_filteredevents.update(pickle.dumps(events, PICKLE_PROTOCOL))
                cache_calevents.update(pickle.dumps(cal_events, PICKLE_PROTOCOL))

    else:
        events = raw_events

        # store event list into global variables in order to sort them
        Globs.events = events

    Globs.labels = labels

    debug(u'Total %d events are loaded finally.' % len(events))
    debug(u'Total %d labels are loaded finally.' % len(labels))

    return events, cal_events, labels


def loadEventsFromWikiPages():

    events = {}
    labels = {}
    cached_event_loaded = 0
    dirty = 0

    eventrecord_list = []
    labelrecord_list = []
    eventpages = []
    stored_errmsg = ''

    request = Globs.request
    category = Params.category

    # cache configurations
    arena = Page(request, Globs.pagename)

    eventkey = 'events'
    labelkey = 'labels'
    pagelistkey = 'eventpages'
    errmsglistkey = 'eventcalerrormsglist'

    cache_events = caching.CacheEntry(request, arena, eventkey,scope='item')
    cache_labels = caching.CacheEntry(request, arena, labelkey,scope='item')
    cache_pages = caching.CacheEntry(request, arena, pagelistkey,scope='item')
    cache_errmsglist = caching.CacheEntry(request, arena, errmsglistkey,scope='item')

    # page list cache

    debug('Checking page list cache')

    # check the time at which page list cache has been created

    cp_mtime = cache_pages.mtime()
    timedelta_days = 9999

    if cp_mtime:
        cp_date = datetime.datetime.fromtimestamp(cp_mtime)
        today = datetime.datetime.fromtimestamp(time.time())
        datediff = today - cp_date
        timedelta_days = datediff.days
        debug('Time from page list cache built = %s' % datediff)


    if Globs.page_action == 'refresh' or cache_pages.needsUpdate(arena._text_filename()) or timedelta_days >= 1:
        categorypages = searchPages(request, category)
        for page in categorypages:
            eventpages.append(page.page_name)
        cache_pages.update('\n'.join(eventpages).encode('utf-8'))
        debug('New page list is built: %d pages' % len(eventpages))
    else:
        eventpages = cache_pages.content().decode('utf-8').split('\n')
        debug('Cached page list is used: %d pages' % len(eventpages))

    if not Globs.page_action == 'refresh':
        # check the cache validity
        for page_name in eventpages:

            p = Page(request, page_name)
            e_ref = page_name

            if cache_events.needsUpdate(p._text_filename()) or cache_labels.needsUpdate(p._text_filename()) or cache_errmsglist.needsUpdate(p._text_filename()):
                dirty = 1
                break
    else:
        dirty = 1

    if dirty:
        # generating events

        dirty_local = 0
        debug_records = {}

        eventrecordkey = 'eventrecords'
        labelrecordkey = 'labelrecords'
        errmsgkey = 'eventcalerrormsg'

        # fetch event records from each page in the category
        for page_name in eventpages:

            p = Page(request, page_name)
            e_ref = page_name


            cache_errmsg = caching.CacheEntry(request, p, errmsgkey,scope='item')
            cache_eventrecords = caching.CacheEntry(request, p, eventrecordkey,scope='item')
            cache_labelrecords = caching.CacheEntry(request, p, labelrecordkey,scope='item')

            if cache_eventrecords.needsUpdate(p._text_filename()) or cache_labelrecords.needsUpdate(p._text_filename()) or Globs.page_action == 'refresh':
                page_content = p.get_raw_body()
                eventrecords, labelrecords = getEventRecordFromPage(page_content, e_ref)

                debug_records[e_ref] = '%d events are fetched from %s' % (len(eventrecords), e_ref)

                # XXXXX
                #debug('events: %s' % eventrecords)
                #debug('labels: %s' % labelrecords)

                cache_eventrecords.update(pickle.dumps(eventrecords, PICKLE_PROTOCOL))
                cache_labelrecords.update(pickle.dumps(labelrecords, PICKLE_PROTOCOL))
                cache_errmsg.update(pickle.dumps(Globs.errormsg, PICKLE_PROTOCOL))

                stored_errmsg += Globs.errormsg
                Globs.errormsg = ''

            else:
                try:
                    eventrecords = pickle.loads(cache_eventrecords.content())
                    labelrecords = pickle.loads(cache_labelrecords.content())
                    Globs.errormsg = pickle.loads(cache_errmsg.content())

                    debug_records[e_ref] = '%d cached eventrecords are used from %s' % (len(eventrecords), e_ref)

                except (pickle.UnpicklingError, IOError, EOFError, ValueError):
                    dirty = 1
                    page_content = p.get_raw_body()
                    eventrecords, labelrecords = getEventRecordFromPage(page_content, e_ref)
                    debug_records[e_ref] = '%d eventrecords are fetched from %s due to pickle error' % (len(eventrecords), e_ref)

                    cache_eventrecords.update(pickle.dumps(eventrecords, PICKLE_PROTOCOL))
                    cache_labelrecords.update(pickle.dumps(labelrecords, PICKLE_PROTOCOL))
                    cache_errmsg.update(pickle.dumps(Globs.errormsg, PICKLE_PROTOCOL))

            eventrecord_list.append(eventrecords)
            labelrecord_list.append(labelrecords)

            stored_errmsg += Globs.errormsg
            Globs.errormsg = ''

        debug('Checking event cache: it\'s dirty or requested to refresh')

    else:

        debug('Checking event cache: still valid')

        try:
            events = pickle.loads(cache_events.content())
            labels = pickle.loads(cache_labels.content())
            stored_errmsg = pickle.loads(cache_errmsglist.content())

            cached_event_loaded = 1

            debug('Cached event information is used: total %d events' % len(events))

        except (pickle.UnpicklingError, IOError, EOFError, ValueError):
            events = {}
            labels = {}
            stored_errmsg = ''

            debug('Picke error at fetching cached events')

    # if it needs refreshed, generate events dictionary
    if not cached_event_loaded:

        # XXX: just for debugging
        debug('Building new event information')
        for page_name in eventpages:
            debug(debug_records[page_name])

        for eventrecords in eventrecord_list:
            for evtrecord in eventrecords:
                e_id = evtrecord['id']
                events[e_id] = evtrecord

        for labelrecords in labelrecord_list:
            for label in labelrecords:
                c_id = label['name']
                if not labels.has_key(c_id):
                    labels[c_id] = label
                else:
                    stored_errmsg += u'<li>%s\n' % geterrormsg('redefined_label', label['refer'], label['name'])

        # after generating updated events, update the cache
        cache_events.update(pickle.dumps(events, PICKLE_PROTOCOL))
        cache_labels.update(pickle.dumps(labels, PICKLE_PROTOCOL))
        cache_errmsglist.update(pickle.dumps(stored_errmsg, PICKLE_PROTOCOL))

        debug('Event information is newly built: total %d events' % len(events))

    Globs.errormsg = stored_errmsg

    # end of updating events block

    return events, labels


def getEventRecordFromPage(pagecontent, referpage):

    request = Globs.request

    eventrecords = []
    labelrecords = []
    page_bgcolor = ''
    page_description = ''

    e_num = 0

    # fetch the page default bgcolor
    regex_page_bgcolor = r"""
(?P<req_field>^[ ]+default_bgcolor::[ ]+)
(
    (?P<pagebgcolor>\#[0-9a-fA-F]{6})
    \s*?
    $
)?
"""

    pattern = re.compile(regex_page_bgcolor, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    match = pattern.search(pagecontent)

    if match:
        if match.group('pagebgcolor'):
            page_bgcolor = match.group('pagebgcolor')
        else:
            errormsg( geterrormsg('invalid_default_bgcolor', referpage) )


    # fetch the page default description
    regex_page_description = r"""
(?P<req_field>^[ ]+default_description::[ ]+)
(
    (?P<pagedescription>.*?)
    \s*?
    $
)?
"""

    pattern = re.compile(regex_page_description, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    match = pattern.search(pagecontent)

    if match:
        if match.group('pagedescription'):
            page_description = match.group('pagedescription')
        else:
            errormsg( geterrormsg('empty_default_description', referpage) )

    # fetch the label definition
    regex_label_definition = r"""
(?P<reqfield>^[ ]+label_def::[ ]+)
(
	(?P<name>[^,^:^\s]+?)
	[,: ]+
	(?P<bgcolor>\#[0-9a-fA-F]{6})
	\s*?
	$
)?
"""


    pattern = re.compile(regex_label_definition, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    match = pattern.findall(pagecontent)

    if match:

        for matchitem in match:

            labelitem = {}

            label_name = matchitem[2]
            label_bgcolor = matchitem[3]

            if label_name and label_bgcolor:
                labelitem['name'] = label_name
                labelitem['bgcolor'] = label_bgcolor
                labelitem['refer'] = referpage

                labelrecords.append(labelitem)
            else:
                errormsg( geterrormsg('empty_label_definition', referpage) )
                continue


    # fetch event item
    regex_eventitem = r"""
(?P<eventitem>
	(?P<heading>^\s*(?P<hmarker>=+)\s(?P<eventtitle>.*?)\s(?P=hmarker) $)
	(?P<eventdetail>
		.*?
		(?=
			^\s*(?P<nexthmarker>=+)\s(?P<nexteventtitle>.*?)\s(?P=nexthmarker) $
			| \Z
        )
	)
)
"""

    pattern = re.compile(regex_eventitem, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    match = pattern.findall(pagecontent)

    if match:

        for matchitem in match:

            eventitem = {}

            eventtitle = matchitem[3]
            eventdetail = matchitem[4]

            e_headid = getheadingid(request, referpage, eventtitle)

            if not eventdetail:
                continue

            #debug('Examininng "%s" event from %s ..' % (eventtitle, referpage))

            try:
                e_start_date, e_start_time, e_end_date, e_end_time, e_bgcolor, e_label, e_description, e_recur_freq, e_recur_type, e_recur_until = geteventfield(eventdetail)
            except EventcalError, errmsgcode:

                if not errmsgcode.value == 'pass':
                    errormsg( geterrormsg(errmsgcode.value, referpage, eventtitle, e_headid) )

                continue

            #except TypeError, ValueError:
            #    errormsg('undefined')
            #    continue

            # set default values
            if not e_bgcolor:
                e_bgcolor = page_bgcolor

            if not e_description:
                e_description = page_description

            e_num += 1
            e_id = 'e_%s_%d' % (referpage, e_num)

            eventitem['id'] = e_id
            eventitem['title'] = eventtitle
            eventitem['startdate'] = e_start_date
            eventitem['starttime'] = e_start_time
            eventitem['enddate'] = e_end_date
            eventitem['endtime'] = e_end_time
            eventitem['title'] = eventtitle
            eventitem['refer'] = referpage
            eventitem['bgcolor'] = e_bgcolor
            eventitem['label'] = e_label
            eventitem['description'] = e_description
            eventitem['recur_freq'] = e_recur_freq
            eventitem['recur_type'] = e_recur_type
            eventitem['recur_until'] = e_recur_until

            try:
                eventitem['date_len'] = diffday(e_start_date, e_end_date) + 1
                eventitem['clone'] = 0
                eventitem['hid'] = e_headid

                if eventitem['date_len'] == 1 and e_start_time and e_end_time:
                    eventitem['time_len'] = difftime(e_start_time, e_end_time) + 1
                else:
                    eventitem['time_len'] = 0

            except EventcalError, errmsgcode:
                debug('Failed to add "%s" event from %s ..' % (eventtitle, referpage))
                errormsg( geterrormsg(errmsgcode.value, referpage, eventtitle, e_headid) )
                continue

            eventrecords.append(eventitem)

            #debug('Added "%s" event from %s ..' % (eventtitle, referpage))

    return eventrecords, labelrecords


def geteventfield(detail):


    # START DATE REGEX ----------------------------
    regex_startdate = r"""
(?P<reqfield>^[ ]+start::(?=[ ]+))
(
    (?P<startdate>
        [ ]+
        (
            (?P<startdate1>
            	(?P<startyear1>19\d{2} | 20\d{2} | \d{2} )
            	[./-]
            	(?P<startmonth1>1[012] | 0[1-9] | [1-9])
            	[./-]
            	(?P<startday1>3[01] | 0[1-9] | [12]\d | [1-9])
            )
            |
            (?P<startdate2>
            	(?P<startmonth2>january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)
            	[ ]+
            	(?P<startday2>3[01] | 0[1-9] | [12]\d | [1-9])
            	(?: st | nd | rd | th )?
            	[ ,]+
            	(?P<startyear2>19\d{2} | 20\d{2} | \d{2})
            )
            |
            (?P<startdate3>
            	(?P<startyear3>19\d{2} | 20\d{2} | \d{2} )
            	(?P<startmonth3>1[012] | 0[1-9])
            	(?P<startday3>3[01] | 0[1-9] | [12]\d)
            )
        )
    )
    (?P<starttime>
        [ ,]+
        (
            (?P<starttime1>
            	(?P<starthour1> 1[0-2] | [0]?[1-9] )
            	(
            		(?: [.:])
            		(?P<startminute1>[0-5]\d{0,1} | [6-9])
            	)?
            	[ ]*
            	(?P<am1> am | pm | p | a )
            )
            |
            (?P<starttime2>
            	(?P<starthour2> | [01]\d{0,1} | 2[0-3] | [1-9])
            	(
            		(?: [.:])
            		(?P<startminute2>[0-5]\d{0,1} | [6-9])
            	)?
            )
            |
            (?P<starttime3>
            	(?P<starthour3> [01]\d | 2[0-3])
            	(?P<startminute3> [0-5]\d)?
            )
            |
            (?P<starttime4>
            	(?P<starthour4> 0[1-9] | 1[0-2])
            	(?P<startminute4> [0-5]\d)?
            	[ ]*
            	(?P<am4> am | pm | p | a )
            )
        )
    )?
    \s*?
    $
)?
"""



    # END DATE REGEX ----------------------------
    regex_enddate = r"""
(?P<reqfield>^[ ]+end::(?=[ ]+))
(
    (?P<enddate>
        [ ]+
        (
            (?P<enddate1>
            	(?P<endyear1>19\d{2} | 20\d{2} | \d{2} )
            	[./-]
            	(?P<endmonth1>1[012] | 0[1-9] | [1-9])
            	[./-]
            	(?P<endday1>3[01] | 0[1-9] | [12]\d | [1-9])
            )
            |
            (?P<enddate2>
            	(?P<endmonth2>january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)
            	[ ]+
            	(?P<endday2>3[01] | 0[1-9] | [12]\d | [1-9])
            	(?: st | nd | rd | th )?
            	[ ,]+
            	(?P<endyear2>19\d{2} | 20\d{2} | \d{2})
            )
            |
            (?P<enddate3>
            	(?P<endyear3>19\d{2} | 20\d{2} | \d{2} )
            	(?P<endmonth3>1[012] | 0[1-9])
            	(?P<endday3>3[01] | 0[1-9] | [12]\d)
            )
        )
    )?
    (?P<endtime>
        [ ,]+
        (
            (?P<endtime1>
            	(?P<endhour1> 1[0-2] | [0]?[1-9] )
            	(
            		(?: [.:])
            		(?P<endminute1>[0-5]\d{0,1} | [6-9])
            	)?
            	[ ]*
            	(?P<am1> am | pm | p | a )
            )
            |
            (?P<endtime2>
            	(?P<endhour2> | [01]\d{0,1} | 2[0-3] | [1-9])
            	(
            		(?: [.:])
            		(?P<endminute2>[0-5]\d{0,1} | [6-9])
            	)?
            )
            |
            (?P<endtime3>
            	(?P<endhour3> [01]\d | 2[0-3])
            	(?P<endminute3> [0-5]\d)?
            )
            |
            (?P<endtime4>
            	(?P<endhour4> 0[1-9] | 1[0-2])
            	(?P<endminute4> [0-5]\d)?
            	[ ]*
            	(?P<am4> am | pm | p | a )
            )
        )
    )?
    \s*?
    $
)?
"""

    regex_bgcolor = r"""
(?P<reqfield>^[ ]+bgcolor::[ ]+)
(
    (?P<bgcolor>\#[0-9a-fA-F]{6})?
    \s*?
    $
)?
"""

    regex_description = r"""
(?P<reqfield>^[ ]+description::[ ]+)
(
    (?P<description>.*?)
    \s*?
    $
)?
"""


    regex_recur = r"""
(?P<reqfield>^[ ]+recur::[ ]+)
(
    (?P<recur_freq>\d+|last)
    \s+
    (?P<recur_type>weekday|day|week|month|year)
    (
    	\s+
    	(?P<recur_until_req>until)
    	\s+
    	(?P<recur_until>
            (?P<enddate>
                (?P<enddate1>
                	(?P<endyear1>19\d{2} | 20\d{2} | \d{2} )
                	[./-]
                	(?P<endmonth1>1[012] | 0[1-9] | [1-9])
                	[./-]
                	(?P<endday1>3[01] | 0[1-9] | [12]\d | [1-9])
                )
                |
                (?P<enddate2>
                	(?P<endmonth2>january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)
                	\s+
                	(?P<endday2>3[01] | 0[1-9] | [12]\d | [1-9])
                	(?: st | nd | rd | th )?
                	[\s,]+
                	(?P<endyear2>19\d{2} | 20\d{2} | \d{2})
                )
                |
                (?P<enddate3>
                	(?P<endyear3>19\d{2} | 20\d{2} | \d{2} )
                	(?P<endmonth3>1[012] | 0[1-9])
                	(?P<endday3>3[01] | 0[1-9] | [12]\d)
                )
            )?
        )?
    )?
    \s*?
    $
)?
"""

    regex_label = r"""
(?P<reqfield>^[ ]+label::[ ]+)
(
	(?P<name>[^,^:^\s]+?)
	\s*?
	$
)?
"""


    # need help on regular expressions for more efficient/flexible form

    # compile regular expression objects

    pattern_startdate = re.compile(regex_startdate, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    pattern_enddate = re.compile(regex_enddate, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    pattern_bgcolor = re.compile(regex_bgcolor, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    pattern_label = re.compile(regex_label, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    pattern_description = re.compile(regex_description, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)
    pattern_recur = re.compile(regex_recur, re.UNICODE + re.MULTILINE + re.IGNORECASE + re.DOTALL + re.VERBOSE)

    ##################### retrieve startdate
    match = pattern_startdate.search(detail)

    if match:

        if match.group('startdate'):
            passed = 1
            # yyyy/mm/dd: 2006/05/10; 06/05/10,
            if match.group('startdate1'):
                if len(match.group('startyear1')) == 2:
                    startyear = '20%s' % match.group('startyear1')
                else:
                    startyear = match.group('startyear1')

                startmonth = match.group('startmonth1')
                startday = match.group('startday1')

            # M dd, yyyy: May 10, 2006; Jan 10th, 2006; Jan 10, 06
            elif match.group('startdate2'):
                if len(match.group('startyear2')) == 2:
                    startyear = '20%s' % match.group('startyear2')
                else:
                    startyear = match.group('startyear2')

                startmonth = getNumericalMonth(match.group('startmonth2'))
                if not startmonth:
                    raise EventcalError('invalid_startdate')

                startday = match.group('startday2')

            # yyyymmdd: 20060510, 060510
            elif match.group('startdate3'):
                if len(match.group('startyear3')) == 2:
                    startyear = '20%s' % match.group('startyear3')
                else:
                    startyear = match.group('startyear3')

                startmonth = match.group('startmonth3')
                startday = match.group('startday3')

            else:
                if len(match.group('startdate').strip()) > 0:
                    raise EventcalError('invalid_startdate')
                else:
                    passed = 0

            if passed:
                startdate = '%d/%02d/%02d' % (int(startyear), int(startmonth), int(startday))
            else:
                startdate = ''

        else:
            startdate = ''

        if match.group('starttime'):
            passed = 1
            # 12h with ':': 12:00; 9:00pm
            if match.group('starttime1'):
                starthour = int(match.group('starthour1'))
                if match.group('startminute1'):
                    startmin = int(match.group('startminute1'))
                else:
                    startmin = 0

                if starthour < 12 and match.group('am1').lower().startswith('p'):
                    starthour += 12

            # 24h with ':': 12:00; 23:00
            elif match.group('starttime2'):
                starthour = int(match.group('starthour2'))
                if match.group('startminute2'):
                    startmin = int(match.group('startminute2'))
                else:
                    startmin = 0

            # 24h without ':': 1200; 2300
            elif match.group('starttime3'):
                starthour = int(match.group('starthour3'))
                if match.group('startminute3'):
                    startmin = int(match.group('startminute3'))
                else:
                    startmin = 0

            # 12h without ':': 1200; 0900pm
            elif match.group('starttime4'):

                starthour = int(match.group('starthour4'))
                if match.group('startminute4'):
                    startmin = int(match.group('startminute4'))
                else:
                    startmin = 0

                if starthour < 12 and match.group('am4').lower().startswith('p'):
                    starthour += 12

            else:
                if len(match.group('starttime').strip()) > 0:
                    raise EventcalError('invalid_starttime')
                else:
                    passed = 0

            if passed:
                starttime = '%02d:%02d' % (int(starthour), int(startmin))
            else:
                starttime = ''

        else:
            starttime = ''

        if not startdate:
            raise EventcalError('invalid_start')

    else:
        raise EventcalError('pass')

    ##################### retrieve enddate
    match = pattern_enddate.search(detail)

    if match:

        if match.group('enddate'):
            passed = 1
            # yyyy/mm/dd: 2006/05/10; 06/05/10,
            if match.group('enddate1'):
                if len(match.group('endyear1')) == 2:
                    endyear = '20%s' % match.group('endyear1')
                else:
                    endyear = match.group('endyear1')

                endmonth = match.group('endmonth1')
                endday = match.group('endday1')

            # M dd, yyyy: May 10, 2006; Jan 10th, 2006; Jan 10, 06
            elif match.group('enddate2'):
                if len(match.group('endyear2')) == 2:
                    endyear = '20%s' % match.group('endyear2')
                else:
                    endyear = match.group('endyear2')

                endmonth = getNumericalMonth(match.group('endmonth2'))
                if not endmonth:
                    raise EventcalError('invalid_enddate')

                endday = match.group('endday2')

            # yyyymmdd: 20060510, 060510
            elif match.group('enddate3'):
                if len(match.group('endyear3')) == 2:
                    endyear = '20%s' % match.group('endyear3')
                else:
                    endyear = match.group('endyear3')

                endmonth = match.group('endmonth3')
                endday = match.group('endday3')

            else:
                if len(match.group('enddate').strip()) > 0:
                    raise EventcalError('invalid_enddate')
                else:
                    passed = 0

            if passed:
                enddate = '%d/%02d/%02d' % (int(endyear), int(endmonth), int(endday))
            else:
                enddate = ''

        else:
            enddate = ''

        if match.group('endtime'):
            passed = 1
            # 12h with ':': 12:00; 9:00pm
            if match.group('endtime1'):
                endhour = int(match.group('endhour1'))
                if match.group('endminute1'):
                    endmin = int(match.group('endminute1'))
                else:
                    endmin = 0

                if endhour < 12 and match.group('am1').lower() == 'pm':
                    endhour += 12

            # 24h with ':': 12:00; 23:00
            elif match.group('endtime2'):
                endhour = int(match.group('endhour2'))
                if match.group('endminute2'):
                    endmin = int(match.group('endminute2'))
                else:
                    endmin = 0

            # 24h without ':': 1200; 2300
            elif match.group('endtime3'):
                endhour = int(match.group('endhour3'))
                if match.group('endminute3'):
                    endmin = int(match.group('endminute3'))
                else:
                    endmin = 0

            # 12h without ':': 1200; 0900pm
            elif match.group('endtime4'):

                endhour = int(match.group('endhour4'))
                if match.group('endminute4'):
                    endmin = int(match.group('endminute4'))
                else:
                    endmin = 0

                if endhour < 12 and match.group('am4').lower() == 'pm':
                    endhour += 12

            else:
                if len(match.group('endtime').strip()) > 0:
                    raise EventcalError('invalid_endtime')
                else:
                    passed = 0

            if passed:
                endtime = '%02d:%02d' % (int(endhour), int(endmin))
            else:
                endtime = ''

        else:
            endtime = ''

        if not (enddate or endtime):
            raise EventcalError('invalid_end')

    else:
        enddate = ''
        endtime = ''


    ##################### retrieve bgcolor
    match = pattern_bgcolor.search(detail)

    if match:
        if match.group('bgcolor'):
            bgcolor = match.group('bgcolor')
        else:
            errormsgcode('invalid_bgcolor')
            bgcolor = ''

    else:
        bgcolor = ''

    ##################### retrieve label
    match = pattern_label.search(detail)

    if match:
        if match.group('name'):
            label = match.group('name')
        else:
            errormsgcode('invalid_label')
            label = ''

    else:
        label = ''

    ##################### retrieve description
    match = pattern_description.search(detail)

    if match:
        if match.group('description'):
            description = match.group('description')
        else:
            errormsgcode('empty_description')
            description = ''
    else:
        description = ''

    ##################### retrieve recurrence
    match = pattern_recur.search(detail)

    if match:

        if match.group('recur_freq') and match.group('recur_type'):

            if match.group('recur_freq') == 'last':
                if match.group('recur_type') == 'weekday':
                    recur_freq = -1
                    recur_type = match.group('recur_type')
                    recur_until = match.group('recur_until')
                else:
                    recur_freq = 0
                    recur_type = ''
                    recur_until = ''

            else:
                recur_freq = int(match.group('recur_freq'))
                recur_type = match.group('recur_type')

                if match.group('recur_until_req'):
                    if match.group('recur_until'):
                        # yyyy/mm/dd: 2006/05/10; 06/05/10,
                        if match.group('enddate1'):
                            if len(match.group('endyear1')) == 2:
                                endyear = '20%s' % match.group('endyear1')
                            else:
                                endyear = match.group('endyear1')

                            endmonth = match.group('endmonth1')
                            endday = match.group('endday1')

                        # M dd, yyyy: May 10, 2006; Jan 10th, 2006; Jan 10, 06
                        elif match.group('enddate2'):
                            if len(match.group('endyear2')) == 2:
                                endyear = '20%s' % match.group('endyear2')
                            else:
                                endyear = match.group('endyear2')

                            endmonth = getNumericalMonth(match.group('endmonth2'))
                            if not endmonth:
                                raise EventcalError('invalid_recur_until')

                            endday = match.group('endday2')

                        # yyyymmdd: 20060510, 060510
                        elif match.group('enddate3'):
                            if len(match.group('endyear3')) == 2:
                                endyear = '20%s' % match.group('endyear3')
                            else:
                                endyear = match.group('endyear3')

                            endmonth = match.group('endmonth3')
                            endday = match.group('endday3')

                        else:
                            raise EventcalError('invalid_recur_until')

                        recur_until = '%d/%02d/%02d' % (int(endyear), int(endmonth), int(endday))

                    else:
                        raise EventcalError('invalid_recur_until')

                else:
                    recur_until = ''

        else:
            raise EventcalError('invalid_recur')

    else:
        recur_freq = 0
        recur_type = ''
        recur_until = ''

    # check validity of each fields

    if (starttime or endtime):
        if not endtime:
            endtime = starttime
        elif not starttime:
            raise EventcalError('need_starttime')


    # if no time, it's 1-day event
    if not enddate:
        enddate = startdate

    try:
        syear, smonth, sday = getdatefield(startdate)
    except (TypeError, ValueError):
        raise EventcalError('invalid_startdate')

    try:
        eyear, emonth, eday = getdatefield(enddate)
    except (TypeError, ValueError):
        raise EventcalError('invalid_enddate')

    if datetime.date(syear, smonth, sday) > datetime.date(eyear, emonth, eday):
        raise EventcalError('enddate_precede')

    # format date
    startdate = formatDate(syear, smonth, sday)
    enddate = formatDate(eyear, emonth, eday)

    if (starttime and endtime):
        try:
            shour, smin = gettimefield(starttime)
        except (TypeError, ValueError):
            raise EventcalError('invalid_starttime')

        try:
            ehour, emin = gettimefield(endtime)
        except (TypeError, ValueError):
            raise EventcalError('invalid_endtime')

        if startdate == enddate:
            if datetime.time(shour, smin) > datetime.time(ehour, emin):
                raise EventcalError('endtime_precede')

        # format time
        starttime = u'%02d%02d' %(shour, smin)
        endtime = u'%02d%02d' %(ehour, emin)

    # check recurrent data
    event_len = diffday(startdate, enddate)
    if recur_freq:

        if recur_type == 'day':
            if event_len > int(recur_freq):
                raise EventcalError('len_recur_int')

        elif recur_type == 'week':
            if event_len > int(recur_freq) * 7:
                raise EventcalError('len_recur_int')

        elif recur_type == 'weekday':
            if event_len > 25:
                raise EventcalError('len_recur_int')

        elif recur_type == 'month':
            if event_len > int(recur_freq) * 25:
                raise EventcalError('len_recur_int')

        elif recur_type == 'year':
            if event_len > int(recur_freq) * 365:
                raise EventcalError('len_recur_int')

        if recur_until:
            try:
                ryear, rmonth, rday = getdatefield(recur_until)
            except (TypeError, ValueError):
                raise EventcalError('invalid_recur_until')

            recur_until = formatDate(ryear, rmonth, rday)

            if int(recur_until) < int(enddate):
                raise EventcalError('recur_until_precede')

    return startdate, starttime, enddate, endtime, bgcolor, label, description, recur_freq, recur_type, recur_until


def converttext(targettext):
    """ Converts some special characters of html to plain-text style """
    # What else to handle?

    targettext = targettext.replace(u'&', '&amp')
    targettext = targettext.replace(u'>', '&gt;')
    targettext = targettext.replace(u'<', '&lt;')
    targettext = targettext.replace(u'\n', '<br>')
    targettext = targettext.replace(u'"', '&quot;')
    targettext = targettext.replace(u'\t', '&nbsp;&nbsp;&nbsp;&nbsp')
    targettext = targettext.replace(u'  ', '&nbsp;&nbsp;')

    return targettext


# monthly view
def showeventcalendar(year, month):

    debug('Show Calendar: Monthly View')

    request = Globs.request
    formatter = Globs.formatter
    _ = request.getText

    wkend = Globs.wkend
    months= Globs.months
    wkdays = Globs.wkdays

    # get the calendar
    monthcal = calendar.monthcalendar(year, month)

    # shows current year & month
    html_header_curyearmonth = calhead_yearmonth(year, month, 'head_yearmonth')

    r7 = range(7)

    # shows header of week days
    html_header_weekdays = []

    for wkday in r7:
        wday = _(wkdays[wkday])
        html_header_weekdays.append( calhead_weekday(wday, 'head_weekday') )
    html_header_weekdays = '    <tr>\r\n%s\r\n</tr>\r\n' % u'\r\n'.join(html_header_weekdays)

    # pending events for next row
    next_pending = []

    # gets previous, next month
    day_delta = datetime.timedelta(days=-1)
    cur_month = datetime.date(year, month, 1)
    prev_month = cur_month + day_delta

    day_delta = datetime.timedelta(days=15)
    cur_month_end = datetime.date(year, month, 25)
    next_month = cur_month_end + day_delta

    prev_monthcal = calendar.monthcalendar(prev_month.year, prev_month.month)
    next_monthcal = calendar.monthcalendar(next_month.year, next_month.month)

    # shows days
    html_week_rows = []

    # set ranges of events
    datefrom = u'%04d%02d21' % (prev_month.year, prev_month.month)
    dateto = u'%04d%02d06' % (next_month.year, next_month.month)

    # read all the events
    events, cal_events, labels = loadEvents(datefrom, dateto)

    #debug(u'  events: %s' % events)
    #debug(u'  cal_events: %s' % cal_events)

    for week in monthcal:

        # day head rows
        html_headday_cols = []
        html_events_rows = []

        for wkday in r7:

            day = week[wkday]

            if not day:
                if week == monthcal[0]:
                    nb_day = prev_monthcal[-1][wkday]
                else:
                    nb_day = next_monthcal[0][wkday]

                html_headday_cols.append( calhead_day_nbmonth(nb_day) )
            else:
                html_headday_cols.append( calhead_day(year, month, day, wkday) )

        html_headday_row = '    <tr>\r\n%s\r\n</tr>\r\n' % u'\r\n'.join(html_headday_cols)
        html_week_rows.append(html_headday_row)

        # dummy rows
        html_headdummy_cols = []

        for wkday in r7:
            day = week[wkday]
            if not day:
                html_headdummy_cols.append( calshow_blankbox('head_dummy_nbmonth') )
            else:
                html_headdummy_cols.append( calshow_blankbox('head_dummy') )

        html_headdummy_cols = u'\r\n'.join(html_headdummy_cols)
        html_week_rows.append(' <tr>\r\n%s </tr>\r\n' % html_headdummy_cols)

        # pending events for next row
        pending = next_pending
        next_pending = []

        # show events
        while 1:
            event_left = 7
            colspan = -1
            html_events_cols = []

            for wkday in r7:

                day = week[wkday]

                if not day:
                    if week == monthcal[0]:
                        cur_date = formatDate(prev_month.year, prev_month.month, prev_monthcal[-1][wkday])
                    else:
                        cur_date = formatDate(next_month.year, next_month.month, next_monthcal[0][wkday])
                else:
                    cur_date = formatDate(year, month, day)

                # if an event is already displayed with colspan
                if colspan > 0:
                    colspan -= 1
                    if cal_events.has_key(cur_date) and lastevent in cal_events[cur_date]:
                        cal_events[cur_date].remove(lastevent)

                    continue

                # if there is any event for this date
                if cal_events.has_key(cur_date):
                    if len(cal_events[cur_date]) > 0:

                        # if there is any pending event in the previous week
                        if wkday == 0 and len(pending) > 0:
                            todo_event_id = pending.pop(0)
                            if todo_event_id in cal_events[cur_date]:
                                cur_event = events[todo_event_id]
                                temp_len = diffday(cur_date, cur_event['enddate']) + 1

                                # calculate colspan value
                                if (7-wkday) < temp_len:
                                    colspan = 7 - wkday
                                    next_pending.append(cur_event['id'])
                                    html_events_cols.append( calshow_eventbox(cur_event, colspan, 'append_pending', cur_date) )

                                else:
                                    colspan = temp_len
                                    html_events_cols.append( calshow_eventbox(cur_event, colspan, 'append', cur_date) )


                                cal_events[cur_date].remove(todo_event_id)

                                colspan -= 1
                                lastevent = todo_event_id
                            else:
                                debug('Warning: no such event in cal_events')

                            continue

                        # if there is no pending event in the previous week, start a new event
                        event_found = 0
                        for e_id in cal_events[cur_date]:

                            # if the start date of the event is current date
                            if events[e_id]['startdate'] == cur_date:

                                cur_event = events[cal_events[cur_date].pop(cal_events[cur_date].index(e_id))]

                                # calculate colspan value
                                if (7-wkday) < cur_event['date_len']:
                                    colspan = 7 - wkday
                                    next_pending.append(cur_event['id'])
                                    html_events_cols.append( calshow_eventbox(cur_event, colspan, 'pending', cur_date) )

                                else:
                                    colspan = cur_event['date_len']
                                    html_events_cols.append( calshow_eventbox(cur_event, colspan, '', cur_date) )

                                colspan -= 1
                                lastevent = cur_event['id']
                                event_found = 1
                                break

                            # if the start date of the event is NOT current date
                            else:

                                # pending event from previous month
                                if wkday == 0 and week == monthcal[0]:

                                    cur_event = events[cal_events[cur_date].pop(0)]
                                    temp_len = diffday(cur_date, cur_event['enddate']) + 1

                                    # calculate colspan value
                                    if (7-wkday) < temp_len:
                                        colspan = 7 - wkday
                                        next_pending.append(cur_event['id'])
                                        html_events_cols.append( calshow_eventbox(cur_event, colspan, 'append_pending', cur_date) )
                                    else:
                                        colspan = temp_len
                                        html_events_cols.append( calshow_eventbox(cur_event, colspan, 'append', cur_date) )

                                    colspan -= 1
                                    lastevent = cur_event['id']
                                    event_found = 1
                                    break

                        # if there is no event to start
                        if not event_found:
                            if not day:
                                html_events_cols.append( calshow_blankbox('cal_nbmonth') )
                            else:
                                html_events_cols.append( calshow_blankbox('cal_noevent') )
                            event_left -= 1

                    else:
                        if not day:
                            html_events_cols.append( calshow_blankbox('cal_nbmonth') )
                        else:
                            html_events_cols.append( calshow_blankbox('cal_noevent') )

                        event_left -= 1

                # if there is NO event for this date
                else:
                    if not day:
                        html_events_cols.append( calshow_blankbox('cal_nbmonth') )
                    else:
                        html_events_cols.append( calshow_blankbox('cal_noevent') )

                    event_left -= 1

            # if no event for this entry
            if not event_left:
                # ignore the previous entry
                break
            else:
                html_events_rows.append(' <tr>\r\n%s </tr>\r\n' % u'\r\n'.join(html_events_cols))

        # show dummy blank slots for week height
        left_blank_rows = 2 - len(html_events_rows)

        # remove the followings
        if left_blank_rows > 0 and 0:
            for i in range(left_blank_rows):
                html_events_cols = []
                for wkday in r7:
                    day = week[wkday]
                    if not day:
                        html_events_cols.append( calshow_blankbox('cal_nbmonth') )
                    else:
                        html_events_cols.append( calshow_blankbox('cal_noevent') )

                html_events_rows.append(' <tr>\r\n%s </tr>\r\n' % u'\r\n'.join(html_events_cols))


        # close the week slots
        html_events_cols = []
        for wkday in r7:
            day = week[wkday]
            if not day:
                html_events_cols.append( calshow_blankbox('cal_last_nbmonth') )
            else:
                html_events_cols.append( calshow_blankbox('cal_last_noevent') )

        html_events_rows.append(' <tr>\r\n%s </tr>\r\n' % u'\r\n'.join(html_events_cols))

        html_events_rows = u'\r\n'.join(html_events_rows)
        html_week_rows.append(html_events_rows)

    html_calendar_rows = u'\r\n'.join(html_week_rows)

    html_cal_table = [
        u'\r\n<div id="eventcalendar">',
        u'<table class="eventcalendar" %s>' % Params.monthlywidth,
        u'%s' % html_header_curyearmonth,
        u'%s' % html_header_weekdays,
        u'%s' % html_calendar_rows,
        u'</table>',
        u'</div>',
        ]
    html_cal_table = u'\r\n'.join(html_cal_table)

    return html_cal_table


def showdailyeventcalendar(year, month, day):
    """ Daily view """

    debug('Show Calendar: Daily View')

    request = Globs.request
    formatter = Globs.formatter
    _ = request.getText

    wkend = Globs.wkend
    months= Globs.months
    wkdays = Globs.wkdays

    cur_date = formatDate(year, month, day)

    # gets previous, next month
    day_delta = datetime.timedelta(days=-1)
    cur_month = datetime.date(year, month, 1)
    prev_month = cur_month + day_delta

    day_delta = datetime.timedelta(days=15)
    cur_month_end = datetime.date(year, month, 25)
    next_month = cur_month_end + day_delta

    # set ranges of events
    datefrom = u'%04d%02d21' % (prev_month.year, prev_month.month)
    dateto = u'%04d%02d06' % (next_month.year, next_month.month)

    # read all the events
    events, cal_events, labels = loadEvents(datefrom, dateto)

    #debug(u'  events: %s' % events)
    #debug(u'  cal_events: %s' % cal_events)

    # calculates hour_events
    hour_events = {}

    if cal_events.has_key(cur_date):
        for e_id in cal_events[cur_date]:
            cur_event = events[e_id]

            if cur_event['date_len'] == 1 and cur_event['time_len'] > 0:
                start_hour, start_min = gettimefield(cur_event['starttime'])

                if not hour_events.has_key(start_hour):
                    hour_events[start_hour] = []

                hour_events[start_hour].append(e_id)

    #debug(u'hour_events: %s' % hour_events)

    # in-day events
    html_calendar_rows = []
    html_hour_cols = {}

    slot_pending = {}
    max_num_slots = 0
    hour_max_slots = {}
    block_slots = []

    start_hour_index = 0

    r24 = range(24)

    for hour_index in r24:

        html_hour_cols[hour_index] = []
        hour_max_slots[hour_index] = 1
        html_hour_cols[hour_index].append ( calshow_daily_hourhead(hour_index) )

        if len(slot_pending) > 0 or hour_events.has_key(hour_index):

            #debug('start: hour_index = %d, slot_pending = %s' % (hour_index, slot_pending))
            if len(slot_pending) == 0:
                if max_num_slots < 1:
                    max_num_slots = 1

                for hour_lines in range(start_hour_index, hour_index):
                    hour_max_slots[hour_lines] = max_num_slots

                #debug('block ended: %d ~ %d, max=%d' % (start_hour_index, hour_index-1, max_num_slots))

                block_slots.append(max_num_slots)

                max_num_slots = 0
                start_hour_index = hour_index

            for slot_index in range(max_num_slots):
                if slot_pending.has_key(slot_index) and slot_pending[slot_index] > 0:
                    if slot_pending[slot_index] == 1:
                        del slot_pending[slot_index]
                    else:
                        slot_pending[slot_index] -= 1
                    html_hour_cols[hour_index].append ( '' )

                else:
                    if hour_events.has_key(hour_index) and len(hour_events[hour_index]) > 0:
                        e_id = hour_events[hour_index][0]
                        cur_event = events[hour_events[hour_index].pop(hour_events[hour_index].index(e_id))]
                        html_hour_cols[hour_index].append ( calshow_daily_eventbox(cur_event) )
                        slot_pending[slot_index] = cur_event['time_len'] - 1
                    else:
                        if not ((len(slot_pending) > 0 and slot_index > max(slot_pending.keys())) or len(slot_pending) == 0):
                            html_hour_cols[hour_index].append ( calshow_blankeventbox() )

            if hour_events.has_key(hour_index):
                for tmp_cnt in range(len(hour_events[hour_index])):
                    e_id = hour_events[hour_index][0]
                    cur_event = events[hour_events[hour_index].pop(hour_events[hour_index].index(e_id))]
                    html_hour_cols[hour_index].append ( calshow_daily_eventbox(cur_event) )
                    slot_pending[max_num_slots] = cur_event['time_len'] - 1
                    if slot_pending[max_num_slots] == 0:
                        del slot_pending[max_num_slots]
                    max_num_slots += 1

        else:
            html_hour_cols[hour_index].append ( calshow_blankeventbox() )
            #hour_max_slots[hour_index] = 1

            if max_num_slots < 1:
                max_num_slots = 1

            for hour_lines in range(start_hour_index, hour_index):
                hour_max_slots[hour_lines] = max_num_slots

            #debug('block ended: %d ~ %d, max=%d' % (start_hour_index, hour_index-1, max_num_slots))

            block_slots.append(max_num_slots)

            max_num_slots = 0
            start_hour_index = hour_index


        #debug('end: hour_index = %d, slot_pending = %s' % (hour_index, slot_pending))

    if max_num_slots < 1:
        max_num_slots = 1

    for hour_lines in range(start_hour_index, 24):
        hour_max_slots[hour_lines] = max_num_slots

    #debug('block ended: %d ~ %d, max=%d' % (start_hour_index, 23, max_num_slots))

    block_slots.append(max_num_slots)

    #debug('hour_max_slots: %s' % hour_max_slots)


    # calculates global colspan
    if len(block_slots):
        global_colspan = LCM(block_slots)
    else:
        global_colspan = 1

    for hour_index in r24:

        colspan = global_colspan / hour_max_slots[hour_index]
        width = 96 / hour_max_slots[hour_index]

        left_slots = hour_max_slots[hour_index] - (len(html_hour_cols[hour_index]) - 1)

        if left_slots > 0:
            #debug('appending left %d slots: %d' % (left_slots, hour_index))
            html_hour_cols[hour_index].append ( calshow_blankeventbox2( left_slots * colspan, left_slots * width ) )

        html_cols = u'\r\n'.join(html_hour_cols[hour_index]) % {'colspan': colspan, 'width': u'%d%%' % width}
        html_cols = u'<tr>%s</tr>\r\n' % html_cols

        html_calendar_rows.append (html_cols)

    html_calendar_rows = u'\r\n'.join(html_calendar_rows)

    # shows current year & month
    html_header_curyearmonthday = calhead_yearmonthday(year, month, day, 'head_yearmonth', global_colspan)

    # one-day long events
    html_oneday_rows = []

    #debug('before cal_events[cur_date] = %s' % cal_events[cur_date])

    if cal_events.has_key(cur_date):
        if len(cal_events[cur_date]) > 0:
            for e_id in cal_events[cur_date]:
                #debug('before cal_events[cur_date] = %s' % cal_events[cur_date])
                #debug('test events[%s] = %s' % (e_id, events[e_id]))
                if events[e_id]['time_len'] <= 0 or events[e_id]['date_len'] > 1:
                    #cur_event = events[cal_events[cur_date].pop(cal_events[cur_date].index(e_id))]
                    cur_event = events[e_id]

                    if cur_event['startdate'] == cur_date:
                        if cur_event['enddate'] == cur_date:
                            str_status = ''
                        else:
                            str_status = 'pending'
                    else:
                        if cur_event['enddate'] == cur_date:
                            str_status = 'append'
                        else:
                            str_status = 'append_pending'

                    tmp_html = u'<tr><td width="4%%" style="border-width: 0px; ">&nbsp;</td>%s</tr>' % calshow_daily_eventbox2(cur_event, global_colspan, str_status, cur_date)
                    html_oneday_rows.append( tmp_html )

                #debug('after cal_events[cur_date] = %s' % cal_events[cur_date])
    else:
        tmp_html = u'<tr><td width="4%%" style="border-width: 0px; ">&nbsp;</td>%s</tr>' % calshow_blankbox2('cal_daily_noevent', global_colspan)
        html_oneday_rows.append( tmp_html )

    #debug('after cal_events[cur_date] = %s' % cal_events[cur_date])
    #debug('html_oneday_rows = %s' % html_oneday_rows)

    html_oneday_rows = u'\r\n'.join(html_oneday_rows)


    html_cal_table = [
        u'\r\n<div id="eventcalendar">',
        u'<table class="eventcalendar" %s>' % Params.dailywidth,
        u'<table border="0">',
        u'%s' % html_header_curyearmonthday,
        u'%s' % html_oneday_rows,
        u'%s' % html_calendar_rows,
        u'</table>',
        u'</td></tr>',
        u'</div>',
        ]
    html_cal_table = u'\r\n'.join(html_cal_table)

    return html_cal_table


def showweeklyeventcalendar(year, month, day):

    """ Weekly view """

    debug('Show Calendar: Weekly View')

    request = Globs.request
    formatter = Globs.formatter
    _ = request.getText

    wkend = Globs.wkend
    months= Globs.months
    wkdays = Globs.wkdays

    cur_date = formatDate(year, month, day)

    # gets previous, next month
    day_delta = datetime.timedelta(days=-1)
    cur_month = datetime.date(year, month, 1)
    prev_month = cur_month + day_delta

    day_delta = datetime.timedelta(days=15)
    cur_month_end = datetime.date(year, month, 25)
    next_month = cur_month_end + day_delta

    # set ranges of events
    datefrom = u'%04d%02d21' % (prev_month.year, prev_month.month)
    dateto = u'%04d%02d06' % (next_month.year, next_month.month)

    # read all the events
    events, cal_events, labels = loadEvents(datefrom, dateto)

    #debug(u'  events: %s' % events)
    #debug(u'  cal_events: %s' % cal_events)

    # calculates hour_events
    hour_events = {}

    first_date_week = getFirstDateOfWeek(year, month, day)


    for dayindex in range(7):
        hour_events[dayindex] = {}

        cur_date = first_date_week + datetime.timedelta(dayindex)
        cur_date = formatDate(cur_date.year, cur_date.month, cur_date.day)

        if cal_events.has_key(cur_date):
            for e_id in cal_events[cur_date]:
                cur_event = events[e_id]

                if cur_event['date_len'] == 1 and cur_event['time_len'] > 0:
                    start_hour, start_min = gettimefield(cur_event['starttime'])

                    if not hour_events[dayindex].has_key(start_hour):
                        hour_events[dayindex][start_hour] = []

                    hour_events[dayindex][start_hour].append(e_id)

    #debug(u'hour_events: %s' % hour_events)

    # in-day events
    html_calendar_rows = []
    html_hour_cols = {}

    slot_pending = {}
    max_num_slots = {}
    hour_max_slots = {}
    block_slots = {}

    start_hour_index = {}

    r24 = range(24)

    for hour_index in r24:

        html_hour_cols[hour_index] = {}
        hour_max_slots[hour_index] = {}

        #html_hour_cols[hour_index].append ( calshow_daily_hourhead(hour_index) )

        for dayindex in range(7):

            if not max_num_slots.has_key(dayindex):
                max_num_slots[dayindex] = 0

            if not slot_pending.has_key(dayindex):
                slot_pending[dayindex] = {}

            if not start_hour_index.has_key(dayindex):
                start_hour_index[dayindex] = 0

            if not block_slots.has_key(dayindex):
                block_slots[dayindex] = []

            html_hour_cols[hour_index][dayindex] = []
            hour_max_slots[hour_index][dayindex] = 1

            if len(slot_pending[dayindex]) > 0 or hour_events[dayindex].has_key(hour_index):

                #debug('start: hour_index = %d, slot_pending = %s' % (hour_index, slot_pending[dayindex]))
                if len(slot_pending[dayindex]) == 0:
                    if max_num_slots[dayindex] < 1:
                        max_num_slots[dayindex] = 1

                    for hour_lines in range(start_hour_index[dayindex], hour_index):
                        hour_max_slots[hour_lines][dayindex] = max_num_slots[dayindex]

                    #debug('block ended: %d ~ %d, max=%d' % (start_hour_index[dayindex], hour_index-1, max_num_slots[dayindex]))

                    block_slots[dayindex].append(max_num_slots[dayindex])

                    max_num_slots[dayindex] = 0
                    start_hour_index[dayindex] = hour_index

                for slot_index in range(max_num_slots[dayindex]):
                    if slot_pending[dayindex].has_key(slot_index) and slot_pending[dayindex][slot_index] > 0:
                        if slot_pending[dayindex][slot_index] == 1:
                            del slot_pending[dayindex][slot_index]
                        else:
                            slot_pending[dayindex][slot_index] -= 1
                        html_hour_cols[hour_index][dayindex].append ( '' )

                    else:
                        if hour_events[dayindex].has_key(hour_index) and len(hour_events[dayindex][hour_index]) > 0:
                            e_id = hour_events[dayindex][hour_index][0]
                            cur_event = events[hour_events[dayindex][hour_index].pop(hour_events[dayindex][hour_index].index(e_id))]
                            html_hour_cols[hour_index][dayindex].append ( calshow_weekly_eventbox(cur_event) )
                            slot_pending[dayindex][slot_index] = cur_event['time_len'] - 1
                        else:
                            if not ((len(slot_pending[dayindex]) > 0 and slot_index > max(slot_pending[dayindex].keys())) or len(slot_pending[dayindex]) == 0):
                                html_hour_cols[hour_index][dayindex].append ( calshow_blankeventbox() )

                if hour_events[dayindex].has_key(hour_index):
                    for tmp_cnt in range(len(hour_events[dayindex][hour_index])):
                        e_id = hour_events[dayindex][hour_index][0]
                        cur_event = events[hour_events[dayindex][hour_index].pop(hour_events[dayindex][hour_index].index(e_id))]
                        html_hour_cols[hour_index][dayindex].append ( calshow_weekly_eventbox(cur_event) )
                        slot_pending[dayindex][max_num_slots[dayindex]] = cur_event['time_len'] - 1
                        if slot_pending[dayindex][max_num_slots[dayindex]] == 0:
                            del slot_pending[dayindex][max_num_slots[dayindex]]
                        max_num_slots[dayindex] += 1

            else:
                html_hour_cols[hour_index][dayindex].append ( calshow_blankeventbox() )
                #hour_max_slots[hour_index][dayindex] = 1

                if max_num_slots[dayindex] < 1:
                    max_num_slots[dayindex] = 1

                for hour_lines in range(start_hour_index[dayindex], hour_index):
                    hour_max_slots[hour_lines][dayindex] = max_num_slots[dayindex]

                #debug('block ended: %d ~ %d, max=%d' % (start_hour_index[dayindex], hour_index-1, max_num_slots[dayindex]))

                block_slots[dayindex].append(max_num_slots[dayindex])

                max_num_slots[dayindex] = 0
                start_hour_index[dayindex] = hour_index

    global_colspan = {}
    header_colspan = 0

    for dayindex in range(7):
        if max_num_slots[dayindex] < 1:
            max_num_slots[dayindex] = 1

        for hour_lines in range(start_hour_index[dayindex], 24):
            hour_max_slots[hour_lines][dayindex] = max_num_slots[dayindex]

        block_slots[dayindex].append(max_num_slots[dayindex])

        # calculates global colspan
        if len(block_slots[dayindex]):
            global_colspan[dayindex] = LCM(block_slots[dayindex])
        else:
            global_colspan[dayindex] = 1

        header_colspan += global_colspan[dayindex]


    for hour_index in r24:

        html_cols_days = []

        for dayindex in range(7):

            colspan = global_colspan[dayindex] / hour_max_slots[hour_index][dayindex]
            width = (100 - 2) / 7 / hour_max_slots[hour_index][dayindex]

            left_slots = hour_max_slots[hour_index][dayindex] - len(html_hour_cols[hour_index][dayindex])

            if left_slots > 0:
                #debug('appending left %d slots: %d' % (left_slots, hour_index))
                html_hour_cols[hour_index][dayindex].append ( calshow_blankeventbox2( left_slots * colspan, left_slots * width ) )

            html_cols = u'\r\n'.join(html_hour_cols[hour_index][dayindex]) % {'colspan': colspan, 'width': u'%d%%' % width}
            html_cols_days.append(html_cols)

        html_cols_collected = u'\r\n'.join(html_cols_days)
        html_cols = u'<tr>%s\r\n%s</tr>\r\n' % (calshow_weekly_hourhead(hour_index), html_cols_collected)

        html_calendar_rows.append (html_cols)

    html_calendar_rows = u'\r\n'.join(html_calendar_rows)

    # shows current year & month
    html_header_curyearmonthday = calhead_yearmonthday2(year, month, day, 'head_yearmonth', header_colspan)

    # one-day long events
    html_oneday_rows = {}

    #debug('before cal_events[cur_date] = %s' % cal_events[cur_date])

    #first_date_week = getFirstDateOfWeek(year, month, day)

    html_oneday_rows = []

    while 1:
        html_oneday_cols = []
        cnt_blank_cols = 0
        pending = -1

        for dayindex in range(7):

            if pending > 0:
                pending -= 1
                html_oneday_cols.append('')
                continue
            else:
                pending = -1

            cur_date = first_date_week + datetime.timedelta(dayindex)
            cur_date = formatDate(cur_date.year, cur_date.month, cur_date.day)

            if cal_events.has_key(cur_date) and len(cal_events[cur_date]) > 0:

                tmpcount = len(cal_events[cur_date])
                for tmp_index in range(tmpcount):
                    cur_event = events[cal_events[cur_date].pop(0)]

                    #debug('event poped out at %s: %s' % (cur_date, cur_event))

                    if (cur_event['startdate'] <= cur_date and dayindex == 0) or cur_event['startdate'] == cur_date:
                        if cur_event['time_len'] <= 0 or cur_event['date_len'] > 1:

                            temp_len = diffday(cur_date, cur_event['enddate']) + 1

                            if cur_event['startdate'] == cur_date:
                                if temp_len <= 7 - dayindex:
                                    str_status = ''
                                else:
                                    str_status = 'pending'
                            else:
                                if temp_len <= 7 - dayindex:
                                    str_status = 'append'
                                else:
                                    str_status = 'append_pending'

                            if temp_len > 7 - dayindex:
                                temp_len = 7 - dayindex

                            pending = temp_len - 1

                            tmp_global_colspan = 0
                            for tmp_index in range(dayindex, dayindex+temp_len):
                                tmp_global_colspan += global_colspan[tmp_index]

                            #debug('event appended at %s with pending=%d: %s' % (cur_date, pending, cur_event))

                            html_oneday_cols.append( calshow_weekly_eventbox2(cur_event, tmp_global_colspan, 14 * temp_len, str_status, cur_date) )
                            break

                if pending < 0:
                    html_oneday_cols.append( calshow_blankbox2('cal_weekly_noevent', global_colspan[dayindex]) )
                    cnt_blank_cols += 1

            else:
                html_oneday_cols.append( calshow_blankbox2('cal_weekly_noevent', global_colspan[dayindex]) )
                cnt_blank_cols += 1

        if cnt_blank_cols >= 7:
            if len(html_oneday_rows) == 0:
                html_oneday_cols = u'<tr><td width="2%%" style="border-width: 0px; ">&nbsp;</td>%s</tr>' % u'\r\n'.join(html_oneday_cols)
                html_oneday_rows.append (html_oneday_cols)
            break
        else:
            html_oneday_cols = u'<tr><td width="2%%" style="border-width: 0px; ">&nbsp;</td>%s</tr>' % u'\r\n'.join(html_oneday_cols)
            html_oneday_rows.append (html_oneday_cols)

    html_date_rows = []

    for dayindex in range(7):
        cur_date = first_date_week + datetime.timedelta(dayindex)
        html_date_rows.append(calhead_weeklydate(cur_date.year, cur_date.month, cur_date.day, global_colspan[dayindex]))

    html_date_rows = u'<tr><td width="2%%" style="border-width: 0px; ">&nbsp;</td>%s</tr>' % u'\r\n'.join(html_date_rows)

    html_oneday_rows = u'\r\n'.join(html_oneday_rows)

    html_cal_table = [
        u'\r\n<div id="eventcalendar">',
        u'<table class="eventcalendar" %s>' % Params.weeklywidth,
        u'<table border="0">',
        u'%s' % html_header_curyearmonthday,
        u'%s' % html_date_rows,
        u'%s' % html_oneday_rows,
        u'%s' % html_calendar_rows,
        u'</table>',
        u'</td></tr>',
        u'</div>',
        ]
    html_cal_table = u'\r\n'.join(html_cal_table)

    return html_cal_table


def showsimpleeventcalendar(year, month):

    """ Simple view """

    debug('Show Calendar: Simple View')

    request = Globs.request
    formatter = Globs.formatter
    _ = request.getText
    monthstyle_us = Globs.month_style_us

    wkend = Globs.wkend
    months= Globs.months
    wkdays = Globs.wkdays

    # get the calendar
    monthcal = calendar.monthcalendar(year, month)

    # shows current year & month
    html_header_curyearmonth = calhead_yearmonth(year, month, 'simple_yearmonth')

    r7 = range(7)

    # shows header of week days
    html_header_weekdays = []

    for wkday in r7:
        wday = wkdays[wkday]
        html_header_weekdays.append( calhead_weekday(wday, 'simple_weekday') )
    html_header_weekdays = '    <tr>\r\n%s\r\n</tr>\r\n' % u'\r\n'.join(html_header_weekdays)

    # gets previous, next month
    day_delta = datetime.timedelta(days=-1)
    cur_month = datetime.date(year, month, 1)
    prev_month = cur_month + day_delta

    day_delta = datetime.timedelta(days=15)
    cur_month_end = datetime.date(year, month, 25)
    next_month = cur_month_end + day_delta

    prev_monthcal = calendar.monthcalendar(prev_month.year, prev_month.month)
    next_monthcal = calendar.monthcalendar(next_month.year, next_month.month)

    # shows days
    html_week_rows = []

    # set ranges of events
    datefrom = u'%04d%02d21' % (prev_month.year, prev_month.month)
    dateto = u'%04d%02d06' % (next_month.year, next_month.month)

    # read all the events
    events, cal_events, labels = loadEvents(datefrom, dateto)

    maketip_js = []

    for week in monthcal:

        # day head rows
        html_headday_cols = []
        html_events_rows = []

        for wkday in r7:

            day = week[wkday]

            if not day:
                if week == monthcal[0]:
                    nb_day = prev_monthcal[-1][wkday]
                else:
                    nb_day = next_monthcal[0][wkday]

                html_headday_cols.append( simple_eventbox(year, month, day, nb_day, 'simple_nb') )
            else:
                cur_date = formatDate(year, month, day)

                if cal_events.has_key(cur_date):
                    html_headday_cols.append( simple_eventbox(year, month, day, wkday, 'simple_event') )

                    if monthstyle_us:
                        tiptitle = u'%s %d, %d' % (months[month-1], day, year)
                    else:
                        tiptitle = u'%d / %02d / %02d' % (year, month, day)

                    date_today = datetime.date( year, month, day )
                    tiptitle = u'%s (%s)' % (tiptitle, _(wkdays[date_today.weekday() - calendar.firstweekday()]))

                    tiptext = []

                    for e_id in cal_events[cur_date]:
                        cur_event = events[e_id]
                        if cur_event['starttime']:
                            time_string = u'(%s:%s)' % (cur_event['starttime'][:2], cur_event['starttime'][2:])
                        else:
                            time_string = ''

                        title = wikiutil.escape(cur_event['title']).replace("'","\\'")
                        description = wikiutil.escape(cur_event['description']).replace("'","\\'")

                        tiptext.append( u'<b>%s</b>%s %s' % (title, time_string, description) )

                    tiptext = u'<br>'.join(tiptext)

                    maketip_js.append("maketip('%s','%s','%s');" % (cur_date, tiptitle, tiptext))
                else:
                    html_headday_cols.append( simple_eventbox(year, month, day, wkday, 'simple_noevent') )

        html_headday_row = '    <tr>\r\n%s\r\n</tr>\r\n' % u'\r\n'.join(html_headday_cols)
        html_week_rows.append(html_headday_row)

    html_calendar_rows = u'\r\n'.join(html_week_rows)

    html_tooltip_result = """\
<script language="JavaScript" type="text/javascript" src="%s/common/js/infobox.js"></script>
<div id="infodiv" style="position:absolute; visibility:hidden; z-index:20; top:-999em; left:0px;"></div>
<script language="JavaScript" type="text/javascript">
<!--
%s
// -->
</script>

""" % (request.cfg.url_prefix, "\n".join(maketip_js))


    html_cal_table = [
        u'\r\n<div id="eventcalendar">',
        u'%s' % html_tooltip_result,
        u'<table class="simplecalendar" %s>' % Params.simplewidth,
        u'%s' % html_header_curyearmonth,
        u'%s' % html_header_weekdays,
        u'%s' % html_calendar_rows,
        u'</table>',
        u'</div>',
        ]
    html_cal_table = u'\r\n'.join(html_cal_table)

    return html_cal_table

def calhead_yearmonth(year, month, headclass):

    """ Show calendar head (year & month) """

    request = Globs.request

    months = Globs.months
    monthstyle_us = Globs.month_style_us
    cal_action = Globs.cal_action
    page_name = Globs.pagename

    page_url = Globs.pageurl

    nextyear, nextmonth = yearmonthplusoffset(year, month, 1)
    prevyear, prevmonth = yearmonthplusoffset(year, month, -1)

    prevlink = u'%s?calaction=%s&caldate=%d%02d%s' % (page_url, cal_action, prevyear, prevmonth, getquerystring(['numcal']) )
    nextlink = u'%s?calaction=%s&caldate=%d%02d%s' % (page_url, cal_action, nextyear, nextmonth, getquerystring(['numcal']))
    curlink = u'%s?calaction=%s&caldate=%d%02d%s' % (page_url, cal_action, year, month, getquerystring(['numcal']))

    if monthstyle_us:
        stryearmonth = u'%s %d' % (months[month-1], year)
        strnextmonth = u'%s %d' % (months[nextmonth-1], nextyear)
        strprevmonth = u'%s %d' % (months[prevmonth-1], prevyear)
    else:
        stryearmonth = u'%d / %02d' % (year, month)
        strnextmonth = u'%d / %02d' % (nextyear, nextmonth)
        strprevmonth = u'%d / %02d' % (prevyear, prevmonth)

    html = [
        u'  <tr>',
        u'      <td class="%s"><a href="%s" title="%s">&lt;</a></td>' % (headclass, prevlink, strprevmonth),
        u'      <td colspan="5" class="%s"><a href="%s" title="Go/Refresh this month">%s</a></td>' % (headclass, curlink, stryearmonth),
        u'      <td class="%s"><a href="%s" title="%s">&gt;</a></td>' % (headclass, nextlink, strnextmonth),
        u'  </tr>',
        ]

    return u'\r\n'.join(html)


def calhead_yearmonthday(year, month, day, headclass, colspan):

    """ Show calendar head (year & month & day) """

    request = Globs.request
    _ = request.getText

    months = Globs.months
    monthstyle_us = Globs.month_style_us
    cal_action = Globs.cal_action
    page_name = Globs.pagename
    wkdays = Globs.wkdays

    page_url = Globs.pageurl

    date_today = datetime.date( year, month, day )
    prevdate = date_today - datetime.timedelta(days=1)
    nextdate = date_today + datetime.timedelta(days=1)

    prevlink = u'%s?calaction=%s&caldate=%d%02d%02d%s' % (page_url, cal_action, prevdate.year, prevdate.month, prevdate.day, getquerystring(['numcal']) )
    nextlink = u'%s?calaction=%s&caldate=%d%02d%02d%s' % (page_url, cal_action, nextdate.year, nextdate.month, nextdate.day, getquerystring(['numcal']))
    curlink = u'%s?calaction=%s&caldate=%d%02d%02d%s' % (page_url, cal_action, year, month, day, getquerystring(['numcal']))

    if monthstyle_us:
        stryearmonth = u'%s %d, %d' % (months[month-1], day, year)
        strnextmonth = u'%s %d, %d' % (months[nextdate.month-1], nextdate.day, nextdate.year)
        strprevmonth = u'%s %d, %d' % (months[prevdate.month-1], prevdate.day, prevdate.year)
    else:
        stryearmonth = u'%d / %02d / %02d' % (year, month, day)
        strnextmonth = u'%d / %02d / %02d' % (nextdate.year, nextdate.month, nextdate.day)
        strprevmonth = u'%d / %02d / %02d' % (prevdate.year, prevdate.month, prevdate.day)

    #stryearmonth = u'%s (%s)' % (stryearmonth, _(wkdays[date_today.weekday()]))
    stryearmonth = u'%s (%s)' % (stryearmonth, _(wkdays[date_today.weekday() - calendar.firstweekday()]))

    html = [
        u'<tr><td width="4%" style="border: none;">&nbsp;</td>',
        u'<td colspan="%d" style="border: none;">' % colspan,
        u'<table width="95%">',
        u'  <tr>',
        u'      <td class="%s"><a href="%s" title="%s">&lt;</a></td>' % (headclass, prevlink, strprevmonth),
        u'      <td class="%s"><a href="%s" title="Go/Refresh this day">%s</a></td>' % (headclass, curlink, stryearmonth),
        u'      <td class="%s"><a href="%s" title="%s">&gt;</a></td>' % (headclass, nextlink, strnextmonth),
        u'  </tr>',
        u'</table>',
        u'</td></tr>',
        ]

    return u'\r\n'.join(html)


def calhead_yearmonthday2(year, month, day, headclass, colspan):

    """ Show calendar head for weekly view (year & month & day) """

    request = Globs.request
    _ = request.getText

    months = Globs.months
    monthstyle_us = Globs.month_style_us
    cal_action = Globs.cal_action
    page_name = Globs.pagename
    wkdays = Globs.wkdays

    page_url = Globs.pageurl

    date_today = datetime.date( year, month, day )
    prevdate = date_today - datetime.timedelta(days=7)
    nextdate = date_today + datetime.timedelta(days=7)

    first_date_week = getFirstDateOfWeek(year, month, day)
    prevdate_f = first_date_week - datetime.timedelta(days=7)
    nextdate_f = first_date_week + datetime.timedelta(days=7)

    last_date_week = first_date_week + datetime.timedelta(days=6)
    prevdate_l = last_date_week - datetime.timedelta(days=7)
    nextdate_l = last_date_week + datetime.timedelta(days=7)

    prevlink = u'%s?calaction=%s&caldate=%d%02d%02d%s' % (page_url, cal_action, prevdate.year, prevdate.month, prevdate.day, getquerystring(['numcal']) )
    nextlink = u'%s?calaction=%s&caldate=%d%02d%02d%s' % (page_url, cal_action, nextdate.year, nextdate.month, nextdate.day, getquerystring(['numcal']))
    curlink = u'%s?calaction=%s&caldate=%d%02d%02d%s' % (page_url, cal_action, year, month, day, getquerystring(['numcal']))

    if monthstyle_us:
        stryearmonth = u'%s %d, %d ~ %s %d, %d' % (months[first_date_week.month-1], first_date_week.day, first_date_week.year, months[last_date_week.month-1], last_date_week.day, last_date_week.year)
        strnextmonth = u'%s %d, %d ~ %s %d, %d' % (months[nextdate_f.month-1], nextdate_f.day, nextdate_f.year, months[nextdate_l.month-1], nextdate_l.day, nextdate_l.year)
        strprevmonth = u'%s %d, %d ~ %s %d, %d' % (months[prevdate_f.month-1], prevdate_f.day, prevdate_f.year, months[prevdate_l.month-1], prevdate_l.day, prevdate_l.year)
    else:
        stryearmonth = u'%d / %02d / %02d ~ %d / %02d / %02d' % (first_date_week.year, first_date_week.month, first_date_week.day, last_date_week.year, last_date_week.month, last_date_week.day)
        strnextmonth = u'%d / %02d / %02d ~ %d / %02d / %02d' % (nextdate_f.year, nextdate_f.month, nextdate_f.day, nextdate_l.year, nextdate_l.month, nextdate_l.day)
        strprevmonth = u'%d / %02d / %02d ~ %d / %02d / %02d' % (prevdate_f.year, prevdate_f.month, prevdate_f.day, prevdate_l.year, prevdate_l.month, prevdate_l.day)

    #stryearmonth = u'%s (%s)' % (stryearmonth, _(wkdays[date_today.weekday() - calendar.firstweekday()]))

    html = [
        u'<tr><td width="2%" style="border: none;">&nbsp;</td>',
        u'<td colspan="%d" style="border: none;">' % colspan,
        u'<table width="95%">',
        u'  <tr>',
        u'      <td class="%s"><a href="%s" title="%s">&lt;</a></td>' % (headclass, prevlink, strprevmonth),
        u'      <td class="%s"><a href="%s" title="Go/Refresh this week">%s</a></td>' % (headclass, curlink, stryearmonth),
        u'      <td class="%s"><a href="%s" title="%s">&gt;</a></td>' % (headclass, nextlink, strnextmonth),
        u'  </tr>',
        u'</table>',
        u'</td></tr>',
        ]

    return u'\r\n'.join(html)


def calhead_weeklydate(year, month, day, colspan):
    """ Show calendar head for weekly view (the date) """

    request = Globs.request
    _ = request.getText

    months = Globs.months
    monthstyle_us = Globs.month_style_us
    cal_action = Globs.cal_action
    page_name = Globs.pagename
    wkdays = Globs.wkdays

    page_url = Globs.pageurl

    date_today = datetime.date( year, month, day )

    if monthstyle_us:
        stryearmonth = u'%s %d' % (months[month-1], day)
    else:
        stryearmonth = u'%02d / %02d' % (month, day)

    stryearmonth = u'%s (%s)' % (stryearmonth, _(wkdays[date_today.weekday() - calendar.firstweekday()]))
    curlink = u'%s?calaction=daily&caldate=%d%02d%02d' % (page_url, year, month, day)

    cyear, cmonth, cday = gettodaydate()
    if cyear == year and cmonth == month and cday == day:
        bgcolor = 'background-color: #FFFFAA;'
    else:
        bgcolor = ''

    if not Params.changeview:
        curlink = '#'

    html = [
        u'<td colspan="%d" style="border-width: 2px; text-align: center; font-size: 9pt; %s">' % (colspan, bgcolor),
        u'<a href="%s">%s</a>' % (curlink, stryearmonth),
        u'</td>',
        ]

    return u'\r\n'.join(html)


def simple_eventbox(year, month, day, wkday, boxclass):
    """ Show days in simple """

    wkend = Globs.wkend
    if wkday == wkend:
        html_text = u'<font color="#aa7744">%s</font>' % day
    else:
        html_text = u'%s' % day

    cyear, cmonth, cday = gettodaydate()

    page_url = Globs.pageurl
    linkkey = u'%d%02d%02d' % (year, month, day)

    curlink = u'%s?calaction=daily&caldate=%d%02d%02d' % (page_url, year, month, day)

    if not Params.changeview:
        curlink = '#'

    curlink = u'<a href="%s" onMouseOver="tip(\'%s\')" onMouseOut="untip()" >%s</a>' % (curlink, linkkey, html_text)

    if boxclass == 'simple_nb':
        html = u'  <td class="%s">&nbsp;</td>\r\n' % boxclass
    else:
        if cyear == year and cmonth == month and cday == day:
            html = u'  <td class="%s_today">%s</td>\r\n' % (boxclass, curlink)
        else:
            html = u'  <td class="%s">%s</td>\r\n' % (boxclass, curlink)

    return html


def calhead_weekday(wday, headclass):
    """ Show weekday """
    if headclass == 'simple_weekday':
        html = u'       <td class="%s">%s</td>\r\n' % (headclass, wday[0])
    else:
        html = u'       <td class="%s">%s</td>\r\n' % (headclass, wday)

    return html


def calhead_day(year, month, day, wkday):
    """ Show days of current month """

    request = Globs.request
    page_name = Globs.pagename
    wkend = Globs.wkend

    if wkday == wkend:
        html_text = u'<font color="#FF3300">%s</font>' % day
    else:
        html_text = u'%s' % day

    page_url = Globs.pageurl
    html_text = u'<a href="%s?calaction=daily&caldate=%d%02d%02d">%s</a>' % (page_url, year, month, day, html_text)

    cyear, cmonth, cday = gettodaydate()

    if (not wkday) and Params.showweeknumber:
        html_text = u'%s <font size="1" color="#aaaaaa"><i>(%d)</i></font>' % (html_text, (int(datetime.date(year, month, day).strftime('%W')) + 1))

    if cyear == year and cmonth == month and cday == day:
        html = u'  <td class="head_day_today">&nbsp;%s</td>\r\n' % html_text
    else:
        html = u'  <td class="head_day">&nbsp;%s</td>\r\n' % html_text

    return html


def calhead_day_nbmonth(day):
    """ Show days of previous or next month """

    html = u'  <td class="head_day_nbmonth">&nbsp;%s</td>\r\n' % day
    return html


def calshow_blankbox(classname):
    """ Show blank calendar box """

    html = u'  <td class="%s">&nbsp;</td>' % classname
    return html


def calshow_blankbox2(classname, colspan):
    html = u'  <td class="%s" colspan="%d">&nbsp;</td>' % (classname, colspan)
    return html


def calshow_eventbox(event, colspan, status, cur_date):

    """ Show eventbox """

    if status:
        status = u'_%s' % status

    title = event['title']
    eid = event['id']
    startdate = event['startdate']
    enddate = event['enddate']
    starttime = event['starttime']
    endtime = event['endtime']
    description = event['description']
    bgcolor = event['bgcolor']

    if not bgcolor:
        if Globs.labels:
            labels = Globs.labels
            # for backward compatibility
            if event.has_key('label'):
                if labels.has_key(event['label']):
                    bgcolor = labels[event['label']]['bgcolor']

    year, month, day = getdatefield(cur_date)

    if bgcolor:
        bgcolor = 'background-color: %s;' % bgcolor
    else:
        bgcolor = 'background-color: %s;' % Params.bgcolor

    if (startdate == enddate) and starttime:
        shour, smin = gettimefield(starttime)

        link = [
            u'<table width="100%" style="border-width: 0px; padding: 0px; margin: 0px;"><tr>\r\n',
            u'<td nowrap class="cal_eventbox_time">%02d:%02d&nbsp;</td>\r\n' % (shour, smin),
            u'<td class="cal_eventbox_time_event">',
            u'%s' % showReferPageParsed(event, 'title', 1),
            u'</td>\r\n</tr></table>',
            ]
        link = u''.join(link)
    else:
        link = u'%s' % showReferPageParsed(event, 'title', 1)


    html = [
        u'  <td class="cal_eventbox" colspan="%d"><table class="cal_event">' % colspan,
        u'      <tr><td class="cal_event%s" style="%s">%s</td></tr>' % (status, bgcolor, link),
        u'      </table></td>',
        ]

    return u'\r\n'.join(html)


def calshow_daily_eventbox2(event, colspan, status, cur_date):
    """ Show eventbox """

    if status:
        status = u'_%s' % status

    title = event['title']
    eid = event['id']
    startdate = event['startdate']
    enddate = event['enddate']
    starttime = event['starttime']
    endtime = event['endtime']
    description = event['description']
    bgcolor = event['bgcolor']

    if not bgcolor:
        labels = Globs.labels
        # for backward compatibility
        if event.has_key('label'):
            if labels.has_key(event['label']):
                bgcolor = labels[event['label']]['bgcolor']

    year, month, day = getdatefield(cur_date)

    if bgcolor:
        bgcolor = 'background-color: %s;' % bgcolor
    else:
        bgcolor = 'background-color: %s;' % Params.bgcolor

    if (startdate == enddate) and starttime:
        shour, smin = gettimefield(starttime)

        link = [
            u'<table width="100%" style="border-width: 0px; padding: 0px; margin: 0px;"><tr>\r\n',
            u'<td width="10" nowrap style="border-width: 0px; padding: 0px; margin: 0px; text-align: left; vertical-align: top; font-size: 7pt; color: #000000;">%02d:%02d&nbsp;</td>\r\n' % (shour, smin),
            u'<td style="border-width: 0px; padding: 0px; margin: 0px; text-align: left; vertical-align: top;font-size: 8pt;">',
            u'%s' % showReferPageParsed(event, 'title', 1),
            u'</td>\r\n</tr></table>',
            ]
        link = u''.join(link)
    else:
        link = u'%s' % showReferPageParsed(event, 'title', 1)


    html = [
        u'  <td colspan="%d" style="width: 96%%; border-width: 0px; line-height: 11px;"><table class="cal_event">' % colspan,
        u'      <tr><td class="cal_event%s" style="%s">%s</td></tr>' % (status, bgcolor, link),
        u'      </table></td>',
        ]

    return u'\r\n'.join(html)


def calshow_daily_eventbox(event):
    """ Show daily eventbox """

    title = event['title']
    eid = event['id']
    startdate = event['startdate']
    enddate = event['enddate']
    starttime = event['starttime']
    endtime = event['endtime']
    description = event['description']
    bgcolor = event['bgcolor']
    time_len = event['time_len']

    if not bgcolor:
        labels = Globs.labels
        # for backward compatibility
        if event.has_key('label'):
            if labels.has_key(event['label']):
                bgcolor = labels[event['label']]['bgcolor']

    if bgcolor:
        bgcolor = 'background-color: %s;' % bgcolor
    else:
        bgcolor = 'background-color: %s;' % Params.bgcolor

    shour, smin = gettimefield(starttime)
    ehour, emin = gettimefield(endtime)

    html = [
        u'  <td colspan="%(colspan)d"',
        u'      style="%s border-width: 2px; border-color: #000000; vertical-align: top; font-size: 9pt; ' % bgcolor,
        u'      width: %(width)s;" ',
        u'      rowspan="%(rowspan)d">' % { 'rowspan': time_len },
        u'      %02d:%02d ~ %02d:%02d<br>%s' % (shour, smin, ehour, emin, showReferPageParsed(event, 'title', 1)),
        u'  </td>',
        ]

    return u'\r\n'.join(html)


def calshow_weekly_eventbox(event):
    """ Show weekly eventbox """

    title = event['title']
    eid = event['id']
    startdate = event['startdate']
    enddate = event['enddate']
    starttime = event['starttime']
    endtime = event['endtime']
    description = event['description']
    bgcolor = event['bgcolor']
    time_len = event['time_len']

    if not bgcolor:
        labels = Globs.labels
        # for backward compatibility
        if event.has_key('label'):
            if labels.has_key(event['label']):
                bgcolor = labels[event['label']]['bgcolor']

    if bgcolor:
        bgcolor = 'background-color: %s;' % bgcolor
    else:
        bgcolor = 'background-color: %s;' % Params.bgcolor

    shour, smin = gettimefield(starttime)
    ehour, emin = gettimefield(endtime)

    html = [
        u'  <td colspan="%(colspan)d"',
        u'      style="%s;' % bgcolor,
        u'      width: %(width)s;" ',
        u'      rowspan="%(rowspan)d"' % { 'rowspan': time_len },
        u'      class="cal_weekly_eventbox">',
        u'      %s' % showReferPageParsed(event, 'title', 1),
        u'  </td>',
        ]

    return u'\r\n'.join(html)


def calshow_blankeventbox():
    """ Show blank eventbox """

    html = [
        u'  <td colspan="%(colspan)d" style="width: %(width)s;" class="cal_blankeventbox">&nbsp;</td>',
        ]

    return u'\r\n'.join(html)


def calshow_weekly_eventbox2(event, colspan, width, status, cur_date):
    """ Show eventbox """
    if status:
        status = u'_%s' % status

    title = event['title']
    eid = event['id']
    startdate = event['startdate']
    enddate = event['enddate']
    starttime = event['starttime']
    endtime = event['endtime']
    description = event['description']
    bgcolor = event['bgcolor']

    year, month, day = getdatefield(cur_date)

    if not bgcolor:
        labels = Globs.labels
        # for backward compatibility
        if event.has_key('label'):
            if labels.has_key(event['label']):
                bgcolor = labels[event['label']]['bgcolor']

    if bgcolor:
        bgcolor = 'background-color: %s;' % bgcolor
    else:
        bgcolor = 'background-color: %s;' % Params.bgcolor

    link = u'%s' % showReferPageParsed(event, 'title', 1)

    html = [
        u'  <td colspan="%d" style="width: %d%%;" class="cal_weekly_eventbox2"><table class="cal_event">' % (colspan, width),
        u'      <tr><td class="cal_event%s" style="%s">%s</td></tr>' % (status, bgcolor, link),
        u'      </table></td>',
        ]

    return u'\r\n'.join(html)


def calshow_blankeventbox2(colspan, width):
    """ Show blank eventbox """

    html = [
        u'  <td colspan="%(colspan)d"' % { 'colspan': colspan },
        u'      style="width: %(width)s;" class="cal_blankeventbox">&nbsp;</td>' % { 'width': '%d%%%%' % width },
        ]

    return u'\r\n'.join(html)



def calshow_daily_hourhead(hour):

    if hour >= Globs.dailystart and hour <= Globs.dailyend:
        bgcolor = "#ffffcc"
    else:
        bgcolor = "#ffeeee"

    html = [
        u'  <td class="cal_hourhead" style="background-color: %s; width: 4%%%%;">%02d</td>' % (bgcolor, hour),
        ]

    return u'\r\n'.join(html)

def calshow_weekly_hourhead(hour):

    if hour >= Globs.dailystart and hour <= Globs.dailyend:
        bgcolor = "#ffffcc"
    else:
        bgcolor = "#ffeeee"

    html = [
        u'  <td class="cal_hourhead" style="width: 2%%%%; background-color: %s; ">%02d</td>' % (bgcolor, hour),
        ]

    return u'\r\n'.join(html)



def insertcalevents(cal_events, datefrom, dateto, e_id, e_start_date, e_end_date):

    if not (int(e_start_date) > dateto or int(e_end_date) < datefrom):

        e_start_date = str(max(int(e_start_date), datefrom))
        e_end_date = str(min(int(e_end_date), dateto))

        day_delta = datetime.timedelta(days=1)
        e_start_year, e_start_month, e_start_day = getdatefield(e_start_date)
        cur_datetime = datetime.date(e_start_year, e_start_month, e_start_day)

        while 1:
            tmp_record_date = formatdateobject(cur_datetime)

            if not cal_events.has_key(tmp_record_date):
                cal_events[tmp_record_date] = []
            cal_events[tmp_record_date].append(e_id)

            if tmp_record_date == e_end_date:
                break

            cur_datetime = cur_datetime + day_delta

# date format should be like '20051004' for 2005, Oct., 04
def diffday(date1, date2):

    try:
        year1, month1, day1 = getdatefield(date1)
        year2, month2, day2 = getdatefield(date2)
        tmp_diff = datetime.date(year2, month2, day2) - datetime.date(year1, month1, day1)
    except (TypeError, ValueError):
        raise EventcalError('invalid_date')

    return tmp_diff.days


# time format should be like '1700' for 05:00pm
def difftime(time1, time2):

    try:
        hour1, min1 = gettimefield(time1)
        hour2, min2 = gettimefield(time2)

    except (TypeError, ValueError):
        raise EventcalError('invalid_time')

    if min2 == 0 and hour2 != 0 and hour1 != hour2:
        hour2 -= 1

    tmp_diff = hour2 - hour1

    return tmp_diff



def formatDate(year, month, day):
    # returns like: '20051004'
    return u'%4d%02d%02d' % (year, month, day)

def formatTime(hour, min):
    # returns like: '1700'
    return u'%2d%02d' % (hour, min)


def formatdateobject(obj_date):

    return formatDate(obj_date.year, obj_date.month, obj_date.day)

def formattimeobject(obj_time):

    return formatTime(obj_time.hour, obj_time.minute)


def debug(astring):
    Globs.debugmsg += u'<li>%s\n' % astring


def geterrormsg(errmsgcode, refer='', title='', hid=''):

    if errmsgcode == 'invalid_caldate':
        msg = 'Warning: Invalid value for "caldate" parameter. Shows today.'

    elif errmsgcode == 'invalid_curdate':
        msg = 'Warning: Invalid value for "curdate" parameter. Shows today.'

    elif errmsgcode == 'invalid_numcal':
        msg = 'Warning: Invalid value of "numcal" parameter. Shows one.'

    elif errmsgcode == 'invalid_startdate':
        msg = 'Error: Invalid startdate format. Not handled.'

    elif errmsgcode == 'invalid_enddate':
        msg = 'Error: Invalid enddate format. Not handled.'

    elif errmsgcode == 'invalid_start':
        msg = 'Error: Invalid start date or time format. Not handled.'

    elif errmsgcode == 'invalid_end':
        msg = 'Error: Invalid end date or time format. Not handled.'

    elif errmsgcode == 'invalid_date':
        msg = 'Error: Invalid date format. Not handled.'

    elif errmsgcode == 'enddate_precede':
        msg = 'Error: Startdate should be earlier than Enddate. Not handled.'

    elif errmsgcode == 'invalid_starttime':
        msg = 'Error: Invalid starttime format. Not handled.'

    elif errmsgcode == 'invalid_endtime':
        msg = 'Error: Invalid endtime format. Not handled.'

    elif errmsgcode == 'invalid_time':
        msg = 'Error: Invalid time format. Not handled.'

    elif errmsgcode == 'endtime_precede':
        msg = 'Error: Starttime should be earlier than Endtime. Not handled.'

    elif errmsgcode == 'len_recur_int':
        msg = 'Error: Event length should be smaller than recurrence interval. Not handled.'

    elif errmsgcode == 'invalid_bgcolor':
        msg = 'Warning: Invalid bgcolor format. Ignored.'

    elif errmsgcode == 'invalid_label':
        msg = 'Warning: Invalid label format. Ignored.'

    elif errmsgcode == 'invalid_recur':
        msg = 'Error: Invalid recurrence format. Not handled.'

    elif errmsgcode == 'invalid_recur_until':
        msg = 'Error: Invalid end date (until) format of the recurrence. Not handled.'

    elif errmsgcode == 'empty_description':
        msg = 'Warning: Empty description. Ignored.'

    elif errmsgcode == 'invalid_default_bgcolor':
        msg = 'Warning: Invalid default_bgcolor format. Ignored.'

    elif errmsgcode == 'empty_default_description':
        msg = 'Warning: Empty default_description. Ignored.'

    elif errmsgcode == 'redefined_label':
        msg = 'Warning: Redefined label. Ignored.'

    elif errmsgcode == 'empty_label_definition':
        msg = 'Warning: Invalid label definition. Ignored.'

    elif errmsgcode == 'need_starttime':
        msg = 'Error: Starttime should be specified. Not handled.'

    elif errmsgcode == 'recur_until_precede':
        msg = 'Error: Enddate should be earlier than the end date (until) of recurrence. Not handled.'

    else:
        msg = 'undefined: %s' % errmsgcode

    if refer:
        msg = '%s (%s)' % (msg, getReferLink(refer, title, hid))

    return msg


def errormsgcode(errmsgcode):

    errormsg(geterrormsg(errmsgcode))


def errormsg(astring):
    Globs.errormsg += u'<li>%s\n' % astring


def yearmonthplusoffset(year, month, offset):
    month = month+offset
    # handle offset and under/overflows - quick and dirty, yes!
    while month < 1:
        month = month + 12
        year = year - 1
    while month > 12:
        month = month - 12
        year = year + 1
    return year, month


def formatcfgdatetime(strdate, strtime=''):

    if not strdate:
        return ''

    request = Globs.request

    if request.user.date_fmt:
        date_fmt = request.user.date_fmt
    else:
        date_fmt = request.cfg.date_fmt

    if request.user.datetime_fmt:
        datetime_fmt = request.user.datetime_fmt
    else:
        datetime_fmt = request.cfg.datetime_fmt

    ## XXX HACK
    datetime_fmt = datetime_fmt.replace(':%S', '')

    date_fmt = str(date_fmt)
    datetime_fmt = str(datetime_fmt)

    year, month, day = getdatefield(str(strdate))
    if strtime:
        hour, min = gettimefield(str(strtime))
        objdatetime = datetime.datetime(year, month, day, hour, min)
        return objdatetime.strftime(datetime_fmt)
    else:
        objdate = getdatetimefromstring(strdate)
        return objdate.strftime(date_fmt)


def getdatetimefromstring(strdate):
    year, month, day = getdatefield(str(strdate))
    return datetime.date( year, month, day )


def searchPages(request, needle):
    """ Search the pages and return the results """
    query = search.QueryParser().parse_query(needle)
    results = search.searchPages(request, query)
    #results.sortByPagename()

    return results.hits

    html = []
    for page in results.hits:
        html.append(page.page_name)

    html = u',<br>'.join(html)
    return u'%s<p>%s' % (Params.category, html)


def getFirstDateOfWeek(year, month, day):
	orgday = datetime.date(year, month, day)
	yearBase, week, weekday = orgday.isocalendar()
	baseDate = datetime.date(yearBase, 2, 1)
	yearBase, weekBase, dayBase = baseDate.isocalendar()
	days = datetime.timedelta(1-dayBase+(week-weekBase)*7)
	theday = baseDate + days

	theday -= datetime.timedelta(7 - calendar.firstweekday())

	if orgday - theday >= datetime.timedelta(7):
	    theday += datetime.timedelta(7)

	return theday

def gcd(a,b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:
        a, b = b, a % b

    return a

def lcm(a,b):
    """Return lowest common multiple."""
    return (a*b)/gcd(a,b)

def LCM(terms):
    "Return lcm of a list of numbers."
    return reduce(lambda a,b: lcm(a,b), terms)


def getNumericalMonth(strMonth):
    months = Globs.months

    strMonth = strMonth.lower()

    index = 0
    for monthitem in months:
        index += 1
        if monthitem.lower().startswith(strMonth):
            return index

    return 0


def getReferLink(refer, title='', hid=''):
    request = Globs.request

    refer_url = '%s/%s' % (request.getScriptname(), wikiutil.quoteWikinameURL(refer))

    if hid:
        refer_url += '#%s' % hid

    if title:
        refer = '%s: "%s"' % (refer, title)

    return '<a href="%s">%s</a>' % (refer_url, refer)
