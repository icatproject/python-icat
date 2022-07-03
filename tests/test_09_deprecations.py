"""Verfify that deprecated features raise a deprecation warning.
"""

import pytest
import icat

# Deprecations not tested in this module:
# - Module variable icat.config.defaultsection.
#   It's easier to test this in the setting of the test_01_config.py
#   module.
#
# No other deprecations for the moment.
