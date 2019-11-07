#
# hpos-admin-server -- Perform authenticated HoloPortOS administrative actions
#

from __future__ import absolute_import, print_function, division

__author__                      = "Perry Kundert"
__email__                       = "perry.kundert@holo.host"
__copyright__                   = "Copyright (c) 2019 Holo Ltd."
__license__                     = "GPLv3 (or later)"

import bisect
import json
import logging
import re

log				= logging.getLogger( "api_util" )

""" 
api_util.register -- Class to manage the set of historically supported API version numbers.
  .add    -- Register an API dict w/ the given version number
  .get    -- Parse version, return best ((<version>, {api})
  .parse  -- Parse a version number, eg 'v1' --> (1,None,None) tuple
  .search -- Retrieve an API (9<version>), {'name': func, ...}) dict matching version tuple
"""


class register:
    def __init__( self ):
        self._endpoint		= {} # Register all version (1,2,3) API enpoint dicts here

    def add( self, version_tuple, api ):
        self._endpoint[version_tuple] = api

    def get( self, version ):
        """Find the nearest viable ((<version>,{api}) pair."""
        version_tuple		= self.parse( version )
        return self.search( version_tuple )

    def parse( self, version ):
        """Canonicalize a "v#.#.#" version string into a 3-tuple.  The re.match returns None for
        unmatched version values, eg. "v1" will return (1,None,None).  Returns the matching
        (<version_tuple>, (<api_version>,<api_dict>)), or raises an Exception.

        """
        version_match		= re.match(
            r"[vV]?(?P<major>\d+)(?:\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?)?",
            version
        )
        assert version_match, \
            f"Invalid API version: {version}"
        version_tuple		= tuple(
            map(
                lambda x: x if x is None else int(x),
                version_match.groups()
            )
        )
        return version_tuple

    def search( self, version_tuple ):
        """Find the API endpoint dict implementing (nearest to) version_tuple.  If none is found,
        raises an Exception.  If a specific value is provided for minor, patch, then it must match;
        otherwise, the largest available entry is used.  For example, if .../v1.3/ is specified, and
        v1.3.7 and v1.3.0 are available, then the v1.3.7 API will be used.

        """
        apis			= sorted(self._endpoint)
        try:
            inexact_index	= version_tuple.index(None)
            assert inexact_index > 0, \
                f"Unsupported API version: {version_tuple}; require at least a major version number"
        except ValueError:
            # Exact version w/o None in version_tuple.
            look_below		= bisect.bisect(apis, version_tuple)
            assert 0 < look_below <= len(apis) \
              and apis[look_below-1] == version_tuple, \
                f"Unsupported API version: {version_tuple}; not found in {apis}"
            log.debug(f"Found API exact eq {version_tuple}, below index {look_below} in {apis}")
        else:
            # Inexact version_tuple containing None; increment next larger version number, return
            # available API below that.  Eg. convert (2,3,None) to (2,4,0)
            next_above		= \
                version_tuple[:inexact_index-1] \
                + ( version_tuple[inexact_index-1] + 1, ) \
                + tuple(0 for _ in version_tuple[inexact_index:])
            # Eg. find index of (2,3,14), for (2,4,0)
            look_below		= bisect.bisect(apis, next_above)
            assert 0 < look_below <= len(apis) \
              and apis[look_below-1][:inexact_index] == version_tuple[:inexact_index], \
                f"Unsupported API version: {version_tuple}; not found in {apis}"
            log.debug(f"Found API close to {version_tuple}, below index {look_below} in {apis} (w/ {next_above})")
    
        # Ensure at least one API was below, and that the one found matches the exact version prefixes
        api_version		= apis[look_below-1]
        return api_version,self._endpoint[api_version]
