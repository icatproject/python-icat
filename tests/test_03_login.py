"""Test login to an ICAT server.
"""

from __future__ import print_function
import pytest
import icat
import icat.config
from conftest import getConfig, tmpSessionId

# Try out three different users: root, useroffice, and acord.  Normal
# users like acord might use a different authentication plugin then
# system users as root and useroffice.  We want to try out both cases.
@pytest.mark.parametrize("user", ["root", "useroffice", "acord"])
def test_login(user):
    """Login to the ICAT server.
    """

    conf = getConfig(confSection=user)
    client = icat.Client(conf.url, **conf.client_kwargs)
    sessionId = client.login(conf.auth, conf.credentials)
    assert sessionId
    assert sessionId == client.sessionId
    username = client.getUserName()
    assert username == "%s/%s" % (conf.auth, user)
    print("\nLogged in as %s to %s." % (user, conf.url))
    client.logout()
    assert client.sessionId is None

    # Verify that the logout was effective, e.g. that the sessionId is
    # invalidated.
    with tmpSessionId(client, sessionId):
        with pytest.raises(icat.exception.ICATSessionError):
            username = client.getUserName()
