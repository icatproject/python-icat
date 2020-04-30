:mod:`icat.client` --- Provide the Client class
===============================================

.. py:module:: icat.client

The :mod:`icat.client` defines the :class:`~icat.client.Client` class
that manages the interaction with an ICAT service as a client.

.. autoclass:: icat.client.Client
    :show-inheritance:

    **Class attributes**

    .. attribute:: Register

        The register of all active clients.

    .. attribute:: AutoRefreshRemain

        Number of minutes to leave in the session before automatic
        refresh should be called.

    **Instance attributes**

    .. attribute:: url

        The URL to the web service description of the ICAT server.

    .. attribute:: kwargs

        A copy of the kwargs used in the constructor.

    .. attribute:: apiversion

        Version of the ICAT server this client connects to.

    .. attribute:: autoLogout

        Flag whether the client should logout automatically on exit.

    .. attribute:: ids

        The :class:`icat.ids.IDSClient` instance used for IDS calls.

    .. attribute:: sessionId

        The session id as returned from :meth:`login`.

    .. attribute:: sslContext

        The :class:`ssl.SSLContext` instance that has been used to
        establish the HTTPS conection to the ICAT and IDS server.
        This is :const:`None` for old Python versions that do not have
        the :class:`ssl.SSLContext` class.

    .. attribute:: typemap

        A :class:`dict` that maps type names from the ICAT WSDL schema
        to the corresponding classes in the
        :class:`icat.entity.Entity` hierarchy.

    **Class and instance methods**

    .. automethod:: cleanupall

    .. automethod:: cleanup

    .. automethod:: add_ids

    .. automethod:: clone

    .. automethod:: new

    .. automethod:: getEntityClass

    .. automethod:: getEntity

    **ICAT API methods**

    These methods implement the low level API calls of the ICAT
    server.  See the documentation in the `ICAT SOAP Manual`_.  (Note:
    the Python examples in that manual are based on plain Suds, not on
    python-icat.)

    .. automethod:: login

    .. automethod:: logout

    .. automethod:: create

    .. automethod:: createMany

    .. automethod:: delete

    .. automethod:: deleteMany

    .. automethod:: get

    .. automethod:: getApiVersion

    .. automethod:: getAuthenticatorInfo

    .. automethod:: getEntityInfo

    .. automethod:: getEntityNames

    .. automethod:: getProperties

    .. automethod:: getRemainingMinutes

    .. automethod:: getUserName

    .. automethod:: getVersion

    .. automethod:: isAccessAllowed

    .. automethod:: refresh

    .. automethod:: search

    .. automethod:: update

    **Custom API methods**

    These higher level methods build on top of the ICAT API methods.

    .. automethod:: autoRefresh

    .. automethod:: assertedSearch

    .. automethod:: searchChunked

    .. automethod:: searchUniqueKey

    .. automethod:: searchMatching

    .. automethod:: createUser

    .. automethod:: createGroup

    .. automethod:: createRules

    **Custom IDS methods**

    These methods provide the most commonly needed IDS functionality
    and build on top of the low level IDS API methods provided by
    :class:`icat.ids.IDSClient`.

    .. automethod:: putData

    .. automethod:: getData

    .. automethod:: getDataUrl

    .. automethod:: prepareData

    .. automethod:: isDataPrepared

    .. automethod:: deleteData

.. _ICAT SOAP Manual: https://repo.icatproject.org/site/icat/server/4.10.0/soap.html
