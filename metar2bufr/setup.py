import io
import os
import re
from setuptools import find_packages, setup

KEYWORDS = [
    'WMO',
    'METAR', 'FM-15'
    'BUFR',
    'decoding',
    'weather',
    'observations'
]

DESCRIPTION = 'Convert METAR TAC messages or a METAR file to BUFR4.'

install_requires = [
    'csv2bufr',
    'metarDecoders',
    'xmlUtilities'
]

setup(
    name='metar2bufr',
    version=0.1,
    description=DESCRIPTION,
    license='"Creative Commons Universal License - https://creativecommons.org/publicdomain/zero/1.0/"',
    keywords=' '.join(KEYWORDS),
    author='Alexander Thompson',
    author_email='alexander.thompson@noaa.gov',
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True
)