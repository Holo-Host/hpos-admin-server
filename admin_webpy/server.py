#! /usr/bin/env python3

#
# hpos-admin-server -- Perform authenticated HoloPortOS administrative actions
#

from __future__ import absolute_import, print_function, division

__author__                      = "Perry Kundert"
__email__                       = "perry.kundert@holo.host"
__copyright__                   = "Copyright (c) 2019 Holo Ltd."
__license__                     = "GPLv3 (or later)"

import argparse
import bisect
import json
import logging
import os
import re
import socket
import sys
import traceback

import web

from .version import __version_info__
from .web_util import *

# The Server provides some known service prefixes.  Here they are; add any more when we know about
prefixes			= [
    # "something",
]

address				= ( 'localhost', 5555 )	# --bind [i'face][:port] HTTP bind address
analytics			= None			# --analytics '...'      Google Analytics {'id':...}
log				= logging.getLogger( "admin_api" )
log_cfg				= {
    "level":	logging.WARNING,
    "datefmt":	'%m-%d %H:%M:%S',
    "format":	'%(asctime)s.%(msecs).03d %(thread)16x %(name)-8.8s %(levelname)-8.8s %(funcName)-10.10s %(message)s',
}

# 
# version... -- Enumerate the set of historically supported API version numbers.
#
def version_info( version ):
    """Canonicalize a "v#.#.#" version string into a 3-tuple.  The re.match returns None for unmatched
    version values, eg. "v1" will return (1,None,None).  Returns the matching (<version_tuple>,
    (<api_version>,<api_dict>)), or raises an Exception.

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

    return version_tuple,version_api( version_tuple )


def version_api( version_tuple ):
    """Find the API endpoint dict implementing (nearest to) version_tuple.  If none is found, raises an
    Exception.  If a specific value is provided for minor, patch, then it must match; otherwise, the
    largest available entry is used.  For example, if .../v1.3/ is specified, and v1.3.7 and v1.3.0
    are available, then the v1.3.7 API will be used.


    """
    apis			= sorted(sorted(version_api.endpoint))
    try:
        inexact_index		= version_tuple.index(None)
        assert inexact_index > 0, \
            f"Unsupported API version: {version_tuple}; require at least a major version number"
    except ValueError:
        # Exact version w/o None.
        look_below		= bisect.bisect(apis, version_tuple)
        assert 0 < look_below <= len(apis) \
            and apis[look_below-1] == version_tuple, \
            f"Unsupported API version: {version_tuple}; not found in {apis}"
        log.debug(f"Found API exact eq {version_tuple}, below index {look_below} in {apis}")
    else:
        # Inexact version containing None; increment next larger version number, return available API
        # below that.  Eg. convert (2,3,None) to (2,4,0)
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
    api_version			= apis[look_below-1]
    return api_version,version_api.endpoint[api_version]

version_api.endpoint		= {} # Install all version (1,2,3) API enpoint dicts here


# 
# The Web API, implemented using web.py
# 

# 
# Current .version.__version_info__ API:
# 
def api_ping_v1( version, path, queries, environ, accept, data=None, framework=web ):
    """Responds to a ping with any body data supplied (to a POST .../ping)"""
    return dict(
        pong			= data
    )


def api_config_v1( version, path, queries, environ, accept, data=None, framework=web ):
    """Responds with the current holo-cofig.json (excl. seed, of course).  Assumes that the current
    holo-config.json is stored (or sym-linked) in the ./data/ directory of the server.

    Presently, *only* the v1.admin element is returned; we avoid returning the seed.

    """
    with open( "data/holo-config.json" ) as f:
        config			= json.loads( f.read() )
    return dict(
        v1 = dict(
            admin		= config['v1']['admin']
        )
    )


version_api.endpoint[__version_info__]	= dict(
    ping			= api_ping_v1,
    config			= api_config_v1,
)

# 
# Previous supported APIs:
# 
pass


def api_request( prefix, version, path, queries, environ, accept, data=None, framework=web ):
    """A HoloPortOS admin API request.
    
    Computes a list of 'results' dicts, and renders it as requested by "accept" encoding.

    Note that the handling of paths *without* a trailing '/' is handled unexpectedly by browsers;
    they do not consider the last segment to be a path segment in the URL, so we must ensure that,
    when we construct URLs to the next API segment, we forcibly include a '/' in the full
    REQUEST_URI + the next path segment (trimming any existing).
    """

    assert not queries, \
        "Unrecognized queries: %s" % ", ".join( queries.keys() )

    try:
        if not prefix:
            # /[index[.html]]
            title		= "Service Prefixes Available"
            results		= [
                dict( url = f"{environ.get('REQUEST_URI').rstrip('/')}/{pre}" )
                for pre in prefixes
            ]
        elif not version:
            # /<prefix>
            title		= "API Versions Available"
            results		= [
                dict( version = f"v{'.'.join(map(str,ver))}" )
                for ver in version_api.endpoint.keys()
            ]
        elif not path:
            # /<prefix>/v#[.#.#]
            ver_tup,(ver,api)	= version_info( version )
            title		= f"API v{'.'.join(map(str,ver))} Paths Available"
            results		= [
                dict( url = f"{environ.get('REQUEST_URI').rstrip('/')}/{p}" )
                for p in api
            ]
        else:
            #
            ver_tup,(ver,api)	= version_info( version )
            assert path in api, f"API v{'.'.join(map(str,ver))}; Unrecognized path: {path}"
            title		= f"API v{'.'.join(map(str,ver))} {path}"
            results		= api[path](
                version	= version,
                path	= path,
                queries	= queries,
                environ	= environ,
                accept	= accept,
                data	= data )

    except Exception as exc:
        log.warning( "Exception: %s", exc )
        log.info( "Exception Stack: %s", traceback.format_exc() )
        raise http_exception( framework, 500, str( exc ))

    accept			= deduce_encoding([ "application/json", "text/javascript", "text/plain",
                                                    "text/html" ],
                                                  environ=environ, accept=accept )


    if accept and accept in ( "application/json", "text/javascript", "text/plain" ):
        response		= ""
        callback		= queries and queries.get( 'callback', "" ) or ""
        if callback:
            response		= callback + "( "
        response               += json.dumps( results, sort_keys=True, indent=4 )
        if callback:
            response           += " )"
    elif accept and accept in ( "text/html" ):
        render			= web.template.render( "templates/", base="layout",
                                                       globals={ 'analytics': analytics } )

        resultslist		= results if type( results ) is list else [results] if results else []
        resultskeys		= list( sorted( resultslist[0].keys() )) if resultslist else []
        response		= render.keylist(
            dict(
                title	= title,
                keys	= resultskeys,
                list	= resultslist
            )
        )
        assert response, f"Failed to render {results}"
    else:
        # Invalid encoding requested.  Return appropriate 406 Not Acceptable
        message			=  "Invalid encoding: %s, for Accept: %s" % (
            accept, environ.get( "HTTP_ACCEPT", "*.*" ))
        raise http_exception( framework, 406, message )

    return accept,response


class api:
    def GET( self, prefix, version, path, data=None ):
        environ			= web.ctx.environ
        queries			= web.input()
        accept			= None
        log.info(f"api GET URI: {environ.get('REQUEST_URI')}, prefix: {prefix!r}, version: {version!r}, path: {path!r}")

        # Trim leading / in path, trailing .{json,html} content type requested via path extension
        if path and path.startswith('/'):
            path		= path[1:]
        if path and path.endswith( ".json" ):
            path		= path[:-5]
            accept		= "application/json"
        elif path and path.endswith( ".html" ):
            path		= path[:-5]
            accept		= "text/html"

        content,response	= api_request(
            prefix	= prefix,
            version	= version,
            path	= path,
            queries	= queries,
            environ	= environ,
            accept	= accept,
            data	= data )

        web.header( "Cache-Control", "no-cache" )
        web.header( "Content-Type", content )
        return response

    def POST( self, prefix, version, path ):
        # form data is in web.input(), just like GET queries, but there could be body data
        return self.GET( prefix, version, path, data=web.data() )


class favicon:
    def GET( self ):
        """Always permanently redirect favicon.ico requests to our favicon.{ico,png}.
        The reason we do this instead of putting a <link "icon"...> is because
        all *other* requests from browsers (ie. api/... ) returning non-HTML
        response Content-Types such as application/json *also* request
        favicon.ico, and we don't have an HTML <head> to specify any icon link.
        Furthermore, they continue to request it 'til satisfied, so we do a 301
        Permanent Redirect to satisfy the browser and prevent future requests.
        So, this is the most general way to handle the favicon.ico"""
        web.redirect( 'static/icons/favicon.ico' )


def web_api( urls, http=None ):
    """Get the required web.py classes from the global namespace.  The iface:port must always passed on
    argv[1] to use app.run(), so use lower-level web.httpserver.runsimple interface, so we can bind
    to the supplied http address."""
    try:
        app			= web.application( urls, globals() )
        web.httpserver.runsimple( app.wsgifunc(), http )
        log.info( "Web API started on %s:%s",
                    http[0] if http else None, http[1] if http else None )
    except socket.error:
        log.error( "Could not bind to %s:%s for web API",
                   http[0] if http else None, http[1] if http else None )
    except Exception as exc:
        log.error( "Web API server on %s:%s failed: %s",
                   http[0] if http else None, http[1] if http else None, exc )


def main( argv=None ):
    ap				= argparse.ArgumentParser(
        description = "HoloPortOS Admin API Server",
        epilog = "" )

    ap.add_argument( '-C', '--change-directory',
                     default=None,
                     help="Change CWD to the target directory" )
    ap.add_argument( '-v', '--verbose',
                     default=0, action="count",
                     help="Display logging information." )
    ap.add_argument( '-d', '--debug',
                     default=False, action="store_true",
                     help="Enable web server debug mode HTML output" )
    ap.add_argument( '-b', '--bind',
                     default=( "%s:%d" % address ),
                     help="HTTP interface[:port] to bind (default: %s:%d)" % (
                         address[0], address[1] ))
    ap.add_argument( '-a', '--analytics',
                     default=None,
                     help="Google Analytics ID (if any)" )
    ap.add_argument( '-p', '--prefix',
                     default='api',
                     help="App URL prefix (optional)" )
    ap.add_argument( '-l', '--log',
                     help="Log file, if desired" )
    args			= ap.parse_args( argv )

    # If desired, run server relative to the specified directory
    if args.change_directory:
        os.chdir( args.change_directory )
    
    # Deduce interface:port address to bind, and correct types (default is address, above)
    http			= args.bind.split( ':' )
    assert 1 <= len( http ) <= 2, "Invalid --address [<interface>]:[<port>}: %s" % args.bind
    http			= ( str( http[0] ) if http[0] else address[0],
                                    int( http[1] ) if len( http ) > 1 and http[1] else address[1] )

    web.config.debug		= bool( args.debug )

    if args.analytics:
        global analytics
        analytics		= { 'id': args.analytics }

    if args.log:
        # Output logging to a file, and handle UNIX-y log file rotation via 'logrotate', which sends
        # signals to indicate that a service's log file has been moved/renamed and it should re-open
        log_cfg['filename']	= args.log

    logging.basicConfig( **log_cfg )

    # The api prefix/version/path regex: (/<prefix>)/(v#[.#.#])(/...)
    api_path			= [ '' ]	# Ensure a leading '/...' after join
    if args.prefix:
        api_path.append( args.prefix )		# Allowing a path prefix, eg. 'api'.

    # Remember the API prefix we've selected, in addition to any other prefixes we're handling
    global prefixes
    prefixes.append( args.prefix or '' )

    # Every API request will have a 'prefix', 'version' and 'path' (None, if not supplied) A
    # non-empty 'path' will contain a leading "/", *unless* its a content-type suffix, eg. .json
    # Both of these are handled by the api.GET.
    api_prefix			= f"({'/'.join(api_path)})" # eg. "(/<prefix>)"
    log.info(f"API Prefix pattern:  {api_prefix!r}")
    api_version			= r"/([vV][^/]*)"
    log.info(f"API Version pattern: {api_version!r}")
    api_path			= r"((?:/.+)?|(?:\..+)?)/?" # /... | [.json]; trailing / ignored

    # 
    # The web.py url endpoints, and their classes
    # 
    urls			= (
        "/favicon.ico",				"favicon",
        api_prefix + api_version + api_path,	"api", # full:        (/<prefix>/(v#[.#[.#.]])(/...)
        api_prefix + "()" + api_path,		"api", # versionless: (/<prefix>)()(/...)
        "/(?:index)?()()" + api_path,		"api", # root
    )

    try:
        web_api( urls=urls, http=http )
    except KeyboardInterrupt:
        log.warning( "Quitting" )
        return 0
    except Exception as exc:
        log.warning( "Exception: %s", exc )
        return 1

if __name__ == "__main__":
    sys.exit( main() )
