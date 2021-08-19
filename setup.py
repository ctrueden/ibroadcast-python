# This is free and unencumbered software released into the public domain.
# See https://unlicense.org/ for details.

import pathlib
from setuptools import setup
from distutils.util import convert_path

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Get values from the about file
about = {}
about_path = convert_path('ibroadcast/about.py')
with open(about_path) as about_file:
    exec(about_file.read(), about)

setup(
    name=about['__PACKAGE_NAME__'],
    version=about['__version__'],
    description=about['__PACKAGE_DESCRIPTION__'],
    author=about['__author__'],
    author_email=about['__email__'],
    url=about['__PACKAGE_URL__'],
    license='Unlicense',
    long_description=README,
    long_description_content_type='text/markdown',
    platforms='ALL',

    include_package_data=True,
    test_suite=None,
    packages=['ibroadcast'],

    python_requires='>=3.6',

    install_requires=[
        'requests>=2.24.0',
    ],

    tests_require=[],

    classifiers=[
        'Topic :: Multimedia :: Sound/Audio',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
