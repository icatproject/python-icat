"""Provide the AuthenticatorInfo class.
"""

try:
    # Python 3.3 and newer
    from collections.abc import Sequence
except ImportError:
    # Python 2
    from collections import Sequence


__all__ = ['AuthenticatorInfo', 'LegacyAuthenticatorInfo']


class AuthenticatorInfo(Sequence):
    """A wrapper around the authenticator info as returned by the ICAT server.
    """

    def __init__(self, authInfo):
        self.authInfo = authInfo

    def __len__(self):
        return len(self.authInfo)

    def __getitem__(self, index):
        return self.authInfo.__getitem__(index)

    def __str__(self):
        return str(self.authInfo)

    def getAuthNames(self):
        return [ a.mnemonic for a in self.authInfo ]

    def getCredentialKeys(self, auth, hide=None):
        keys = set()
        found = False
        for info in self.authInfo:
            if auth and info.mnemonic != auth:
                continue
            found = True
            for k in getattr(info, "keys", []):
                if hide is None or getattr(k, "hide", False) == hide:
                    keys.add(k.name)
        if auth and not found:
            raise KeyError("No such authenticator '%s'." % auth)
        return keys

class LegacyAuthenticatorInfo(object):
    """AuthenticatorInfo for old ICAT server.

    Emulate AuthenticatorInfo for the case that there is no
    authenticator info from the server.  Pretent that all
    authenticators expect 'username' and 'password' as credential
    keys. 
    """

    def getAuthNames(self):
        return None

    def getCredentialKeys(self, auth, hide=None):
        if hide is not None:
            if hide:
                return set(["password"])
            else:
                return set(["username"])
        else:
            return set(["username", "password"])
