"""Provide the Client class.

This is the only module that needs to be imported to use the icat.
"""

from warnings import warn
import logging
from distutils.version import StrictVersion as Version
import atexit
import shutil

import suds
import suds.client
import suds.sudsobject

from icat.entity import Entity
import icat.entities
from icat.exception import *

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
    'sample': icat.entities.Sample,
    'sampleParameter': icat.entities.SampleParameter,
    'sampleType': icat.entities.SampleType,
    'shift': icat.entities.Shift,
    'study': icat.entities.Study,
    'studyInvestigation': icat.entities.StudyInvestigation,
    'user': icat.entities.User,
    'userGroup': icat.entities.UserGroup43,
    }
"""Map instance types defined in the WSDL to Python classes (ICAT 4.3.*)."""

class Client(suds.client.Client):
 
    """A client accessing an ICAT service.

    Client is a subclass of suds.client.Client and inherits most of
    its behavior.  It adds methods for the instantiation of ICAT
    entities and implementations of the ICAT API methods.

    :group ICAT API methods: login, logout, create, createMany,
        delete, deleteMany, get, getApiVersion, getEntityInfo,
        getEntityNames, getProperties, getRemainingMinutes,
        getUserName, isAccessAllowed, luceneClear, luceneCommit,
        lucenePopulate, luceneSearch, refresh, search, searchText,
        update
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

        super(Client, self).__init__(url, **kwargs)
        self.apiversion = Version(self.getApiVersion())
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
        elif self.apiversion < '4.4':
            self.typemap = TypeMap43.copy()
        else:
            warn(ClientVersionWarning(self.apiversion, "too new"))
            self.typemap = TypeMap43.copy()

        self.sessionId = None
        self.autoLogout = True

        self.Register[id(self)] = self

    def __del__(self):
        """Call `cleanup`."""
        self.cleanup()

    def cleanup(self):

        """Release resources allocated by the client.

        Logout from the active ICAT session (if ``self.autoLogout`` is
        True) and delete the temporary cache directory.  The client
        should not be used any more after calling this method.
        """

        if id(self) in self.Register:
            if self.autoLogout:
                self.logout()

            # Try our best to clean the temporary cache dir, but don't
            # bother trying to recover from any errors doing so, just
            # ignore any exceptions.
            try:
                if self.options.cache.location:
                    shutil.rmtree(self.options.cache.location)
            except:
                pass

            del self.Register[id(self)]


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
                raise TypeError("Invalid instance type '%s'." % instancetype)
        elif isinstance(obj, basestring):
            # obj is the name of an instance type, create the instance
            instancetype = obj
            try:
                Class = self.typemap[instancetype]
            except KeyError:
                raise TypeError("Invalid instance type '%s'." % instancetype)
            instance = self.factory.create(instancetype)
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
        try:
            return self.service.getEntityInfo(beanName)
        except suds.WebFault as e:
            raise translateError(e)

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


    # ================== convenience methods ===================

    def createUser(self, name, search=False, **kwargs):
        """Search a user by name or Create a new user.

        If search is ``True`` search a user by the given name.  If
        search is ``False`` or no user is found, create a new user.

        :param name: username.
        :type name: ``str``
        :param search: flag wether a user should be searched first.
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
        g.addUser(users)
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
            if self.apiversion < '4.3':
                r = self.new("rule", crudFlags=crudFlags, what=w, group=group)
            else:
                r = self.new("rule", crudFlags=crudFlags, what=w, grouping=group)
            rules.append(r)
        return self.createMany(rules)

    def assertedSearch(self, query, assertmin=1, assertmax=1):
        """Search with an assertion on the result.

        Perform a search and verify that the number of items found
        lies with the bounds of assertmin and assertmax.  Raise an
        error if this assertion fails.

        :param query: the search query string.
        :type query: ``str``
        :param assertmin: minimum number of expected results.
        :type assertmin: ``int``
        :param assertmax: maximum number of expected results.
        :type assertmax: ``int``
        :return: search result.
        :rtype: ``list``
        :raise ValueError: in case of inconsistent arguments.
        :raise SearchResultError: if the assertion on the number of
            results fails.
        """
        if assertmin > assertmax:
            raise ValueError("Minimum (%d) is larger then maximum (%d)."
                             % (assertmin, assertmax))
        result = self.search(query)
        num = len(result)
        if num >= assertmin and num <= assertmax:
            return result
        else:
            raise SearchResultError(query, assertmin, assertmax, num)


atexit.register(Client.cleanupall)
