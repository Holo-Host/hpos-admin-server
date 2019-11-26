
#
# hpos-admin-server -- Perform authenticated HoloPortOS administrative actions
#

from __future__ import absolute_import, print_function, division

__author__                      = "Perry Kundert"
__email__                       = "perry.kundert@holo.host"
__copyright__                   = "Copyright (c) 2019 Holo Ltd."
__license__                     = "GPLv3 (or later)"

__all__                         = [ 'server' ]

# These modules form the public interface of hpos-admin-server
from .version  import __version__, __version_info__
from .server import *
