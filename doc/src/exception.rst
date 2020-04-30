:mod:`icat.exception` --- Exception handling
============================================

.. py:module:: icat.exception

This module defines Python counterparts of the exceptions raised by
ICAT or IDS server, as well as exceptions raised in python-icat.

Helper
------

.. autoexception:: icat.exception._BaseException
    :members:
    :show-inheritance:

Exceptions raised by the ICAT or IDS server
-------------------------------------------

.. autoexception:: icat.exception.ServerError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATParameterError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATInternalError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATPrivilegesError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATNoObjectError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATObjectExistsError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATSessionError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATValidationError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATNotImplementedError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSBadRequestError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSDataNotOnlineError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSInsufficientPrivilegesError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSInsufficientStorageError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSInternalError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSNotFoundError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSNotImplementedError
    :members:
    :show-inheritance:

.. autofunction:: icat.exception.translateError

Exceptions raised by python-icat
--------------------------------

.. autoexception:: icat.exception.InternalError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ConfigError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.QueryNullableOrderWarning
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ClientVersionWarning
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.ICATDeprecationWarning
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.EntityTypeError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.VersionMethodError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.SearchResultError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.SearchAssertionError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.DataConsistencyError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.IDSResponseError
    :members:
    :show-inheritance:

.. autoexception:: icat.exception.GenealogyError
    :members:
    :show-inheritance:

Exception hierarchy
-------------------

The class hierarchy for the exceptions is::

  Exception
   +-- ServerError
   |    +-- ICATError
   |    |    +-- ICATParameterError
   |    |    +-- ICATInternalError
   |    |    +-- ICATPrivilegesError
   |    |    +-- ICATNoObjectError
   |    |    +-- ICATObjectExistsError
   |    |    +-- ICATSessionError
   |    |    +-- ICATValidationError
   |    |    +-- ICATNotImplementedError
   |    +-- IDSError
   |         +-- IDSBadRequestError
   |         +-- IDSDataNotOnlineError
   |         +-- IDSInsufficientPrivilegesError
   |         +-- IDSInsufficientStorageError
   |         +-- IDSInternalError
   |         +-- IDSNotFoundError
   |         +-- IDSNotImplementedError
   +-- InternalError
   +-- ConfigError
   +-- EntityTypeError
   +-- VersionMethodError
   +-- SearchResultError
   |    +-- SearchAssertionError
   +-- DataConsistencyError
   +-- IDSResponseError
   +-- GenealogyError
   +-- Warning
        +-- QueryNullableOrderWarning
        +-- ClientVersionWarning
        +-- DeprecationWarning
             +-- ICATDeprecationWarning

Here, :exc:`Exception`, :exc:`Warning`, and :exc:`DeprecationWarning`
are build-in exceptions from the Python standard library.
