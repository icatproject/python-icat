"""Exception handling.
"""

import suds

__all__ = [
    # helper
    'stripCause', 
    # Internal error
    'InternalError', 
    # Exceptions thrown by the ICAT server
    'ICATError', 'ICATParameterError', 'ICATInternalError', 
    'ICATPrivilegesError', 'ICATNoObjectError', 'ICATObjectExistsError', 
    'ICATSessionError', 'ICATValidationError', 
    'translateError', 
    # icat.client, icat.entity
    'ClientVersionWarning', 'VersionMethodError', 'SearchResultError', 
    'SearchAssertionError', 'DataConsistencyError', 
    # IDS
    'IDSError', 'IDSResponseError', 
    'IDSServerError', 'IDSBadRequestError', 'IDSDataNotOnlineError', 
    'IDSInsufficientPrivilegesError', 'IDSInsufficientStorageError', 
    'IDSInternalError', 'IDSNotFoundError', 'IDSNotImplementedError', 
    'translateIDSError', 
    # icat.config
    'ConfigError', 
    # icat.icatcheck
    'GenealogyError',
    ]


# ======================== helper function =========================

def stripCause(e):
    """Try to suppress misleading context from an exception.

    `Exception Chaining and Embedded Tracebacks`_ has been introduced
    with Python 3.  Unfortunately the result is completely misleading
    most of the times.  Try to suppress the context from the exception
    traceback.  This works with Python 3.3 and newer, but has no
    effect with Python 3.1 and 3.2.

    .. _Exception Chaining and Embedded Tracebacks: http://legacy.python.org/dev/peps/pep-3134/
    """
    if hasattr(e, '__cause__'):
        e.__cause__ = None
    return e

# ========================= Internal error =========================

class InternalError(Exception):
    """An error that reveals a bug in python-icat.
    """
    pass

# ============== Exceptions thrown by the ICAT server ==============

class ICATError(Exception):
    """Base class for the errors raised by the ICAT server.
    """
    def __init__(self, webfault):
        try:
            msg = webfault.fault.faultstring
        except AttributeError:
            msg = str(webfault)
        super(ICATError, self).__init__(msg)
        self.fault = webfault.fault
        self.document = webfault.document
        try:
            icatexception = webfault.fault.detail.IcatException
        except AttributeError:
            pass
        else:
            self.message = getattr(icatexception, 'message', None)
            self.offset = getattr(icatexception, 'offset', None)
            self.type = getattr(icatexception, 'type', None)

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

IcatExceptionTypeMap = {
    "BAD_PARAMETER": ICATParameterError,
    "INTERNAL": ICATInternalError,
    "INSUFFICIENT_PRIVILEGES": ICATPrivilegesError,
    "NO_SUCH_OBJECT_FOUND": ICATNoObjectError,
    "OBJECT_ALREADY_EXISTS": ICATObjectExistsError,
    "SESSION": ICATSessionError,
    "VALIDATION": ICATValidationError,
}
"""Map exception types thrown by the ICAT server to Python classes."""

def translateError(error):
    """Translate a suds.WebFault into the corresponding ICATError."""
    if isinstance(error, suds.WebFault):
        try:
            Class = IcatExceptionTypeMap[error.fault.detail.IcatException.type]
        except AttributeError:
            Class = ICATError
        return stripCause(Class(error))
    else:
        raise TypeError("Invalid argument type '%s'." % type(error))


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

class VersionMethodError(Exception):
    """Call of an ICAT API method that is not supported in the version
    of the ICAT server.
    """
    def __init__(self, method, version=None):
        if version is None:
            icatstr = "this ICAT version"
        else:
            icatstr = "ICAT version %s" % version
        msg = ("%s is not supported in %s." % (method, icatstr))
        super(VersionMethodError, self).__init__(msg)

class SearchResultError(Exception):
    """A search result does not conform to what should have been expected.
    """
    pass

class SearchAssertionError(SearchResultError):
    """A search result does not conform to an assertion.

    This exception is thrown when the number of objects found on a
    search does not lie within the bounds of an assertion.
    """
    def __init__(self, query, assertmin, assertmax, num):
        # The most common case will be assertmin > 0 and num = 0.
        # Formulate a convenient message for this case and a generic
        # one for all other cases.
        if num == 0:
            msg = 'Nothing found on query: "%s"' % query
        elif assertmax is None:
            msg = ('Number of objects found (%d) is not within '
                   'the expected bounds between %d and infinity '
                   'on query: "%s"'
                   % (num, assertmin, query))
        else:
            msg = ('Number of objects found (%d) is not within '
                   'the expected bounds between %d and %d on query: "%s"'
                   % (num, assertmin, assertmax, query))
        super(SearchAssertionError, self).__init__(msg)
        self.query = query
        self.assertmin = assertmin
        self.assertmax = assertmax
        self.num = num

class DataConsistencyError(Exception):
    """Some data is not consistent with rules or constraints."""
    pass

# ==== Exceptions raised while talking to an ICAT Data Service =====

class IDSError(Exception):
    """Base class for the errors raised while talking to IDS.
    """
    pass

class IDSResponseError(IDSError):
    """The response from the IDS was not what should have been expected.
    """
    pass

class IDSServerError(IDSError):
    """Error raised by the by the IDS.
    """
    def __init__(self, status, code, message):
        super(IDSServerError, self).__init__(message)
        self.code = status
        self.idscode = code
        self.idsmessage = message

class IDSBadRequestError(IDSServerError):
    pass

class IDSDataNotOnlineError(IDSServerError):
    pass

class IDSInsufficientPrivilegesError(IDSServerError):
    pass

class IDSInsufficientStorageError(IDSServerError):
    pass

class IDSInternalError(IDSServerError):
    pass

class IDSNotFoundError(IDSServerError):
    pass

class IDSNotImplementedError(IDSServerError):
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

def translateIDSError(status, code, message):
    """Create the corresponding IDSServerError from an IDS error code."""
    try:
        Class = IDSExceptionTypeMap[code]
    except AttributeError:
        Class = IDSServerError
    return Class(status, code, message)

# ================ Exceptions raised in icat.config ================

class ConfigError(Exception):
    """Error getting configuration options."""
    pass

# ============== Exceptions raised in icat.icatcheck ===============

class GenealogyError(Exception):
    """Error in the genealogy of entity types."""
    pass
