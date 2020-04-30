"""Exception handling.
"""

import sys
import warnings
try:
    # Python 3.3 and newer
    from collections.abc import Mapping
except ImportError:
    # Python 2
    from collections import Mapping
import suds

__all__ = [
    # Exceptions thrown by the ICAT or IDS server
    'ServerError', 
    'ICATError', 'ICATParameterError', 'ICATInternalError', 
    'ICATPrivilegesError', 'ICATNoObjectError', 'ICATObjectExistsError', 
    'ICATSessionError', 'ICATValidationError', 'ICATNotImplementedError',
    'IDSError', 'IDSBadRequestError', 'IDSDataNotOnlineError', 
    'IDSInsufficientPrivilegesError', 'IDSInsufficientStorageError', 
    'IDSInternalError', 'IDSNotFoundError', 'IDSNotImplementedError', 
    'translateError', 
    # Internal error
    'InternalError', 
    # icat.config
    'ConfigError', 
    # icat.query
    'QueryNullableOrderWarning', 
    # icat.client, icat.entity
    'ClientVersionWarning', 'ICATDeprecationWarning', 
    'EntityTypeError', 'VersionMethodError', 'SearchResultError', 
    'SearchAssertionError', 'DataConsistencyError', 
    # icat.ids
    'IDSResponseError', 
    # icat.icatcheck
    'GenealogyError',
    ]


# =========================== base class ===========================

class _BaseException(Exception):
    """An exception that tries to suppress misleading context.

    `Exception Chaining and Embedded Tracebacks`_ has been introduced
    with Python 3.  Unfortunately the result is completely misleading
    most of the times.  This class tries to strip the context from the
    exception traceback.

    This is the common base class for for all exceptions defined in
    :mod:`icat.exception`, it is not intented to be raised directly.

    .. _Exception Chaining and Embedded Tracebacks: https://www.python.org/dev/peps/pep-3134

    """
    def __init__(self, *args):
        super(_BaseException, self).__init__(*args)
        if hasattr(self, '__cause__'):
            self.__cause__ = None


def stripCause(e):
    """Try to suppress misleading context from an exception.

    .. deprecated:: 0.14.0
       Not needed any more, embedded in
       :exc:`icat.exception._BaseException` now.
    """
    warnings.warn("stripCause() is deprecated and will be removed "
                  "in python-icat 1.0.", DeprecationWarning, 2)
    if hasattr(e, '__cause__'):
        e.__cause__ = None
    return e


# ========== Exceptions thrown by the ICAT or IDS server ===========

class ServerError(_BaseException):
    """Errors raised by either the ICAT or the IDS server.

    This is the common base class for :exc:`icat.exception.ICATError`
    and :exc:`icat.exception.IDSError`, it is not intented to be
    raised directly.
    """
    def __init__(self, error, status=None):
        """Expecept either a suds.WebFault or a Mapping with the keys 'code',
        'message', and 'offset'.
        """
        if isinstance(error, suds.WebFault):
            try:
                message = self._convertmsg(error.fault.faultstring)
            except AttributeError:
                message = self._convertmsg(str(error))
            super(ServerError, self).__init__(message)
            self.status = status
            self.message = message
            self.fault = error.fault
            self.document = error.document
            try:
                icatexception = error.fault.detail.IcatException
            except AttributeError:
                self.type = None
                self.offset = None
            else:
                self.type = getattr(icatexception, 'type', None)
                self.offset = getattr(icatexception, 'offset', None)
        elif isinstance(error, Mapping):
            # Deliberately not fetching KeyError here.  Require the
            # field to be present.  Only 'offset' is optional.
            message = self._convertmsg(error['message'])
            super(ServerError, self).__init__(message)
            self.status = status
            self.message = message
            self.type = str(error['code'])
            self.offset = error.get('offset', None)
        elif isinstance(error, basestring):
            # For compatibility with other exception classes, also
            # allow the constructor to be called with just a message
            # string as argument.
            message = self._convertmsg(error)
            super(ServerError, self).__init__(message)
            self.status = None
            self.message = message
            self.type = None
            self.offset = None
        else:
            raise TypeError("Invalid argument type '%s'." % type(error))

        # Sanitize offset: we get is as a string from the HTTP
        # response, but it is supposed to be an int.  If the offset is
        # negativ, it has no meaning and should be set to None.
        if self.offset is not None:
            self.offset = int(self.offset)
            if self.offset < 0:
                self.offset = None

    def _convertmsg(self, msg):
        # msg may be a str, a suds.sax.text.Text instance, or (only
        # for Python 2) an unicode instance.  In Python 2, we must
        # convert it to a pure ascii string for Exception.  In Python
        # 3, we convert it to a str.  It may still contain non-ascii
        # chars, but this is ok for Exception in Python 3.
        if sys.version_info < (3, 0):
            return msg.encode('ascii', 'replace')
        else:
            return str(msg)


class ICATError(ServerError):
    """Base class for the errors raised by the ICAT server.
    """
    pass

class ICATParameterError(ICATError):
    """Generally indicates a problem with the arguments made to a
    call.
    """
    pass

class ICATInternalError(ICATError):
    """May be caused by network problems, database problems, GlassFish
    problems or bugs in ICAT.
    """
    pass

class ICATPrivilegesError(ICATError):
    """Indicates that the authorization rules have not matched your
    request.
    """
    pass

class ICATNoObjectError(ICATError):
    """Is thrown when something is not found.
    """
    pass

class ICATObjectExistsError(ICATError):
    """Is thrown when trying to create something but there is already
    one with the same values of the constraint fields.
    """
    pass

class ICATSessionError(ICATError):
    """Is used when the sessionId you have passed into a call is not
    valid or if you are unable to authenticate.
    """
    pass

class ICATValidationError(ICATError):
    """Marks an exception which was thrown instead of placing the
    database in an invalid state.
    """
    pass

class ICATNotImplementedError(ICATError):
    """
    """
    # Added in icat.server 4.6, but not documented.
    pass

IcatExceptionTypeMap = {
    "BAD_PARAMETER": ICATParameterError,
    "INTERNAL": ICATInternalError,
    "INSUFFICIENT_PRIVILEGES": ICATPrivilegesError,
    "NO_SUCH_OBJECT_FOUND": ICATNoObjectError,
    "OBJECT_ALREADY_EXISTS": ICATObjectExistsError,
    "SESSION": ICATSessionError,
    "VALIDATION": ICATValidationError,
    "NOT_IMPLEMENTED": ICATNotImplementedError,
}
"""Map exception types thrown by the ICAT server to Python classes."""


class IDSError(ServerError):
    """Base class for the errors raised by the IDS server.
    """
    pass

class IDSBadRequestError(IDSError):
    """Any kind of bad input parameter.
    """
    pass

class IDSDataNotOnlineError(IDSError):
    """The requested data are not on line.
    """
    pass

class IDSInsufficientPrivilegesError(IDSError):
    """You are denied access to the data.
    """
    pass

class IDSInsufficientStorageError(IDSError):
    """There is not sufficient physical storage or you have exceeded some quota.
    """
    pass

class IDSInternalError(IDSError):
    """Some kind of failure in the server or in communicating with the server.
    """
    pass

class IDSNotFoundError(IDSError):
    """The requested data do not exist.
    """
    pass

class IDSNotImplementedError(IDSError):
    """Use of some functionality that is not supported by the implementation.
    """
    pass

IDSExceptionTypeMap = {
    "BadRequestException": IDSBadRequestError,
    "DataNotOnlineException": IDSDataNotOnlineError,
    "InsufficientPrivilegesException": IDSInsufficientPrivilegesError,
    "InsufficientStorageException": IDSInsufficientStorageError,
    "InternalException": IDSInternalError,
    "NotFoundException": IDSNotFoundError,
    "NotImplementedException": IDSNotImplementedError,
}
"""Map IDS error codes to Python classes."""


def translateError(error, status=None, server="ICAT"):
    """Translate an error from ICAT or IDS to the corresponding exception."""
    if server == "ICAT":
        typemap = IcatExceptionTypeMap
        BaseClass = ICATError
    elif server == "IDS":
        typemap = IDSExceptionTypeMap
        BaseClass = IDSError
    else:
        raise ValueError("Invalid server '%s'." % server)

    if isinstance(error, suds.WebFault):
        try:
            Class = typemap[error.fault.detail.IcatException.type]
        except AttributeError:
            Class = BaseClass
    elif isinstance(error, Mapping):
        Class = typemap[error['code']]
    else:
        raise TypeError("Invalid argument type '%s'." % type(error))

    return Class(error, status)


# ========================= Internal error =========================

class InternalError(_BaseException):
    """An error that reveals a bug in python-icat.
    """
    pass


# ================ Exceptions raised in icat.config ================

class ConfigError(_BaseException):
    """Error getting configuration options."""
    pass


# ================ Exceptions raised in icat.query =================

class QueryNullableOrderWarning(Warning):
    """Warn about using a nullable relation for ordering.
    """
    def __init__(self, attr):
        msg = ("ordering on a nullable relation implicitly "
               "adds a '%s IS NOT NULL' condition." % attr)
        super(QueryNullableOrderWarning, self).__init__(msg)


# ======== Exceptions raised in icat.client and icat.entity ========

class ClientVersionWarning(Warning):
    """Warn that the version of the ICAT server is not supported by
    the client.
    """
    def __init__(self, version=None, comment=None):
        if version is None:
            icatstr = "this ICAT version"
        else:
            icatstr = "ICAT version %s" % version
        if comment is None:
            msg = ("%s is not supported, "
                   "expect problems and weird behavior!" % icatstr)
        else:
            msg = ("%s is not supported (%s), "
                   "expect problems and weird behavior!" % (icatstr, comment))
        super(ClientVersionWarning, self).__init__(msg)

class ICATDeprecationWarning(DeprecationWarning):
    """Warn about using an API feature that may get removed in future ICAT
    server versions.
    """
    def __init__(self, feature, version=None):
        if version is None:
            icatstr = "a future ICAT version"
        else:
            icatstr = "ICAT version %s" % version
        msg = ("%s has been deprecated and is expected to get removed in %s." 
               % (feature, icatstr))
        super(ICATDeprecationWarning, self).__init__(msg)

class EntityTypeError(_BaseException):
    """An invalid entity type has been used."""
    pass

class VersionMethodError(_BaseException):
    """Call of an API method that is not supported in the version
    of the server.
    """
    def __init__(self, method, version=None, service="ICAT"):
        if version is None:
            icatstr = "this %s version" % service
        else:
            icatstr = "%s version %s" % (service, version)
        msg = ("%s is not supported in %s." % (method, icatstr))
        super(VersionMethodError, self).__init__(msg)

class SearchResultError(_BaseException):
    """A search result does not conform to what should have been expected.
    """
    pass

class SearchAssertionError(SearchResultError):
    """A search result does not conform to an assertion.

    This exception is thrown when the number of objects found on a
    search does not lie within the bounds of an assertion, see
    :meth:`icat.client.Client.assertedSearch`.
    """
    def __init__(self, query, assertmin, assertmax, num):
        # The most common case will be assertmin > 0 and num = 0.
        # Formulate a convenient message for this case and a generic
        # one for all other cases.
        if num == 0:
            msg = 'Nothing found on query: "%s"' % query
        elif num < assertmin:
            msg = ('Less objects found then expected (%d < %d) on query: "%s"'
                   % (num, assertmin, query))
        elif assertmax == 1:
            msg = ('Search result is not unique, '
                   '%d objects found on query: "%s"'
                   % (num, query))
        else:
            msg = ('Number of objects found (%d) is not within '
                   'the expected bounds between %d and %d on query: "%s"'
                   % (num, assertmin, assertmax, query))
        super(SearchAssertionError, self).__init__(msg)
        self.query = query
        self.assertmin = assertmin
        self.assertmax = assertmax
        self.num = num

class DataConsistencyError(_BaseException):
    """Some data is not consistent with rules or constraints."""
    pass


# ================= Exceptions raised in icat.ids ==================

class IDSResponseError(_BaseException):
    """The response from the IDS was not what should have been expected.
    """
    pass


# ============== Exceptions raised in icat.icatcheck ===============

class GenealogyError(_BaseException):
    """Error in the genealogy of entity types.

    .. deprecated:: 0.17
       Only used in :mod:`icat.icatcheck` which in turn is deprecated.
    """
    pass

