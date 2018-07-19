import argparse
import os
import platform
import sys
from setuptools import setup, find_packages

appname = "electrum-merchant"

if sys.version_info[:3] < (3, 5, 0):
    sys.exit("Error: electrum-merchant requires Python version >= 3.5.0...")

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = appname,
    packages = ['electrum-merchant',],
    version = '0.3',
    description = 'Electrum wallet - merchant add-ons',
    long_description = read('README.rst'),
    author = 'Thomas Voegtlin, Serge Victor',
    author_email = 'electrum@random.re',
    url = 'https://github.com/spesmilo/electrum-merchant',
    license = 'MIT',
    keywords = 'electrum, bitcoin, litecoin, bitcoin cash, dash, payment, merchant',
    zip_safe = False,
    include_package_data = True,
    platforms = 'any',
    install_requires = 'npmdownloader',
    download_url = 'https://github.com/spesmilo/electrum-merchant/tarball/0.3',
    classifiers = [
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
    ]
)
