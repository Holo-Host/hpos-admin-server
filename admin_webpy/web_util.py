#
# hpos-admin-server -- Perform authenticated HoloPortOS administrative actions
#

from __future__ import absolute_import, print_function, division

__author__                      = "Perry Kundert"
__email__                       = "perry.kundert@holo.host"
__copyright__                   = "Copyright (c) 2019 Holo Ltd."
__license__                     = "GPLv3 (or later)"

import json
import logging

log				= logging.getLogger( "web_util" )


def deduce_encoding( available, environ, accept=None ):
    """Deduce acceptable encoding from HTTP Accept: header:

        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8

    If it remains None (or the supplied one is unrecognized), the
    caller should fail to produce the desired content, and return an
    HTML status code 406 Not Acceptable.

    If no Accept: encoding is supplied in the environ, the default
    (first) encoding in order is used.

    We don't test a supplied 'accept' encoding against the HTTP_ACCEPT
    settings, because certain URLs have a fixed encoding.  For
    example, /some/url/blah.json always wants to return
    "application/json", regardless of whether the browser's Accept:
    header indicates it is acceptable.  We *do* however test the
    supplied 'accept' encoding against the 'available' encodings,
    because these are the only ones known to the caller.

    Otherwise, return the first acceptable encoding in 'available'.  If no
    matching encodings are avaliable, return the (original) None.
    """
    if accept:
        # A desired encoding; make sure it is available
        accept		= accept.lower()
        if accept not in available:
            accept	= None
        return accept

    # No predefined accept encoding; deduce preferred available one.  Accept:
    # may contain */*, */json, etc.  If multiple matches, select the one with
    # the highest Accept: quality value (our present None starts with a quality
    # metric of 0.0).  Test available: ["application/json", "text/html"],
    # vs. HTTP_ACCEPT
    # "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" Since
    # earlier matches are for the more preferred encodings, later matches must
    # *exceed* the quality metric of the earlier.
    accept		= None # may be "", False, {}, [], ()
    HTTP_ACCEPT		= environ.get( "HTTP_ACCEPT", "*/*" ).lower() if environ else "*/*"
    quality		= 0.0
    for stanza in HTTP_ACCEPT.split( ',' ):
        # application/xml;q=0.9
        q		= 1.0
        for encoding in reversed( stanza.split( ';' )):
            if encoding.startswith( "q=" ):
                q	= float( encoding[2:] )
        for avail in available:
            match	= True
            for a, t in zip( avail.split( '/' ), encoding.split( '/' )):
                if a != t and t != '*':
                    match = False
            if match:
                log.debug( "Found %16s == %-16s;q=%.1f %s %-16s;q=%.1f",
                           avail, encoding, q,
                           '> ' if q > quality else '<=',
                           accept, quality )
                if q > quality:
                    quality	= q
                    accept	= avail
    return accept

