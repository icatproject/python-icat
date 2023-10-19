"""Test login to an ICAT server.
"""

from urllib.parse import urlparse
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

    client, conf = getConfig(confSection=user)
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

def test_login_icat_shorturl():
    """Test connecting to ICAT using a generic URL.  Ref. #63.
    """
    # Connect normally using the configured URL first.  If that URL
    # has a path component that is equal to the default path, shorten
    # the URL stripping the path and try again.  It should connect to
    # the same ICAT.  To test the latter, we check that a session id
    # obtained from one client is valid at the other one.
    client, conf = getConfig()
    sessionId = client.login(conf.auth, conf.credentials)
    assert sessionId
    assert sessionId == client.sessionId
    username = client.getUserName()
    o = urlparse(conf.url)
    if o[2:6] != ("/ICATService/ICAT", "", "wsdl", ""):
        pytest.skip("not a canonical path in URL")
    url = "%s://%s" % (o.scheme, o.netloc)
    gen_client = icat.Client(url, **client.kwargs)
    gen_client.autoLogout = False
    gen_client.sessionId = sessionId
    assert gen_client.getUserName() == username

def test_login_ids_shorturl():
    """Test connecting to IDS using a generic URL.  Ref. #63.
    """
    # Connect normally using the configured URL first.  If that URL
    # has a path component that is equal to the default path, shorten
    # the URL stripping the path and try again.  It should connect to
    # the same IDS.  There is no real test for the latter, but at
    # least we check that getIcatUrl() returns the same URL for both
    # clients.
    client, conf = getConfig()
    if not client.ids:
        pytest.skip("no IDS configured")
    try:
        icatURL = client.ids.getIcatUrl()
    except icat.VersionMethodError:
        pytest.skip("IDS is too old for this test")
    o = urlparse(conf.idsurl)
    if o[2:6] != ("/ids", "", "", ""):
        pytest.skip("not a canonical path in URL")
    url = "%s://%s" % (o.scheme, o.netloc)
    kwargs = dict(client.kwargs)
    kwargs['idsurl'] = url
    gen_client = icat.Client(conf.url, **kwargs)
    assert gen_client.ids.getIcatUrl() == icatURL
