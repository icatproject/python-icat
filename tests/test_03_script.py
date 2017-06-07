"""Calling simple scripts to connect to an ICAT server.

Same as test_03_getversion.py and test_03_login.py, but calling
external scripts.
"""

import pytest
import icat
import icat.config
from conftest import getConfig, callscript

def test_getversion():
    """Get version info from the ICAT server.
    """
    _, conf = getConfig(needlogin=False)
    callscript("getversion.py", conf.cmdargs)


@pytest.mark.parametrize("user", ["root", "useroffice", "acord"])
def test_login(user):
    """Login to the ICAT server.
    """
    _, conf = getConfig(confSection=user)
    callscript("login.py", conf.cmdargs)
