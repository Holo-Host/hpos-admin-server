from setuptools import setup
import os, sys

here = os.path.abspath( os.path.dirname( __file__ ))

__version__			= None
__version_info__		= None
exec( open( 'admin_webpy/version.py', 'r' ).read() )

console_scripts			= [
    'hpos-admin-server	= admin_webpy.server.main:main',
]

install_requires		= open( os.path.join( here, "requirements.txt" )).readlines()

setup(
    name			= "hpos-admin-server",
    version			= __version__,
    tests_require		= [ "pytest" ],
    install_requires		= install_requires,
    packages			= [ 
        "hpos-admin-server",
    ],
    package_dir			= {
        "hpos-admin-server":	"./admin_webpy", 
    },
    entry_points		= {
        'console_scripts': 	console_scripts,
    },
    include_package_data	= True,
    author			= "Perry Kundert",
    author_email		= "perry.kunder@holo.host",
    description			= "HoloPortOS admin API server",
    long_description		= """\
Respond to authenticated Admin API requests from HoloPortOS admin.

All requests are assumed signed by the holo-config.json Admin API private key.
This confirmation is performed elsewhere (eg. via nginx auth_request module).
""",
    license			= "GPLv3",
    keywords			= "HoloPortOS HPOS Holo Admin",
    url				= "https://github.com/Holo-Host/hpos-admin-server",
    classifiers			= [
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "Environment :: Web Environment",
    ],
)
