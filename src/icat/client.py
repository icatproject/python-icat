"""Provide the Client class.

This is the only module that needs to be imported to use the icat.
"""

import atexit
import logging
import os
from pathlib import Path
import re
import time
import urllib.parse
from warnings import warn
import weakref

import suds
import suds.client
import suds.sudsobject

from .entities import getTypeMap
from .entity import Entity
from .exception import *
from .helper import (Version, simpleqp_unquote, parse_attr_val,
                     ms_timestamp, disable_logger)
from .ids import *
from .query import Query
from .sslcontext import create_ssl_context, HTTPSTransport

__all__ = ['Client']

log = logging.getLogger(__name__)

def _complete_url(url, default_path="/ICATService/ICAT?wsdl"):
    if not url:
        return url
    o = urllib.parse.urlparse(url)
    if o.path or o.query:
        return url
    return "%s://%s%s" % (o.scheme, o.netloc, default_path)

class Client(suds.client.Client):
 
    """A client accessing an ICAT service.

    This is a subclass of :class:`suds.client.Client` and inherits
    most of its behavior.  It adds methods for the instantiation of
    ICAT entities and implementations of the ICAT API methods.

    :param url: The URL pointing to the WSDL of the ICAT service.  If
        the URL does not contain a path, e.g. contains only a URL
        scheme and network location part, a default path is assumend.
    :type url: :class:`str`
    :param idsurl: The URL pointing to the IDS service.  If set, an
        :class:`icat.ids.IDSClient` instance will be created.
    :type idsurl: :class:`str`
    :param checkCert: Flag whether the server's SSL certificate should
        be verified if connecting ICAT with HTTPS.
    :type checkCert: :class:`bool`
    :param caFile: Path to a file of concatenated trusted CA
        certificates.  If neither `caFile` nor `caPath` is set, the
        system's default certificates will be used.
    :type caFile: :class:`str`
    :param caPath: Path to a directory containing trusted CA
        certificates.  If neither `caFile` nor `caPath` is set, the
        system's default certificates will be used.
    :type caPath: :class:`str`
    :param sslContext: A SSL context describing various SSL options to
        be used in HTTPS connections.  If set, this will override
        `checkCert`, `caFile`, and `caPath`.
    :type sslContext: :class:`ssl.SSLContext`
    :param proxy: HTTP proxy settings.  A map with the keys
        `http_proxy` and `https_proxy` and the URL of the respective
        proxy to use as values.
    :type proxy: :class:`dict`
    :param kwargs: additional keyword arguments that will be passed to
        :class:`suds.client.Client`, see :class:`suds.options.Options`
        for details.
    """

    Register = weakref.WeakValueDictionary()
    """The register of all active clients.

    .. versionchanged:: 1.1.0
        changed type to :class:`weakref.WeakValueDictionary`.
    """

    AutoRefreshRemain = 30
    """Number of minutes to leave in the session before automatic refresh
    should be called.
    """

    @classmethod
    def cleanupall(cls):
        """Cleanup all class instances.

        Call :meth:`~icat.client.Client.cleanup` on all registered
        class instances, e.g. on all clients that have not yet been
        cleaned up.
        """
        for r in list(cls.Register.valuerefs()):
            c = r()
            if c:
                c.cleanup()

    def _schedule_auto_refresh(self, t=None):
        now = time.time()
        if t == "never":
            # Schedule it very far in the future.  This is just to
            # make sure that self._next_refresh has a formally valid
            # value.
            year = 365.25 * (24 * 60 * 60)
            self._next_refresh = now + year
        elif t:
            self._next_refresh = t
        else:
            wait = max(self.getRemainingMinutes() - self.AutoRefreshRemain, 0)
            self._next_refresh = now + 60*wait

    def __init__(self, url, idsurl=None,
                 checkCert=True, caFile=None, caPath=None, sslContext=None,
                 proxy=None, **kwargs):

        """Initialize the client.

        Extend the inherited constructor.  Query the API version from
        the ICAT server and initialize the typemap accordingly.
        """

        self.url = _complete_url(url)
        self.kwargs = dict(kwargs)
        self.kwargs['idsurl'] = idsurl
        self.kwargs['checkCert'] = checkCert
        self.kwargs['caFile'] = caFile
        self.kwargs['caPath'] = caPath
        self.kwargs['sslContext'] = sslContext
        self.kwargs['proxy'] = proxy
        idsurl = _complete_url(idsurl, default_path="/ids")

        self.apiversion = None
        self.entityInfoCache = {}
        self.typemap = None
        self.ids = None
        self.sessionId = None
        self.autoLogout = True
        self._schedule_auto_refresh("never")

        if sslContext:
            self.sslContext = sslContext
        else:
            self.sslContext = create_ssl_context(checkCert, caFile, caPath)

        if not proxy:
            proxy = {}
        kwargs['transport'] = HTTPSTransport(self.sslContext, proxy=proxy)
        super().__init__(self.url, **kwargs)
        self.apiversion = Version(self.getApiVersion())
        log.debug("Connect to %s, ICAT version %s", url, self.apiversion)

        if self.apiversion < '4.3.0':
            warn(ClientVersionWarning(self.apiversion, "too old"))
        self.typemap = getTypeMap(self)

        if idsurl:
            self.add_ids(idsurl)
        self.Register[id(self)] = self

    def __del__(self):
        """Call :meth:`~icat.client.Client.cleanup`."""
        self.cleanup()

    def cleanup(self):
        """Release resources allocated by the client.

        Logout from the active ICAT session (if :attr:`autoLogout` is
        :const:`True`).  The client should not be used any more after
        calling this method.
        """
        if self.autoLogout:
            self.logout()
        if id(self) in self.Register:
            del self.Register[id(self)]

    def add_ids(self, url, proxy=None):
        """Add the URL to an ICAT Data Service."""
        if proxy is None:
            proxy = self.options.proxy
        idsargs = {}
        if self.sessionId:
            idsargs['sessionId'] = self.sessionId
        idsargs['sslContext'] = self.sslContext
        if proxy:
            idsargs['proxy'] = proxy
        self.ids = IDSClient(url, **idsargs)

    def __setattr__(self, attr, value):
        super().__setattr__(attr, value)
        if attr == 'sessionId' and self.ids:
            self.ids.sessionId = self.sessionId

    def clone(self):
        """Create a clone.

        Return a clone of the :class:`Client` object.  That is, a
        client that connects to the same ICAT server and has been
        created with the same kwargs.  The clone will be in the state
        as returned from the constructor.  In particular, it does not
        share the same session if this client object is logged in.

        :return: a clone of the client object.
        :rtype: :class:`Client`
        """
        Class = type(self)
        return Class(self.url, **self.kwargs)


    def _has_wsdl_type(self, name):
        """Check if this client's WSDL defines a particular type name.
        """
        with disable_logger("suds.resolver"):
            return self.factory.resolver.find(name)

    def new(self, obj, **kwargs):

        """Instantiate a new :class:`icat.entity.Entity` object.

        If obj is a Suds instance object or a string, lookup the
        corresponding entity class in the :attr:`typemap`.  If obj is
        a string, this lookup is case insensitive and a new entity
        object is instantiated.  If obj is a Suds instance object, an
        entity object corresponding to this instance object is
        instantiated.  If obj is :const:`None`, do nothing and return
        :const:`None`.
        
        :param obj: either a Suds instance object, a name of an
            instance type, or :const:`None`.
        :type obj: :class:`suds.sudsobject.Object` or :class:`str`
        :param kwargs: attributes passed to the constructor of
            :class:`icat.entity.Entity`.
        :return: the new entity object or :const:`None`.
        :rtype: :class:`icat.entity.Entity`
        :raise EntityTypeError: if obj is neither a valid instance
            object, nor a valid name of an entity type, nor None.

        .. versionchanged:: 1.0.0
            if the `obj` argument is a string, it is taken case
            insensitive.
        """

        if isinstance(obj, suds.sudsobject.Object):
            # obj is already an instance, use it right away
            instance = obj
            instancetype = instance.__class__.__name__
            try:
                Class = self.typemap[instancetype]
            except KeyError:
                raise EntityTypeError("Invalid instance type '%s'." 
                                      % instancetype)
        elif isinstance(obj, str):
            # obj is the name of an instance type, create the instance
            try:
                Class = self.typemap[obj.lower()]
            except KeyError:
                raise EntityTypeError("Invalid instance type '%s'." 
                                      % obj)
            instancetype = Class.getInstanceName()
            instance = self.factory.create(instancetype)
            # The factory creates a whole tree of dummy objects for
            # all relationships of the instance object and the
            # relationships of the related objects and so on.  These
            # dummy objects are of no use, discard them.
            for r in (Class.InstRel | Class.InstMRel):
                delattr(instance, r)
        elif obj is None:
            return None
        else:
            raise EntityTypeError("Invalid argument type '%s'." % type(obj))

        if Class is None:
            raise EntityTypeError("Instance type '%s' is not supported." 
                                  % instancetype)
        if Class.BeanName is None:
            raise EntityTypeError("Refuse to create an instance of "
                                  "abstract type '%s'." % instancetype)

        return Class(self, instance, **kwargs)

    def getEntityClass(self, name):
        """Return the Entity class corresponding to a BeanName.
        """
        for c in self.typemap.values():
            if name == c.BeanName:
                return c
        else:
            raise EntityTypeError("Invalid entity type '%s'." % name)

    def getEntity(self, obj):
        """Get the corresponding :class:`icat.entity.Entity` for an object.

        if obj is a `fieldSet`, return a tuple of the fields.  If obj
        is any other Suds instance object, create a new entity object
        with :meth:`~icat.client.Client.new`.  Otherwise do nothing
        and return obj unchanged.
        
        :param obj: either a Suds instance object or anything.
        :type obj: :class:`suds.sudsobject.Object` or any type
        :return: the new entity object or obj.
        :rtype: :class:`tuple` or :class:`icat.entity.Entity` or any type

        .. versionchanged:: 0.18.0
            add support of `fieldSet`.

        .. versionchanged:: 0.18.1
            changed the return type from :class:`list` to
            :class:`tuple` in the case of `fieldSet`.
        """
        if obj.__class__.__name__ == 'fieldSet':
            return tuple(obj.fields)
        elif isinstance(obj, suds.sudsobject.Object):
            return self.new(obj)
        else:
            return obj

    # ==================== ICAT API methods ====================

    def login(self, auth, credentials):
        self.logout()
        cred = self.factory.create("credentials")
        for k in credentials:
            cred.entry.append({ 'key': k, 'value': credentials[k] })
        try:
            self.sessionId = self.service.login(auth, cred)
        except suds.WebFault as e:
            raise translateError(e)
        self._schedule_auto_refresh()
        return self.sessionId

    def logout(self):
        if self.sessionId:
            try:
                try:
                    self.service.logout(self.sessionId)
                except suds.WebFault as e:
                    raise translateError(e)
                finally:
                    self.sessionId = None
            except ICATSessionError:
                # silently ignore ICATSessionError, e.g. an expired session.
                pass

    def create(self, bean):
        if getattr(bean, 'validate', None):
            bean.validate()
        try:
            return self.service.create(self.sessionId, Entity.getInstance(bean))
        except suds.WebFault as e:
            raise translateError(e)

    def createMany(self, beans):
        for b in beans:
            if getattr(b, 'validate', None):
                b.validate()
        try:
            return self.service.createMany(self.sessionId, Entity.getInstances(beans))
        except suds.WebFault as e:
            raise translateError(e)

    def delete(self, bean):
        try:
            self.service.delete(self.sessionId, Entity.getInstance(bean))
        except suds.WebFault as e:
            raise translateError(e)

    def deleteMany(self, beans):
        try:
            self.service.deleteMany(self.sessionId, Entity.getInstances(beans))
        except suds.WebFault as e:
            raise translateError(e)

    def get(self, query, primaryKey):
        try:
            instance = self.service.get(self.sessionId, str(query), primaryKey)
            return self.getEntity(instance)
        except suds.WebFault as e:
            raise translateError(e)

    def getApiVersion(self):
        try:
            return self.service.getApiVersion()
        except suds.WebFault as e:
            raise translateError(e)

    def getAuthenticatorInfo(self):
        try:
            return self.service.getAuthenticatorInfo()
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.9.0':
                raise VersionMethodError("getAuthenticatorInfo", 
                                         self.apiversion)
            else:
                raise

    def getEntityInfo(self, beanName):
        if self.entityInfoCache and beanName in self.entityInfoCache:
            return self.entityInfoCache[beanName]
        try:
            info = self.service.getEntityInfo(beanName)
        except suds.WebFault as e:
            raise translateError(e)
        if isinstance(self.entityInfoCache, dict):
            self.entityInfoCache[beanName] = info
        return info

    def getEntityNames(self):
        try:
            return self.service.getEntityNames()
        except suds.WebFault as e:
            raise translateError(e)

    def getProperties(self):
        try:
            return self.service.getProperties(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)

    def getRemainingMinutes(self):
        try:
            return self.service.getRemainingMinutes(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)

    def getUserName(self):
        try:
            return self.service.getUserName(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)

    def getVersion(self):
        try:
            return self.service.getVersion()
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            return self.getApiVersion()

    def isAccessAllowed(self, bean, accessType):
        try:
            return self.service.isAccessAllowed(self.sessionId, Entity.getInstance(bean), accessType)
        except suds.WebFault as e:
            raise translateError(e)

    def refresh(self):
        try:
            self.service.refresh(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)

    def search(self, query):
        try:
            instances = self.service.search(self.sessionId, str(query))
            return [self.getEntity(i) for i in instances]
        except suds.WebFault as e:
            raise translateError(e)

    def update(self, bean):
        try:
            self.service.update(self.sessionId, Entity.getInstance(bean))
        except suds.WebFault as e:
            raise translateError(e)


    # =================== custom API methods ===================

    def autoRefresh(self):
        """Call :meth:`~icat.client.Client.refresh` only if needed.

        Call :meth:`~icat.client.Client.refresh` if less then
        :attr:`AutoRefreshRemain` minutes remain in the current
        session.  Do not make any client calls if not.  This method is
        supposed to be very cheap if enough time remains in the
        session so that it may be called often in a loop without
        causing too much needless load.
        """
        if time.time() > self._next_refresh:
            self.refresh()
            self._schedule_auto_refresh()

    def assertedSearch(self, query, assertmin=1, assertmax=1):
        """Search with an assertion on the result.

        Perform a search and verify that the number of items found
        lies within the bounds of `assertmin` and `assertmax`.  Raise
        an error if this assertion fails.

        :param query: the search query.
        :type query: :class:`icat.query.Query` or :class:`str`
        :param assertmin: minimum number of expected results.
        :type assertmin: :class:`int`
        :param assertmax: maximum number of expected results.  A value
            of :const:`None` is treated as infinity.
        :type assertmax: :class:`int`
        :return: search result.
        :rtype: :class:`list`
        :raise ValueError: in case of inconsistent arguments.
        :raise SearchAssertionError: if the assertion on the number of
            results fails.
        :raise ICATError: in case of exceptions raised by the ICAT
            server.

        """
        if assertmax is not None and assertmin > assertmax:
            raise ValueError("Minimum (%d) is larger then maximum (%d)."
                             % (assertmin, assertmax))
        result = self.search(query)
        num = len(result)
        if num >= assertmin and (assertmax is None or num <= assertmax):
            return result
        else:
            raise SearchAssertionError(query, assertmin, assertmax, num)

    def searchChunked(self, query, skip=0, count=None, chunksize=100):
        """Search the ICAT server.

        Call the ICAT :meth:`~icat.client.Client.search` API method,
        limiting the number of results in each call and repeat the
        call as often as needed to retrieve all the results.

        This can be used as a drop in replacement for the search API
        method most of the times.  It avoids the error if the number
        of items in the result exceeds the limit imposed by the ICAT
        server.  There are a few subtle differences though: the query
        must not contain a LIMIT clause (use the skip and count
        arguments instead) and should contain an ORDER BY clause.  The
        return value is a generator yielding successively the items in
        the search result rather than a list.  The individual search
        calls are done lazily, e.g. they are not done until needed to
        yield the next item from the generator.

        .. note::
            The result may be defective (omissions, duplicates) if the
            content in the ICAT server changes between individual
            search calls in a way that would affect the result.  It is
            a common mistake when looping over items returned from
            this method to have code with side effects on the search
            result in the body of the loop.  Example:

            .. code-block:: python

                # Mark all datasets as complete
                # This will *not* work as expected!
                query = Query(client, "Dataset", conditions={
                    "complete": "= False"
                }, includes="1", order=["id"])
                for ds in client.searchChunked(query):
                    ds.complete = True
                    ds.update()

            This should rather be formulated as:

            .. code-block:: python

                # Mark all datasets as complete
                # This version works!
                query = Query(client, "Dataset", includes="1", order=["id"])
                for ds in client.searchChunked(query):
                    if ds.complete:
                        continue
                    ds.complete = True
                    ds.update()

        :param query: the search query.
        :type query: :class:`icat.query.Query` or :class:`str`
        :param skip: offset from within the full list of available results.
        :type skip: :class:`int`
        :param count: maximum number of items to return.  A value of
            :const:`None` means no limit.
        :type count: :class:`int`
        :param chunksize: number of items to query in each search
            call.  This is an internal tuning parameter and does not
            affect the result.
        :type chunksize: :class:`int`
        :return: a generator that successively yields the items in the
            search result.
        :rtype: generator
        """
        if isinstance(query, Query):
            query = str(query)
        query = query.replace('%', '%%')
        if query.startswith("SELECT"):
            query += " LIMIT %d, %d"
        else:
            query = "%d, %d " + query
        if chunksize < 2:
            chunksize = 2
        delivered = 0
        while True:
            if count is not None and count - delivered < chunksize:
                chunksize = count - delivered
            if chunksize == 0:
                break
            items = self.search(query % (skip, chunksize))
            skip += chunksize
            for o in items:
                yield o
                delivered += 1
            if len(items) < chunksize:
                break

    def searchUniqueKey(self, key, objindex=None):
        """Search the object that belongs to a unique key.

        This is in a sense the inverse method to
        :meth:`icat.entity.Entity.getUniqueKey`, the key must
        previously have been generated by it.  This method searches
        the entity object that the key has been generated for from the
        server.

        if objindex is not :const:`None`, it is used as a cache of
        previously retrieved objects.  It must be a dict that maps
        keys to entity objects.  The object retrieved by this method
        call will be added to this index.

        :param key: the unique key of the object to search for.
        :type key: :class:`str`
        :param objindex: cache of entity objects.
        :type objindex: :class:`dict`
        :return: the object corresponding to the key.
        :rtype: :class:`icat.entity.Entity`
        :raise SearchResultError: if the object has not been found.
        :raise ValueError: if the key is not well formed.
        """

        if objindex is not None and key in objindex:
            return objindex[key]
        us = key.index('_')
        beanname = key[:us]
        av = parse_attr_val(key[us+1:])
        info = self.getEntityInfo(beanname)
        query = Query(self, beanname)
        for f in info.fields:
            if f.name in av.keys():
                attr = f.name
                if f.relType == "ATTRIBUTE":
                    cond = "= '%s'" % simpleqp_unquote(av[attr])
                    query.addConditions({attr:cond})
                elif f.relType == "ONE":
                    rk = str("%s_%s" % (f.type, av[attr]))
                    ro = self.searchUniqueKey(rk, objindex)
                    query.addConditions({"%s.id" % attr:"= %d" % ro.id})
                else:
                    raise ValueError("malformed '%s': invalid attribute '%s'" 
                                     % (key, attr))
        obj = self.assertedSearch(query)[0]
        if objindex is not None:
            objindex[key] = obj
        return obj

    def searchMatching(self, obj, includes=None):
        """Search the matching object.

        Search the object from the ICAT server that matches the given
        object in the uniqueness constraint.

        >>> dataset = client.new("Dataset", investigation=inv, name=dsname)
        >>> dataset = client.searchMatching(dataset)
        >>> dataset.id
        172383

        :param obj: an entity object having the attrinutes for the
            uniqueness constraint set accordingly.
        :type obj: :class:`icat.entity.Entity`
        :param includes: list of related objects to add to the INCLUDE
            clause of the search query.
            See :meth:`icat.query.Query.addIncludes` for details.
        :type includes: iterable of :class:`str`
        :return: the corresponding object.
        :rtype: :class:`icat.entity.Entity`
        :raise SearchResultError: if the object has not been found.
        :raise ValueError: if the object's class does not have a
            uniqueness constraint or if any attribute needed for the
            constraint is not set.
        """
        if 'id' in obj.Constraint:
            raise ValueError("%s does not have a uniqueness constraint.")
        query = Query(self, obj.BeanName, includes=includes)
        for a in obj.Constraint:
            v = getattr(obj, a)
            if v is None:
                raise ValueError("%s is not set" % a)
            if a in obj.InstAttr:
                query.addConditions({a: "= '%s'" % v})
            elif a in obj.InstRel:
                if v.id is None:
                    raise ValueError("%s.id is not set" % a)
                query.addConditions({"%s.id" % a: "= %d" % v.id})
            else:
                raise InternalError("Invalid constraint '%s' in %s."
                                    % (a, obj.BeanName))
        return self.assertedSearch(query)[0]

    def createUser(self, name, search=False, **kwargs):
        """Search a user by name or create a new user.

        If search is :const:`True` search a user by the given name.  If
        search is :const:`False` or no user is found, create a new user.

        :param name: username.
        :type name: :class:`str`
        :param search: flag whether a user should be searched first.
        :type search: :class:`bool`
        :param kwargs: attributes of the user passed to `new`.
        :return: the user.
        :rtype: :class:`icat.entity.Entity`
        """
        if search:
            users = self.search("User[name='%s']" % name)
            if len(users): 
                log.info("User: '%s' already exists", name)
                return users[0]

        log.info("User: creating '%s'", name)
        u = self.new("User", name=name, **kwargs)
        u.create()
        return u

    def createGroup(self, name, users=()):
        """Create a group and add users to it.

        :param name: the name of the group.
        :type name: :class:`str`
        :param users: a list of users.
        :type users: :class:`list` of :class:`icat.entity.Entity`
        :return: the group.
        :rtype: :class:`icat.entity.Entity`
        """
        log.info("Group: creating '%s'", name)
        g = self.new("Grouping", name=name)
        g.create()
        g.addUsers(users)
        return g

    def createRules(self, crudFlags, what, group=None):
        """Create access rules.

        :param crudFlags: access mode.
        :type crudFlags: :class:`str`
        :param what: list of items subject to the rule.  The items
            must be either ICAT search expression strings or
            :class:`icat.query.Query` objects.
        :type what: :class:`list`
        :param group: the group that should be granted access or
            :const:`None` for everybody.
        :type group: :class:`icat.entity.Entity`
        :return: list of the ids of the created rules.
        :rtype: :class:`list` of :class:`int`
        """
        if group:
            log.info("Rule: adding %s permissions for group '%s'", 
                     crudFlags, group.name)
        else:
            log.info("Rule: adding %s permissions for anybody", crudFlags)

        rules = []
        for w in what:
            r = self.new("Rule",
                         crudFlags=crudFlags, what=str(w), grouping=group)
            rules.append(r)
        return self.createMany(rules)


    # =================== custom IDS methods ===================

    def putData(self, infile, datafile):
        """Upload a datafile to IDS.

        The content of the file to upload is read from `infile`,
        either directly if it is an open file, or a file by that name
        will be opened for reading.

        The `datafile` object must be initialized but not yet created
        at the ICAT server.  It will be created by the IDS.  The ids
        of the Dataset and the DatafileFormat as well as the
        attributes description, doi, datafileCreateTime, and
        datafileModTime will be taken from `datafile`.  If
        datafileModTime is not set, the method will try to
        :func:`os.fstat` `infile` and use the last modification time
        from the file system, if available.  If datafileCreateTime is
        not set, it will be set to datafileModTime.

        Note that only the attributes datafileFormat, dataset,
        description, doi, datafileCreateTime, and datafileModTime of
        `datafile` will be taken into account as described above.  All
        other attributes are ignored and the Datafile object created
        in the ICAT server might end up with different values for
        those other attribues.

        :param infile: either a file opened for reading or a file name.
        :type infile: :class:`file` or :class:`~pathlib.Path` or :class:`str`
        :param datafile: A Datafile object.
        :type datafile: :class:`icat.entity.Entity`
        :return: The Datafile object created by IDS.
        :rtype: :class:`icat.entity.Entity`

        .. versionchanged:: 1.0.0
            the `infile` parameter also accepts a
            :class:`~pathlib.Path` object.
        """

        if not self.ids:
            raise RuntimeError("no IDS.")
        if not datafile.name:
            raise ValueError("datafile.name is not set.")
        if not datafile.dataset or not datafile.dataset.id:
            raise ValueError("datafile.dataset is not set.")
        if not datafile.datafileFormat or not datafile.datafileFormat.id:
            raise ValueError("datafile.datafileFormat is not set.")

        if not hasattr(infile, 'read'):
            # We got a file name as infile.  Open the file and
            # recursively call the method again with the open file
            # as argument.  This is the easiest way to guarantee
            # that the file will finally get closed also in case
            # of errors.
            try:
                infile = Path(infile)
            except TypeError:
                raise TypeError("invalid infile type '%s': "
                                "must either be a file or a file name." % 
                                type(infile)) from None
            else:
                with infile.open('rb') as f:
                    return self.putData(f, datafile)

        modTime = ms_timestamp(datafile.datafileModTime)
        if not modTime:
            try:
                # Try our best to get the mtime from the fileno, but
                # don't bother if this doesn't work, e.g. if it cannot
                # be fstated.  Note that fstat() yields seconds since
                # epoch as float, while IDS expects milliseconds since
                # epoch as int.
                modTime = int(1000*os.fstat(infile.fileno()).st_mtime)
            except:
                pass
        createTime = ms_timestamp(datafile.datafileCreateTime)
        if not createTime:
            createTime = modTime

        dfid = self.ids.put(infile, datafile.name, 
                            datafile.dataset.id, datafile.datafileFormat.id, 
                            datafile.description, datafile.doi, 
                            createTime, modTime)
        return self.get(datafile.BeanName, dfid)

    def getData(self, objs, compressFlag=False, zipFlag=False, outname=None, 
                offset=0):
        """Retrieve the requested data from IDS.

        The data objects to retrieve are given in objs.  This can be
        any combination of single Datafiles, Datasets, or complete
        Investigations.

        :param objs: either a dict having some of the keys
            `investigationIds`, `datasetIds`, and `datafileIds` with a
            list of object ids as value respectively, or a list of
            entity objects, or a data selection, or an id returned by
            :meth:`~icat.client.Client.prepareData`.
        :type objs: :class:`dict`, :class:`list` of
            :class:`icat.entity.Entity`,
            :class:`icat.ids.DataSelection`, or :class:`str`
        :param compressFlag: flag whether to use a zip format with an
            implementation defined compression level, otherwise use no
            (or minimal) compression.
        :type compressFlag: :class:`bool`
        :param zipFlag: flag whether return a single datafile in zip
            format.  For multiple files zip format is always used.
        :type zipFlag: :class:`bool`
        :param outname: the preferred name for the downloaded file to
            specify in the Content-Disposition header.
        :type outname: :class:`str`
        :param offset: if larger then zero, add Range header to the
            HTTP request with the indicated bytes offset.
        :type offset: :class:`int`
        :return: a file-like object as returned by
            :meth:`urllib.request.OpenerDirector.open`.

        .. versionchanged:: 0.17.0
            accept a prepared id in `objs`.
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, (DataSelection, str)):
            objs = DataSelection(objs)
        return self.ids.getData(objs, compressFlag, zipFlag, outname, offset)

    def getDataUrl(self, objs, compressFlag=False, zipFlag=False, outname=None):
        """Get the URL to retrieve the requested data from IDS.

        The data objects to retrieve are given in objs.  This can be
        any combination of single Datafiles, Datasets, or complete
        Investigations.

        Note that the URL contains the session id of the current ICAT
        session.  It will become invalid if the client logs out.

        :param objs: either a dict having some of the keys
            `investigationIds`, `datasetIds`, and `datafileIds`
            with a list of object ids as value respectively, or a list
            of entity objects, or a data selection, or an id returned by
            :meth:`~icat.client.Client.prepareData`.
        :type objs: :class:`dict`, :class:`list` of
            :class:`icat.entity.Entity`,
            :class:`icat.ids.DataSelection`, or :class:`str`
        :param compressFlag: flag whether to use a zip format with an
            implementation defined compression level, otherwise use no
            (or minimal) compression.
        :type compressFlag: :class:`bool`
        :param zipFlag: flag whether return a single datafile in zip
            format.  For multiple files zip format is always used.
        :type zipFlag: :class:`bool`
        :param outname: the preferred name for the downloaded file to
            specify in the Content-Disposition header.
        :type outname: :class:`str`
        :return: the URL for the data at the IDS.
        :rtype: :class:`str`

        .. versionchanged:: 0.17.0
            accept a prepared id in `objs`.
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, (DataSelection, str)):
            objs = DataSelection(objs)
        return self.ids.getDataUrl(objs, compressFlag, zipFlag, outname)

    def prepareData(self, objs, compressFlag=False, zipFlag=False):
        """Prepare data at IDS to be retrieved in subsequent calls.

        The data objects to retrieve are given in objs.  This can be
        any combination of single Datafiles, Datasets, or complete
        Investigations.

        :param objs: either a dict having some of the keys
            `investigationIds`, `datasetIds`, and `datafileIds`
            with a list of object ids as value respectively, or a list
            of entity objects, or a data selection.
        :type objs: :class:`dict`, :class:`list` of
            :class:`icat.entity.Entity`, or
            :class:`icat.ids.DataSelection`
        :param compressFlag: flag whether to use a zip format with an
            implementation defined compression level, otherwise use no
            (or minimal) compression.
        :type compressFlag: :class:`bool`
        :param zipFlag: flag whether return a single datafile in zip
            format.  For multiple files zip format is always used.
        :type zipFlag: :class:`bool`
        :return: `preparedId`, an opaque string which may be used as an
            argument to :meth:`~icat.client.Client.isDataPrepared` and
            :meth:`~icat.client.Client.getData` calls.
        :rtype: :class:`str`
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, DataSelection):
            objs = DataSelection(objs)
        return self.ids.prepareData(objs, compressFlag, zipFlag)

    def isDataPrepared(self, preparedId):
        """Check if prepared data is ready at IDS.

        :param preparedId: the id returned by
            :meth:`~icat.client.Client.prepareData`.
        :type preparedId: :class:`str`
        :return: :const:`True` if the data is ready, otherwise :const:`False`.
        :rtype: :class:`bool`
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        return self.ids.isPrepared(preparedId)

    def deleteData(self, objs):
        """Delete data from IDS.

        The data objects to delete are given in objs.  This can be
        any combination of single Datafiles, Datasets, or complete
        Investigations.

        :param objs: either a dict having some of the keys
            `investigationIds`, `datasetIds`, and `datafileIds`
            with a list of object ids as value respectively, or a list
            of entity objects, or a data selection.
        :type objs: :class:`dict`, :class:`list` of
            :class:`icat.entity.Entity`, or
            :class:`icat.ids.DataSelection`
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, DataSelection):
            objs = DataSelection(objs)
        self.ids.delete(objs)


atexit.register(Client.cleanupall)
