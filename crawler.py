import urllib.request
import json


def get_events_from_url(url):
    source = urllib.request.urlopen(url)
    data = source.read().decode()

    events_list = json.loads(data)

    # print(json.dumps(events_list, indent=2))

    for event in events_list:
        print('Event:', event['title'])
        print('City:', event['city'])
        print('Date:', event['start_time'], '-', event['end_time'])
        print('==============================')


get_events_from_url('http://www.agendadulibre.org/events.json')
