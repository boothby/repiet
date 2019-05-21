from __future__ import absolute_import

import sys
import os
from setuptools import setup

# add __version__, __author__, __authoremail__, __description__ to this namespace
_PY2 = sys.version_info.major == 2

# change directories so this works when called from other locations. Useful in build systems.
setup_folder_loc = os.path.dirname(os.path.abspath(__file__))
os.chdir(setup_folder_loc)

install_requires = ['networkx', 'Pillow']

packages = ['piet2']

scripts = ['bin/piet2']

setup(
    name='piet2',
    version='0.0.0',
    author='Kelly Boothby',
    author_email='',
    description='A Piet compiler, targeting a variety of other languages',
    url='https://github.com/boothby/piet2',
    packages=packages,
    scripts=scripts,
    install_requires=install_requires,
    zip_safe=False,
)

