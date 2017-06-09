:mod:`icat.client` --- Provide the Client class
===============================================

.. py:module:: icat.client

.. autoclass:: icat.client.Client
    :show-inheritance:

Instance attributes:

.. attribute:: Client.apiversion

    Version of the ICAT server this client connects to.

.. attribute:: Client.autoLogout

    Flag whether the client should logout automatically on exit.

.. attribute:: Client.ids

    The :class:`icat.ids.IDSClient` instance used for IDS calls.

.. attribute:: Client.sessionId

    The session id as returned from :meth:`icat.client.Client.login`.

.. attribute:: Client.sslContext

    The :class:`ssl.SSLContext` instance that has been used to
    establish the HTTPS conection to the ICAT and IDS server.  This is
    :const:`None` for old Python versions that do not have the
    :class:`ssl.SSLContext` class.

.. attribute:: Client.typemap

    A :class:`dict` that maps type names from the ICAT WSDL schema to
    the corresponding classes in the :class:`icat.entity.Entity`
    hierarchy.

.. attribute:: Client.url

    The URL to the web service description of the ICAT server.

Class and instance methods:

.. automethod:: icat.client.Client.cleanupall

.. automethod:: icat.client.Client.cleanup

.. automethod:: icat.client.Client.add_ids

.. automethod:: icat.client.Client.new

.. automethod:: icat.client.Client.getEntityClass

.. automethod:: icat.client.Client.getEntity

ICAT API methods
................

These methods implement the ICAT API calls.  Please refer to the ICAT
Java Client documentation for details.

.. automethod:: icat.client.Client.login

.. automethod:: icat.client.Client.logout

.. automethod:: icat.client.Client.create

.. automethod:: icat.client.Client.createMany

.. automethod:: icat.client.Client.delete

.. automethod:: icat.client.Client.deleteMany

.. automethod:: icat.client.Client.get

.. automethod:: icat.client.Client.getApiVersion

.. automethod:: icat.client.Client.getAuthenticatorInfo

.. automethod:: icat.client.Client.getEntityInfo

.. automethod:: icat.client.Client.getEntityNames

.. automethod:: icat.client.Client.getProperties

.. automethod:: icat.client.Client.getRemainingMinutes

.. automethod:: icat.client.Client.getUserName

.. automethod:: icat.client.Client.getVersion

.. automethod:: icat.client.Client.isAccessAllowed

.. automethod:: icat.client.Client.refresh

.. automethod:: icat.client.Client.search

.. automethod:: icat.client.Client.update

Custom API methods
..................

.. automethod:: icat.client.Client.assertedSearch

.. automethod:: icat.client.Client.searchChunked

.. automethod:: icat.client.Client.searchUniqueKey

.. automethod:: icat.client.Client.searchMatching

.. automethod:: icat.client.Client.createUser

.. automethod:: icat.client.Client.createGroup

.. automethod:: icat.client.Client.createRules

Custom IDS methods
..................

.. automethod:: icat.client.Client.putData

.. automethod:: icat.client.Client.getData

.. automethod:: icat.client.Client.getDataUrl

.. automethod:: icat.client.Client.prepareData

.. automethod:: icat.client.Client.isDataPrepared

.. automethod:: icat.client.Client.getPreparedData

.. automethod:: icat.client.Client.getPreparedDataUrl

.. automethod:: icat.client.Client.deleteData
