# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EventAggregator location handling

    @copyright: 2008, 2009, 2010, 2011, 2012, 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from LocationSupport import getMapReference

def getMapsPage(request):
    return getattr(request.cfg, "event_aggregator_maps_page", "EventMapsDict")

def getLocationsPage(request):
    return getattr(request.cfg, "event_aggregator_locations_page", "EventLocationsDict")

class Location:

    """
    A representation of a location acquired from the locations dictionary.

    The locations dictionary is a mapping from location to a string containing
    white-space-separated values describing...

      * The latitude and longitude of the location.
      * Optionally, the time regime used by the location.
    """

    def __init__(self, location, locations):

        """
        Initialise the given 'location' using the 'locations' dictionary
        provided.
        """

        self.location = location

        try:
            self.data = locations[location].split()
        except KeyError:
            self.data = []

    def getPosition(self):

        """
        Attempt to return the position of this location. If no position can be
        found, return a latitude of None and a longitude of None.
        """

        try:
            latitude, longitude = map(getMapReference, self.data[:2])
            return latitude, longitude
        except ValueError:
            return None, None

    def getTimeRegime(self):

        """
        Attempt to return the time regime employed at this location. If no
        regime has been specified, return None.
        """

        try:
            return self.data[2]
        except IndexError:
            return None

# vim: tabstop=4 expandtab shiftwidth=4
