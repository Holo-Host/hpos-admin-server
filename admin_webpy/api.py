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

log				= logging.getLogger( "api" )

"""
api.rest -- Adds all available API versions
"""

# 
# v1 API:
# 
# GET /api/v1/ping
# GET /api/v1/config
# GET /api/v1/status
# 

def api_ping_v1( version, path, queries, environ, accept, data=None ):
    """Responds to a ping with any body data supplied (to a POST .../ping)"""
    return dict(
        pong			= data
    )


def api_config_v1( version, path, queries, environ, accept, data=None ):
    """Responds with the current HoloPortOS config, if successful.

    From holo-cofig.json, we return the contents of `v1`, (excluding seed, of course).  Assumes that
    the current holo-config.json is stored (or sym-linked) in the ./data/ directory of the server.
    This is presently just the `admin` object, which includes by default, `public_key` and `email`.

    A PUT (replace full contents) or PATCH (change partial contents) can modify this data.  Only the
    `admin` object in `holo-config.json` may be modified, and only `email`, `public_key` and `name`
    may be specified.  Attempting to alter any other entries is an error, and attempting to delete
    `email` or `public_key` is an error.

    The `holo-config.json` is considered mutable configuration data, and the file is altered and
    re-written in-place, as the last step in PUT/PATCH API call.  We cannot use an atomic move
    operation (because the file may be supplied via symbolic link), but since the contents of
    `holo-config.json` is used only on boot-up, we are unlikely to encounter race-conditions.


    The `name` field is simply stored, as a string, as a property in the topmost level of the JSON
    object in `holo-config.json`.


    From the HoloPortOS, we produce the `holoportos` object.  This contains `network` ("live",
    "dev", "test"), and `sshAccess` (true, false).  They may not be deleted, but their values may be
    changed via PUT or PATCH.

    If a value is changed, a Nix operation is launched to alter this state in the NixOS operating
    system.


    Once successful, the current system `api/v#/config` status is re-harvested and returned; the
    results of the successful GET, PUT and PATCH are `200 OK`, and a body payload containing the
    current config of the system.
    """
    with open( "data/holo-config.json" ) as f:
        config			= json.loads( f.read() )
    return dict(
        admin			= config['v1']['admin']
    )


def api_status_v1( version, path, queries, environ, accept, data=None ):
    """The `holo_nixpkgs` object contains:


    `channel.rev`:

    This commit hash is parsed from the symbolic link: `./data/run/current-system ->
    /nix/store/sakdkx4rabp5a0fk16c4r8sjbhv751hp-nixos-system-holoportos-19.09pre-git`

    `current_system.rev`: Parsed from `./data/booted-system` symbolic link.

    `zerotier`: From `zerotier-cli -j info`
    """


def rest( apis ):
    """Add all available APIs at their API version tuples"""
    apis.add(
        version_tuple	= (1,0,0),
        api		= dict(
            ping		= api_ping_v1,
            config		= api_config_v1,
            status		= api_status_v1,
        )
    )


