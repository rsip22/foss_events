def download_events_ical():
    """ Download events' data in icalendar format """
    debug('Download events: icalendar')

    # request = macro.request
    # request = self.request
    request.content_type = "text/calendar; charset=%s" % config.charset

    # write_resource(self.request)
    # return 1, None

    """
    event['dtstart'] = '20050404T080000'
    """

    # read all the events
    events, cal_events, labels = loadEvents()

    # sort events
    sorted_eventids = events.keys()
    sorted_eventids.sort(comp_list_events)

    # eventitem['startdate'] = e_start_date
    # eventitem['starttime'] = e_start_time
    # eventitem['enddate'] = e_end_date
    # eventitem['endtime'] = e_end_time
    # eventitem['refer'] = referpage
    # eventitem['bgcolor'] = e_bgcolor
    # eventitem['recur_freq'] = e_recur_freq
    # eventitem['recur_type'] = e_recur_type
    # eventitem['recur_until'] = e_recur_until

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
        new_event['DTSTART'] = make_date_time(event,
                                              'startdate',
                                              'starttime')
        new_event['DTEND'] = make_date_time(event, 'enddate', 'endtime')
        new_event.add('description', item['description'])
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

    """
    print 'EVENTS type: ', type(events)  # DICT
    print 'CAL_EVENTS type: ', type(cal_events)  # DICT
    print 'LABELS type: ', type(labels)  # DICT
    """
    # print 'event values: ', events.values()

    for item in events.values():
        make_event(item)
        # print '~~~ Item title: ', item['title']

    return display(cal)
