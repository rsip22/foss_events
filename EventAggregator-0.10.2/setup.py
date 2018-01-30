#! /usr/bin/env python

from distutils.core import setup

setup(
    name         = "EventAggregator",
    description  = "Aggregate event data and display it in an event calendar (or summarise it in iCalendar and RSS resources)",
    author       = "Paul Boddie",
    author_email = "paul@boddie.org.uk",
    url          = "http://moinmo.in/MacroMarket/EventAggregator",
    version      = "0.10.2",
    packages     = ["EventAggregatorSupport"],
    py_modules   = ["MoinMoin.script.import.eventfeed"]
    )
