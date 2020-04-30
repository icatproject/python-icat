"""Provide the AuthenticatorInfo class.
"""

from collections.abc import Sequence


__all__ = ['AuthenticatorInfo', 'LegacyAuthenticatorInfo']


class AuthenticatorInfo(Sequence):
    """A wrapper around the authenticator info as returned by the ICAT server.

    :param authInfo: authenticator information from the ICAT server as
        returned by :meth:`icat.client.Client.getAuthenticatorInfo`.
    :type authInfo: :class:`list`
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
        """Return a list of authenticator names available at the ICAT server.
        """
        return [ a.mnemonic for a in self.authInfo ]

    def getCredentialKeys(self, auth=None, hide=None):
        """Return credential keys.

        :param auth: authenticator name.  If given, return only the
            credential keys for this authenticator.  If :const:`None`,
            return credential keys for all authenticators.
        :type auth: :class:`str`
        :param hide: if given, return either only the hidden or the
            non-hidden credential keys, according to the provided
            value.  If :const:`None`, return credential keys for all
            authenticators.
        :type hide: :class:`bool`
        :return: names of credential keys.
        :rtype: :class:`set` of :class:`str`
        :raise KeyError: if `auth` is provided, but no authenticator
            by that name is defined in the authenticator information.

        .. versionchanged:: 0.17.0
            add default value for parameter `auth`.
        """
        keys = set()
        found = False
        for info in self.authInfo:
            if auth is not None and info.mnemonic != auth:
                continue
            found = True
            for k in getattr(info, "keys", []):
                if hide is None or getattr(k, "hide", False) == hide:
                    keys.add(k.name)
        if auth is not None and not found:
            raise KeyError("No such authenticator '%s'." % auth)
        return keys

class LegacyAuthenticatorInfo():
    """AuthenticatorInfo for old ICAT server.

    This is a dummy implementation to emulate AuthenticatorInfo for
    the case that the server does not support the
    :meth:`icat.client.Client.getAuthenticatorInfo` call.
    """

    def getAuthNames(self):
        """Return :const:`None`."""
        return None

    def getCredentialKeys(self, auth=None, hide=None):
        """Return credential keys.

        Dummy implementation, pretent that all authenticators expect
        `username` and `password` as credential keys, where `password`
        is marked as hidden.

        :param auth: authenticator name.  This parameter is ignored.
        :type auth: :class:`str`
        :param hide: if given, return either only the hidden or the
            non-hidden credential keys, according to the provided
            value.  If :const:`None`, return credential keys for all
            authenticators.
        :type hide: :class:`bool`
        :return: names of credential keys.
        :rtype: :class:`set` of :class:`str`

        .. versionchanged:: 0.17.0
            add default value for parameter `auth`.
        """
        if hide is not None:
            if hide:
                return {"password"}
            else:
                return {"username"}
        else:
            return {"username", "password"}
