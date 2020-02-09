import os
from setuptools import setup, find_packages

PACKAGE_NAME = "oneupsdk"

# The text of the README file
README = open("README.md").read()

# Get the version number without importing our package
# (which would trigger some ImportError due to missing dependencies)

version_contents = {}
with open(os.path.join(PACKAGE_NAME, "version.py")) as f:
    exec(f.read(), version_contents)

# This call to setup() does all the work
setup(
    name=PACKAGE_NAME,
    version=version_contents["__version__"],
    description="SDK Integration for the OneUp Learning platform.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/jlumbroso/oneup-sdk-python",
    author="Jérémie Lumbroso",
    author_email="lumbroso@cs.princeton.edu",
    license="LGPL-3.0-or-later",
    classifiers=[
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    install_requires=[
        "bs4",
        "confuse",
        "python-dateutil",
        "PyYAML",
        "requests",
        "six",
        # "better_exceptions",
        # "blessings",
        # "colorama",
        # "eliot",
    ],
    include_package_data=True,
)
