from __future__ import absolute_import

import sys
import os
from setuptools import setup
import repiet

# change directories so this works when called from other locations. Useful in build systems.
setup_folder_loc = os.path.dirname(os.path.abspath(__file__))
os.chdir(setup_folder_loc)

install_requires = ['Pillow']

packages = ['repiet', 'repiet._backends']

scripts = ['bin/repiet']

setup(
    name=repiet.__pkgname__,
    version=repiet.__version__,
    author=repiet.__authorname__,
    author_email=repiet.__authoremail__,
    description=repiet.__description__,
    url=repiet.__url__,
    packages=packages,
    scripts=scripts,
    install_requires=install_requires,
)
