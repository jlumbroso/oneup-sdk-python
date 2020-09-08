# -*- coding: utf-8 -*-

"""
OneUp SDK

Provides a convenient SDK to interface with the OneUp Learning platform developed
by West-Salem State University.

   Name: oneupsdk
 Author: Jérémie Lumbroso
  Email: lumbroso@cs.princeton.edu
    URL: https://github.com/jlumbroso/oneup-sdk-python
License: Copyright (c) 2020 Jérémie Lumbroso, licensed under the LGPLv3 license
"""

from __future__ import absolute_import

# Documentation

from oneupsdk.version import __version__


# Configuration file

import os as _os
import confuse as _confuse

APPNAME = "oneupsdk"

class OneUpSDKConfiguration(_confuse.LazyConfig):

    def config_dir(self):

        local_config = _os.path.join(_os.getcwd(), _confuse.CONFIG_FILENAME)
        if _os.path.exists(local_config):
            return _os.getcwd()

        return super(OneUpSDKConfiguration, self).config_dir()


class OneUpSDKConfigurationException(Exception):

    def __init__(self, section=None, src=None):
        msg = "There is an error with the configuration file.\n\n"

        if section is not None:
            msg = ("The configuration file does not contain the "
                   "correct parameters for {}.\n\n").format(section)

        if src is not None:
            msg += "Original message was: {}\n\n".format(src)

        super(OneUpSDKConfigurationException, self).__init__(msg)


config = OneUpSDKConfiguration(APPNAME, __name__)

# def get_course_name():
#     try:
#         course = config["course"].get(str).lower()
#         return course
#     except:
#         pass
#
#
# def get_course_term():
#     try:
#         course = config["term"].get(str).lower()
#         return course
#     except:
#         pass


def get_local_config(section, template):

    try:
        valid = config.get(template)

    except _confuse.NotFoundError as exc:
        raise OneUpSDKConfigurationException(
            section=section,
            src=exc.args,
        )

    return valid[section]


from oneupsdk.integration.api import configure_auth