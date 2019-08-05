from __future__ import absolute_import

import sys
import os
from setuptools import setup

# change directories so this works when called from other locations. Useful in build systems.
setup_folder_loc = os.path.dirname(os.path.abspath(__file__))
os.chdir(setup_folder_loc)

install_requires = ['Pillow']

packages = ['repiet', 'repiet._backends']

scripts = ['bin/repiet']

setup(
    name='repiet',
    version='0.0.0',
    author='Kelly Boothby',
    author_email='',
    description='A Piet compiler, targeting a variety of other languages',
    url='https://github.com/boothby/repiet',
    packages=packages,
    scripts=scripts,
    install_requires=install_requires,
    zip_safe=False,
)

