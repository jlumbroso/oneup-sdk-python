
from __future__ import absolute_import

import oneupsdk

SECTION_NAME = "oneup"

config = oneupsdk.get_local_config(
    section=SECTION_NAME,
    template={
        SECTION_NAME: {
            "username": str,
            "password": str,
        },
    })


# Import top-level methods
from oneupsdk.integration.macros import *