import icalendar


def download_events_ical():

    debug('Download events: icalendar')

    request = Globs.request
    formatter = Globs.formatter

    html_event_rows = []
    html_list_header = cal_listhead()

    # read all the events
    events, cal_events, labels = loadEvents()

    # sort events
    sorted_eventids = events.keys()
    sorted_eventids.sort(comp_list_events)

    # TODO: organize the data to export to icalendar
