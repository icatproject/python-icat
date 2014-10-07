"""Provide the Client class.

This is the only module that needs to be imported to use the icat.
"""

import os
from warnings import warn
import re
import logging
from distutils.version import StrictVersion as Version
import atexit

import suds
import suds.client
import suds.sudsobject

from icat.entity import Entity
import icat.entities
from icat.exception import *
from icat.ids import *
from icat.helper import simpleqp_unquote, parse_attr_val

__all__ = ['Client']


log = logging.getLogger(__name__)

TypeMap42 = {
    'entityBaseBean': Entity,
    'application': icat.entities.Application,
    'datafile': icat.entities.Datafile,
    'datafileFormat': icat.entities.DatafileFormat,
    'datafileParameter': icat.entities.DatafileParameter,
    'dataset': icat.entities.Dataset,
    'datasetParameter': icat.entities.DatasetParameter,
    'datasetType': icat.entities.DatasetType,
    'facility': icat.entities.Facility,
    'facilityCycle': icat.entities.FacilityCycle,
    'group': icat.entities.Group,
    'inputDatafile': icat.entities.InputDatafile,
    'inputDataset': icat.entities.InputDataset,
    'instrument': icat.entities.Instrument,
    'instrumentScientist': icat.entities.InstrumentScientist,
    'investigation': icat.entities.Investigation,
    'investigationParameter': icat.entities.InvestigationParameter,
    'investigationType': icat.entities.InvestigationType,
    'investigationUser': icat.entities.InvestigationUser,
    'job': icat.entities.Job,
    'keyword': icat.entities.Keyword,
    'notificationRequest': icat.entities.NotificationRequest,
    'outputDatafile': icat.entities.OutputDatafile,
    'outputDataset': icat.entities.OutputDataset,
    'parameter': icat.entities.Parameter,
    'parameterType': icat.entities.ParameterType,
    'permissibleStringValue': icat.entities.PermissibleStringValue,
    'publication': icat.entities.Publication,
    'relatedDatafile': icat.entities.RelatedDatafile,
    'rule': icat.entities.Rule,
    'sample': icat.entities.Sample,
    'sampleParameter': icat.entities.SampleParameter,
    'sampleType': icat.entities.SampleType,
    'shift': icat.entities.Shift,
    'study': icat.entities.Study,
    'studyInvestigation': icat.entities.StudyInvestigation,
    'user': icat.entities.User,
    'userGroup': icat.entities.UserGroup,
    }
"""Map instance types defined in the WSDL to Python classes (ICAT 4.2.*)."""

TypeMap43 = {
    'entityBaseBean': Entity,
    'application': icat.entities.Application43,
    'dataCollection': icat.entities.DataCollection,
    'dataCollectionDatafile': icat.entities.DataCollectionDatafile,
    'dataCollectionDataset': icat.entities.DataCollectionDataset,
    'dataCollectionParameter': icat.entities.DataCollectionParameter,
    'datafile': icat.entities.Datafile43,
    'datafileFormat': icat.entities.DatafileFormat,
    'datafileParameter': icat.entities.DatafileParameter,
    'dataset': icat.entities.Dataset43,
    'datasetParameter': icat.entities.DatasetParameter,
    'datasetType': icat.entities.DatasetType,
    'facility': icat.entities.Facility43,
    'facilityCycle': icat.entities.FacilityCycle43,
    'grouping': icat.entities.Group43,
    'instrument': icat.entities.Instrument43,
    'instrumentScientist': icat.entities.InstrumentScientist,
    'investigation': icat.entities.Investigation43,
    'investigationInstrument': icat.entities.InvestigationInstrument,
    'investigationParameter': icat.entities.InvestigationParameter,
    'investigationType': icat.entities.InvestigationType,
    'investigationUser': icat.entities.InvestigationUser,
    'job': icat.entities.Job43,
    'keyword': icat.entities.Keyword,
    'log': icat.entities.Log,
    'parameter': icat.entities.Parameter,
    'parameterType': icat.entities.ParameterType43,
    'permissibleStringValue': icat.entities.PermissibleStringValue,
    'publicStep': icat.entities.PublicStep,
    'publication': icat.entities.Publication,
    'relatedDatafile': icat.entities.RelatedDatafile,
    'rule': icat.entities.Rule43,
    'sample': icat.entities.Sample43,
    'sampleParameter': icat.entities.SampleParameter,
    'sampleType': icat.entities.SampleType43,
    'shift': icat.entities.Shift,
    'study': icat.entities.Study,
    'studyInvestigation': icat.entities.StudyInvestigation,
    'user': icat.entities.User,
    'userGroup': icat.entities.UserGroup43,
    }
"""Map instance types defined in the WSDL to Python classes (ICAT 4.3.0)."""

TypeMap431 = TypeMap43.copy()
"""Map instance types defined in the WSDL to Python classes (ICAT 4.3.1)."""
TypeMap431.update( dataCollection = icat.entities.DataCollection431 )

class Client(suds.client.Client):
 
    """A client accessing an ICAT service.

    Client is a subclass of suds.client.Client and inherits most of
    its behavior.  It adds methods for the instantiation of ICAT
    entities and implementations of the ICAT API methods.

    :group ICAT API methods: login, logout, create, createMany,
        delete, deleteMany, get, getApiVersion, getEntityInfo,
        getEntityNames, getProperties, getRemainingMinutes,
        getUserName, isAccessAllowed, luceneClear, luceneCommit,
        luceneGetPopulating, lucenePopulate, luceneSearch, refresh,
        search, searchText, update

    :group custom API methods: searchUniqueKey, assertedSearch,
        createUser, createGroup, createRules

    :group custom IDS methods: putData, getData, getDataUrl,
        prepareData, isDataPrepared, getPreparedData,
        getPreparedDataUrl, deleteData
    """

    Register = {}
    """The register of all active clients."""

    @classmethod
    def cleanupall(cls):
        """Cleanup all class instances.

        Call `cleanup` on all registered class instances, e.g. on all
        clients that have not yet been cleaned up.
        """
        cl = list(cls.Register.values())
        for c in cl:
            c.cleanup()

    def __init__(self, url, **kwargs):

        """Initialize the client.

        Extend the inherited constructor.  Query the API version from
        the ICAT server and initialize the typemap accordingly.

        :param url: The URL for the WSDL.
        :type url: str
        :param kwargs: keyword arguments.
        :see: ``suds.options.Options`` for the keyword arguments.
        """

        if 'idsurl' in kwargs:
            idsurl = kwargs['idsurl']
            del kwargs['idsurl']
        else:
            idsurl = None

        super(Client, self).__init__(url, **kwargs)
        apiversion = self.getApiVersion()
        # Translate a version having a trailing '-SNAPSHOT' into
        # something that StrictVersion would accept.
        apiversion = re.sub(r'-SNAPSHOT$', 'a1', apiversion)
        self.apiversion = Version(apiversion)
        log.debug("Connect to %s, ICAT version %s", url, self.apiversion)

        # We need to use different TypeMaps depending on the ICAT
        # version.  Currently 4.2.* and 4.3.* are supported.  For
        # other versions, use the closest known TypeMap and hope for
        # the best.
        if self.apiversion < '4.2.0':
            warn(ClientVersionWarning(self.apiversion, "too old"))
            self.typemap = TypeMap42.copy()
        elif self.apiversion < '4.3.0':
            self.typemap = TypeMap42.copy()
        elif self.apiversion == '4.3.0':
            self.typemap = TypeMap43.copy()
        elif self.apiversion < '4.4':
            self.typemap = TypeMap431.copy()
        else:
            warn(ClientVersionWarning(self.apiversion, "too new"))
            self.typemap = TypeMap43.copy()

        self.ids = None
        self.sessionId = None
        self.autoLogout = True
        self.entityInfoCache = {}

        if idsurl:
            self.add_ids(idsurl)
        self.Register[id(self)] = self

    def __del__(self):
        """Call `cleanup`."""
        self.cleanup()

    def cleanup(self):
        """Release resources allocated by the client.

        Logout from the active ICAT session (if ``self.autoLogout`` is
        True).  The client should not be used any more after calling
        this method.
        """
        if id(self) in self.Register:
            if self.autoLogout:
                self.logout()
            del self.Register[id(self)]

    def add_ids(self, url, proxy=None):
        """Add the URL to an ICAT Data Service."""
        if proxy is None:
            proxy = self.options.proxy
        idsargs = {}
        if self.sessionId:
            idsargs['sessionId'] = self.sessionId
        if proxy:
            idsargs['proxy'] = proxy
        self.ids = IDSClient(url, **idsargs)

    def __setattr__(self, attr, value):
        super(Client, self).__setattr__(attr, value)
        if attr == 'sessionId' and self.ids:
            self.ids.sessionId = self.sessionId


    def new(self, obj, **kwargs):

        """Instantiate a new `Entity` object.

        If obj is a string, take it as the name of an instance type.
        Create a new instance object of this type and lookup the class
        for the ``Entity`` object in the ``typemap`` using this type
        name.  If obj is an instance object, look up its class name in
        the ``typemap`` to determine the class for the ``Entity``
        object.  If obj is ``None``, do nothing and return ``None``.
        
        :param obj: either a Suds instance object, a name of an
            instance type, or ``None``.
        :type obj: ``suds.sudsobject.Object`` or ``str``
        :param kwargs: attributes passed to the constructor
            `Entity.__init__` of the entity class.
        :return: the new entity object or ``None``.
        :rtype: ``Entity``
        :raise TypeError: if obj is neither a valid instance object,
            nor a valid name of an entity type, nor None.
        """

        if isinstance(obj, suds.sudsobject.Object):
            # obj is already an instance, use it right away
            instance = obj
            instancetype = instance.__class__.__name__
            try:
                Class = self.typemap[instancetype]
            except KeyError:
                raise stripCause(TypeError("Invalid instance type '%s'." 
                                           % instancetype))
        elif isinstance(obj, basestring):
            # obj is the name of an instance type, create the instance
            instancetype = obj
            try:
                Class = self.typemap[instancetype]
            except KeyError:
                raise stripCause(TypeError("Invalid instance type '%s'." 
                                           % instancetype))
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
            raise TypeError("Invalid argument type '%s'." % type(obj))

        if Class is None:
            raise TypeError("Instance type '%s' is not supported." % 
                            instancetype)
        if Class.BeanName is None:
            raise TypeError("Refuse to create an instance of "
                            "abstract type '%s'." % instancetype)

        return Class(self, instance, **kwargs)

    def getEntity(self, obj):
        """Get the corresponding `Entity` for an object.

        If obj is a Suds instance object, create a new ``Entity``
        object with `new`.  Otherwise do nothing and return obj
        unchanged.
        
        :param obj: either a Suds instance object or anything.
        :type obj: ``suds.sudsobject.Object`` or any type
        :return: the new entity object or obj.
        :rtype: ``Entity`` or any type
        """
        if isinstance(obj, suds.sudsobject.Object):
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
        return self.sessionId

    def logout(self):
        if self.sessionId:
            try:
                self.service.logout(self.sessionId)
            except suds.WebFault as e:
                raise translateError(e)
            finally:
                self.sessionId = None


    def create(self, bean):
        try:
            return self.service.create(self.sessionId, Entity.getInstance(bean))
        except suds.WebFault as e:
            raise translateError(e)

    def createMany(self, beans):
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
            instance = self.service.get(self.sessionId, query, primaryKey)
            return self.getEntity(instance)
        except suds.WebFault as e:
            raise translateError(e)

    def getApiVersion(self):
        try:
            return self.service.getApiVersion()
        except suds.WebFault as e:
            raise translateError(e)

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
        if self.apiversion < '4.3':
            entitynames = [e.BeanName for e in self.typemap.values() 
                           if (e is not None and e.BeanName is not None)]
            entitynames.sort()
            return entitynames
        else:
            try:
                return self.service.getEntityNames()
            except suds.WebFault as e:
                raise translateError(e)

    def getProperties(self):
        try:
            return self.service.getProperties(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("getProperties", self.apiversion)
            else:
                raise

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

    def isAccessAllowed(self, bean, accessType):
        try:
            return self.service.isAccessAllowed(self.sessionId, Entity.getInstance(bean), accessType)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("isAccessAllowed", self.apiversion)
            else:
                raise

    def luceneClear(self):
        try:
            self.service.luceneClear(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("luceneClear", self.apiversion)
            else:
                raise

    def luceneCommit(self):
        try:
            self.service.luceneCommit(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("luceneCommit", self.apiversion)
            else:
                raise

    def luceneGetPopulating(self):
        try:
            return self.service.luceneGetPopulating(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3.1':
                raise VersionMethodError("luceneGetPopulating", self.apiversion)
            else:
                raise

    def lucenePopulate(self, entityName):
        try:
            self.service.lucenePopulate(self.sessionId, entityName)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("lucenePopulate", self.apiversion)
            else:
                raise

    def luceneSearch(self, query, maxCount, entityName):
        try:
            return self.service.luceneSearch(self.sessionId, query, maxCount, entityName)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("luceneSearch", self.apiversion)
            else:
                raise

    def refresh(self):
        try:
            self.service.refresh(self.sessionId)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("refresh", self.apiversion)
            else:
                raise

    def search(self, query):
        try:
            instances = self.service.search(self.sessionId, query)
            return map(lambda i: self.getEntity(i), instances)
        except suds.WebFault as e:
            raise translateError(e)

    def searchText(self, query, maxCount, entityName):
        try:
            instances = self.service.searchText(self.sessionId, query, 
                                                maxCount, entityName)
            return map(lambda i: self.getEntity(i), instances)
        except suds.WebFault as e:
            raise translateError(e)
        except suds.MethodNotFound as e:
            if self.apiversion < '4.3':
                raise VersionMethodError("searchText", self.apiversion)
            else:
                raise

    def update(self, bean):
        try:
            self.service.update(self.sessionId, Entity.getInstance(bean))
        except suds.WebFault as e:
            raise translateError(e)


    # =================== custom API methods ===================

    def assertedSearch(self, query, assertmin=1, assertmax=1):
        """Search with an assertion on the result.

        Perform a search and verify that the number of items found
        lies within the bounds of assertmin and assertmax.  Raise an
        error if this assertion fails.

        :param query: the search query string.
        :type query: ``str``
        :param assertmin: minimum number of expected results.
        :type assertmin: ``int``
        :param assertmax: maximum number of expected results.  A value
            of ``None`` is treated as infinity.
        :type assertmax: ``int``
        :return: search result.
        :rtype: ``list``
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

    def searchUniqueKey(self, key, objindex=None):
        """Search the object that belongs to a unique key.

        This is in a sense the inverse method to
        `Entity.getUniqueKey()`.  The key must previously have been
        generated by ``getUniqueKey()``.  This method searches the
        Entity object that created this key from the server.

        if objindex is not ``None``, it is used as a cache of
        previously retrieved objects.  It must be a dict that maps
        keys to Entity objects.  The newly object retrieved by this
        method call will be added to this index.

        This method uses the JPQL inspired query syntax introduced
        with ICAT 4.3.0.  It won't work with older ICAT servers.

        :param key: the unique key of the object to search for.
        :type key: ``str``
        :param objindex: cache of Entity objects.
        :type objindex: ``dict``
        :return: the object corresponding to the key.
        :rtype: ``Entity``
        :raise SearchResultError: if the object have not been found.
        :raise ValueError: if the key is not well formed.
        :raise VersionMethodError: if connected to an ICAT server
            older then 4.3.0.
        """

        if self.apiversion < '4.3':
            raise VersionMethodError("searchUniqueKey", self.apiversion)
        if objindex is not None and key in objindex:
            return objindex[key]
        us = key.index('_')
        beanname = key[:us]
        av = parse_attr_val(key[us+1:])
        info = self.getEntityInfo(beanname)
        query = "SELECT e FROM %s e" % beanname
        op = "WHERE"
        for f in info.fields:
            if f.name in av.keys():
                attr = f.name
                if f.relType == "ATTRIBUTE":
                    query += " %s e.%s = '%s'" % (op, attr, 
                                                  simpleqp_unquote(av[attr]))
                elif f.relType == "ONE":
                    rk = str("%s_%s" % (f.type, av[attr]))
                    ro = self.searchUniqueKey(rk, objindex)
                    query += " %s e.%s.id = %d" % (op, attr, ro.id)
                else:
                    raise ValueError("malformed '%s': invalid attribute '%s'" 
                                     % (key, attr))
                op = "AND"
        obj = self.assertedSearch(query)[0]
        if objindex is not None:
            objindex[key] = obj
        return obj

    def createUser(self, name, search=False, **kwargs):
        """Search a user by name or Create a new user.

        If search is ``True`` search a user by the given name.  If
        search is ``False`` or no user is found, create a new user.

        :param name: username.
        :type name: ``str``
        :param search: flag whether a user should be searched first.
        :type search: ``bool``
        :param kwargs: attributes of the user passed to `new`.
        :return: the user.
        :rtype: ``Entity``
        """
        if search:
            users = self.search("User[name='%s']" % name)
            if len(users): 
                log.info("User: '%s' already exists", name)
                return users[0]

        log.info("User: creating '%s'", name)
        u = self.new("user", name=name, **kwargs)
        u.create()
        return u

    def createGroup(self, name, users=[]):
        """Create a group and add users to it.

        :param name: the name of the group.
        :type name: ``str``
        :param users: a list of users.
        :type users: ``list`` of ``Entity``
        :return: the group.
        :rtype: ``Entity``
        """
        log.info("Group: creating '%s'", name)
        if self.apiversion < '4.3':
            g = self.new("group", name=name)
        else:
            g = self.new("grouping", name=name)
        g.create()
        g.addUsers(users)
        return g

    def createRules(self, group, crudFlags, what):
        """Create access rules.

        :param group: the group that should be granted access or
            ``None`` for everybody.
        :type group: ``Entity``
        :param crudFlags: access mode.
        :type crudFlags: ``str``
        :param what: list of items subject to the rule.
        :type what: ``list`` of ``str``
        :return: list of the ids of the created rules.
        :rtype: ``list`` of ``long``
        """
        if group:
            log.info("Rule: adding %s permissions for group '%s'", 
                     crudFlags, group.name)
        else:
            log.info("Rule: adding %s permissions for anybody", crudFlags)

        rules = []
        for w in what:
            r = self.new("rule", crudFlags=crudFlags, what=w, grouping=group)
            rules.append(r)
        return self.createMany(rules)


    # =================== custom IDS methods ===================

    def putData(self, infile, datafile):
        """Upload a datafile to IDS.

        The content of the file to upload is read from infile, either
        directly if it is an open file, or a file by that named will
        be opened for reading.  

        The datafile object must be initialized but not yet created at
        the ICAT server.  It will be created by the IDS.  The ids of
        the Dataset and the DatafileFormat as well as the attributes
        description, doi, datafileCreateTime, and datafileModTime will
        be taken from datafile.  If datafileModTime is not set, the
        method will try to fstat infile and use the last modification
        time from the file system, if available.  If
        datafileCreateTime is not set, it will be set to
        datafileModTime.

        Note that only the attributes datafileFormat, dataset,
        description, doi, datafileCreateTime, and datafileModTime of
        datafile will be taken into account as described above.  All
        other attributes are ignored and the Datafile object created
        in the ICAT server might end up with different values for
        those other attribues.

        :param infile: either a file opened for reading or a filename.
        :type infile: ``file`` or ``str``
        :param datafile: A Datafile object.
        :type datafile: `Datafile`
        :return: id of the Datafile object created by IDS.
        :rtype: ``long``
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
            if isinstance(infile, basestring):
                # We got a file name as infile.  Open the file and
                # recursively call the method again with the open file
                # as argument.  This is the easiest way to guarantee
                # that the file will finally get closed also in case
                # of errors.
                with open(infile, 'rb') as f:
                    return self.putData(f, datafile)
            else:
                raise TypeError("invalid infile type '%s': "
                                "must either be a file or a file name." % 
                                type(infile))

        modTime = datafile.datafileModTime
        if not modTime:
            try:
                # Try our best to get the mtime from the fileno, but
                # don't bother if this doesn't work, e.g. if it cannot
                # be fstated.  Note that fstat() yields seconds since
                # epoch as float, while IDS expects microseconds since
                # epoch as int.
                modTime = int(1000*os.fstat(infile.fileno()).st_mtime)
            except:
                pass
        createTime = datafile.datafileCreateTime
        if not createTime:
            createTime = modTime

        return self.ids.put(infile, datafile.name, 
                            datafile.dataset.id, datafile.datafileFormat.id, 
                            datafile.description, datafile.doi, 
                            createTime, modTime)

    def getData(self, objs, compressFlag=False, zipFlag=False, outname=None, 
                offset=0):
        """Retrieve the requested data from IDS.

        The data objects to retrieve are given in objs.  This can be
        any combination of single Datafiles, Datasets, or complete
        Investigations.

        :param objs: either a dict having some of the keys
            ``investigationIds``, ``datasetIds``, and ``datafileIds``
            with a list if object ids as value respectively, or a list
            of entity objects, or a data selection.
        :type objs: ``dict``, ``list`` of ``Entity``, or `DataSelection`
        :param compressFlag: flag whether to use a zip format with an
            implementation defined compression level, otherwise use no
            (or minimal) compression.
        :type compressFlag: ``bool``
        :param zipFlag: flag whether return a single datafile in zip
            format.  For multiple files zip format is always used.
        :type zipFlag: ``bool``
        :param outname: the preferred name for the downloaded file to
            specify in the Content-Disposition header.
        :type outname: ``str``
        :param offset: if larger then zero, add Range header to the
            HTTP request with the indicated bytes offset.
        :type offset: ``int``
        :return: a file-like object as returned by
            ``urllib2.OpenerDirector.open()``
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, DataSelection):
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
            ``investigationIds``, ``datasetIds``, and ``datafileIds``
            with a list if object ids as value respectively, or a list
            of entity objects, or a data selection.
        :type objs: ``dict``, ``list`` of ``Entity``, or `DataSelection`
        :param compressFlag: flag whether to use a zip format with an
            implementation defined compression level, otherwise use no
            (or minimal) compression.
        :type compressFlag: ``bool``
        :param zipFlag: flag whether return a single datafile in zip
            format.  For multiple files zip format is always used.
        :type zipFlag: ``bool``
        :param outname: the preferred name for the downloaded file to
            specify in the Content-Disposition header.
        :type outname: ``str``
        :return: the URL for tha data at the IDS.
        :rtype: ``str``
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, DataSelection):
            objs = DataSelection(objs)
        return self.ids.getDataUrl(objs, compressFlag, zipFlag, outname)

    def prepareData(self, objs, compressFlag=False, zipFlag=False):
        """Prepare data at IDS for a subsequent getPreparedData call.

        The data objects to retrieve are given in objs.  This can be
        any combination of single Datafiles, Datasets, or complete
        Investigations.

        :param objs: either a dict having some of the keys
            ``investigationIds``, ``datasetIds``, and ``datafileIds``
            with a list if object ids as value respectively, or a list
            of entity objects, or a data selection.
        :type objs: ``dict``, ``list`` of ``Entity``, or `DataSelection`
        :param compressFlag: flag whether to use a zip format with an
            implementation defined compression level, otherwise use no
            (or minimal) compression.
        :type compressFlag: ``bool``
        :param zipFlag: flag whether return a single datafile in zip
            format.  For multiple files zip format is always used.
        :type zipFlag: ``bool``
        :return: preparedId, an opaque string which may be used as an
            argument to isDataPrepared() and getPreparedData() calls.
        :rtype: ``str``
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, DataSelection):
            objs = DataSelection(objs)
        return self.ids.prepareData(objs, compressFlag, zipFlag)

    def isDataPrepared(self, preparedId):
        """Check if prepared data is ready at IDS.

        :param preparedId: the id returned by prepareData().
        :type preparedId: ``str``
        :return: ``True`` if the data is ready, otherwise ``False``.
        :rtype: ``bool``
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        return self.ids.isPrepared(preparedId)

    def getPreparedData(self, preparedId, outname=None, offset=0):
        """Retrieve prepared data from IDS.

        :param preparedId: the id returned by prepareData().
        :type preparedId: ``str``
        :param outname: the preferred name for the downloaded file to
            specify in the Content-Disposition header.
        :type outname: ``str``
        :param offset: if larger then zero, add Range header to the
            HTTP request with the indicated bytes offset.
        :type offset: ``int``
        :return: a file-like object as returned by
            ``urllib2.OpenerDirector.open()``
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        return self.ids.getPreparedData(preparedId, outname, offset)

    def getPreparedDataUrl(self, preparedId, outname=None):
        """Get the URL to retrieve prepared data from IDS.

        :param preparedId: the id returned by prepareData().
        :type preparedId: ``str``
        :param outname: the preferred name for the downloaded file to
            specify in the Content-Disposition header.
        :type outname: ``str``
        :return: the URL for tha data at the IDS.
        :rtype: ``str``
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        return self.ids.getPreparedDataUrl(preparedId, outname)

    def deleteData(self, objs):
        """Delete data from IDS.

        The data objects to delete are given in objs.  This can be
        any combination of single Datafiles, Datasets, or complete
        Investigations.

        :param objs: either a dict having some of the keys
            ``investigationIds``, ``datasetIds``, and ``datafileIds``
            with a list if object ids as value respectively, or a list
            of entity objects, or a data selection.
        :type objs: ``dict``, ``list`` of ``Entity``, or `DataSelection`
        """
        if not self.ids:
            raise RuntimeError("no IDS.")
        if not isinstance(objs, DataSelection):
            objs = DataSelection(objs)
        self.ids.delete(objs)


atexit.register(Client.cleanupall)
