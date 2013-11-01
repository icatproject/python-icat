"""Common Gateway Interface support for ICAT.

This module provides tools for writing CGI scripts acting as ICAT clients.
"""

from Cookie import SimpleCookie
import os
import re
import icat.client
from icat.exception import ICATError, ICATSessionError


class SessionCookie(SimpleCookie):
    """A cookie to store an ICAT session id.

    Extend C{SimpleCookie} by the attribute C{sessionId}.  Setting
    this attribute will set the session id in the cookie, getting it
    will retrieve its value from the cookie.
    """

    def __init__(self):
        if 'HTTP_COOKIE' in os.environ:
            super(SessionCookie, self).__init__(os.environ['HTTP_COOKIE'])
        else:
            super(SessionCookie, self).__init__()
        self.cookieName = 'ICATSESSIONID'
        self.path = '/'
        self.secure = True
        self.sidre = r'^[-a-zA-Z0-9]+$'

    def __getattr__(self, attr):
        if attr == 'sessionId':
            if self.cookieName in self:
                sessionId = self[self.cookieName].value
                if re.match(self.sidre, sessionId):
                    return sessionId
                else:
                    return None
            else:
                return None
        else:
            return super(SessionCookie, self).__getattr__(attr)

    def __setattr__(self, attr, value):
        if attr == 'sessionId':
            if value is None:
                self[self.cookieName] = ""
                self[self.cookieName]['max-age'] = "0"
            elif re.match(self.sidre, value):
                self[self.cookieName] = value
            else:
                raise ValueError("Invalid sessionId '%s'." % value)
            self[self.cookieName]['path'] = self.path
            if self.secure:
                self[self.cookieName]['secure'] = "1"
        else:
            super(SessionCookie, self).__setattr__(attr, value)


class Session(object):
    """A persisting ICAT session.

    Manage an ICAT session that persist over the life time of the
    script.  The session id is stored in a L{SessionCookie}.
    """

    def __init__(self, url, 
                 cookieName='ICATSESSIONID', cookiePath='/', secure=True):
        """Initialize the instance.

        Connect to the ICAT service at the given URL.  Get the status
        of the session from the L{SessionCookie}.
        """
        super(Session, self).__init__()
        self.client = icat.client.Client(url)
        self.client.autoLogout = False
        self.cookie = SessionCookie()
        self.cookie.cookieName = cookieName
        self.cookie.path = cookiePath
        self.cookie.secure = secure

        self.client.sessionId = self.cookie.sessionId
        self.sessionError = None

    def isActive(self):
        """Check whether there is an active session."""
        if self.client.sessionId:
            # Query the user name in order to test wether the
            # sessionId is valid.
            try:
                self.username = self.client.getUserName()
            except ICATSessionError as e:
                self.sessionError = e.message
                self.client.sessionId = None
                self.cookie.sessionId = None
                return False
            else:
                self.sessionError = None
                return True
        else:
            return False

    def login(self, auth, username, password):
        """Log in with username and password and start a session."""
        credentials = { 'username':username,
                        'password':password }
        self.cookie.sessionId = self.client.login(auth, credentials)
        self.sessionError = None

    def logout(self):
        """Log out and terminate the session."""
        # Ignore errors from logging out: it may happen that a
        # spurious sessionId is left as a cookie in the user's
        # browser.  In such cases, ICAT will raise an exception
        # "Unable to find user by sessionid".  But that's ok, we
        # wanted to go anyway.
        # In the theory, we should catch an ICATSessionError here, but
        # see ICAT Issue 127.
        try:
            self.client.logout()
        except ICATError:
            pass
        self.cookie.sessionId = None
        self.sessionError = None
