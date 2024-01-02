"""Provide the classes corresponding to the entities in the ICAT schema.

The classes representing the entities in the ICAT schema are
dynamically created based on the entity information queried from the
ICAT server.  The classes are derived from the abstract base class
:class:`icat.entity.Entity`.  They override the class attributes
:attr:`icat.entity.Entity.BeanName`,
:attr:`icat.entity.Entity.Constraint`,
:attr:`icat.entity.Entity.InstAttr`,
:attr:`icat.entity.Entity.InstRel`,
:attr:`icat.entity.Entity.InstMRel`,
:attr:`icat.entity.Entity.AttrAlias`, and
:attr:`icat.entity.Entity.SortAttrs` as appropriate.

.. versionchanged:: 0.17.0
    create the entity classes dynamically.
"""

import itertools

from .entity import Entity
from .exception import InternalError


class GroupingMixin:
    """Mixin class to define custom methods for Grouping objects.
    """

    def addUsers(self, users):
        """Add users to the group.
        """
        ugs = []
        uids = set()
        for u in users:
            if u.id in uids:
                continue
            ugs.append(self.client.new("UserGroup", user=u, grouping=self))
            uids.add(u.id)
        if ugs:
            self.client.createMany(ugs)

    def getUsers(self, attribute=None):
        """Get the users in the group.  If `attribute` is given, return the
        corresponding attribute for all users in the group, otherwise
        return the users.
        """
        if attribute is not None:
            query = ("User.%s <-> UserGroup <-> %s [id=%d]" 
                     % (attribute, self.BeanName, self.id))
        else:
            query = ("User <-> UserGroup <-> %s [id=%d]" 
                     % (self.BeanName, self.id))
        return self.client.search(query)


class InstrumentMixin:
    """Mixin class to define custom methods for Instrument objects.
    """

    def addInstrumentScientists(self, users):
        """Add instrument scientists to the instrument.
        """
        iss = []
        for u in users:
            iss.append(self.client.new("InstrumentScientist",
                                       instrument=self, user=u))
        if iss:
            self.client.createMany(iss)

    def getInstrumentScientists(self, attribute=None):
        """Get instrument scientists of the instrument.  If `attribute` is
        given, return the corresponding attribute for all users
        related to the instrument, otherwise return the users.
        """
        if attribute is not None:
            query = ("User.%s <-> InstrumentScientist <-> Instrument [id=%d]" 
                     % (attribute, self.id))
        else:
            query = ("User <-> InstrumentScientist <-> Instrument [id=%d]" 
                     % (self.id))
        return self.client.search(query)


class InvestigationMixin:
    """Mixin class to define custom methods for Investigation objects.
    """

    def addInstrument(self, instrument):
        """Add an instrument to the investigation.
        """
        ii = self.client.new("InvestigationInstrument",
                             investigation=self, instrument=instrument)
        ii.create()

    def addKeywords(self, keywords):
        """Add keywords to the investigation.
        """
        kws = []
        for k in keywords:
            kws.append(self.client.new("Keyword", name=k, investigation=self))
        if kws:
            self.client.createMany(kws)

    def addInvestigationUsers(self, users, role='Investigator'):
        """Add investigation users.
        """
        ius = []
        for u in users:
            ius.append(self.client.new("InvestigationUser",
                                       investigation=self, user=u, role=role))
        if ius:
            self.client.createMany(ius)


class Investigation44Mixin(InvestigationMixin):
    """Mixin class to define custom methods for Investigation objects for
    ICAT version 4.4.0 and later.
    """

    def addInvestigationGroup(self, group, role=None):
        """Add an investigation group.
        """
        ig = self.client.new("InvestigationGroup", investigation=self)
        ig.grouping = group
        ig.role = role
        ig.create()


_parent = {
    'DataCollectionParameter': 'parameter',
    'DatafileParameter': 'parameter',
    'DatasetParameter': 'parameter',
    'InvestigationParameter': 'parameter',
    'SampleParameter': 'parameter',
}

_extra_attrs = {
    'Parameter': [
        (None, {
            'BeanName': None,
        }),
    ],
    'DataCollection': [
        (None, {
            'AttrAlias': {'parameters': 'dataCollectionParameters'},
            'SortAttrs': ('dataCollectionDatasets', 'dataCollectionDatafiles'),
        }),
        ('4.3.1', {
            'AttrAlias': {'dataCollectionParameters': 'parameters'},
        }),
    ],
    'DataCollectionDatafile': [
        (None, {
            'SortAttrs': ('datafile',),
        }),
    ],
    'DataCollectionDataset': [
        (None, {
            'SortAttrs': ('dataset',),
        }),
    ],
    'DataPublicationDate': [
        (None, {
            'SortAttrs': ('publication', 'date', 'dateType'),
        }),
    ],
    'DataPublicationUser': [
        (None, {
            'SortAttrs': ('publication', 'contributorType', 'orderKey', 'user'),
        }),
    ],
    'Grouping': [
        (None, {
            'Mixin': GroupingMixin,
        }),
    ],
    'Instrument': [
        (None, {
            'Mixin': InstrumentMixin,
        }),
    ],
    'Investigation': [
        (None, {
            'Mixin': InvestigationMixin,
        }),
        ('4.4.0', {
            'Mixin': Investigation44Mixin,
        }),
    ],
    'InvestigationType': [
        (None, {
            'SortAttrs': ('facility', 'name'),
        }),
    ],
    'Job': [
        (None, {
            'SortAttrs': ('application', 'arguments',
                          'inputDataCollection', 'outputDataCollection'),
        }),
    ],
    'Log': [
        (None, {
            'SortAttrs': ('operation', 'entityName'),
        }),
    ],
    'Publication': [
        (None, {
            'SortAttrs': ('investigation', 'fullReference'),
        }),
    ],
    'Rule': [
        (None, {
            'AttrAlias': {'group': 'grouping'},
            'SortAttrs': ('grouping', 'what'),
        }),
    ],
    'Study': [
        (None, {
            'SortAttrs': ('name',),
        }),
    ],
    'UserGroup': [
        (None, {
            'AttrAlias': {'group': 'grouping'},
        }),
    ],
}

def getTypeMap(client):
    """Generate a type map for the client.

    Query the ICAT server about the entity classes defined in the
    schema and their attributes and relations.  Generate corresponding
    Python classes representing these entities.  The Python classes
    are based on :class:`icat.entity.Entity`.

    :param client: a client object configured to connect to an ICAT
        server.
    :type client: :class:`icat.client.Client`
    :return: a mapping of type names from the ICAT web service
        description to the corresponding Python classes.  This mapping
        may be used as :attr:`icat.client.Client.typemap` for the
        client object.
    :rtype: :class:`dict`
    """
    def addType(typemap, cls):
        instanceName = cls.getInstanceName()
        typemap[instanceName] = cls
        typemap[instanceName.lower()] = cls

    typemap = dict()
    addType(typemap, Entity)
    for beanName in itertools.chain(('Parameter',), client.getEntityNames()):
        try:
            parent = typemap[_parent[beanName]]
        except KeyError:
            parent = Entity
        info = client.getEntityInfo(beanName)
        attrs = { 'BeanName': str(beanName), }
        try:
            attrs['__doc__'] = str(info.classComment)
        except AttributeError:
            attrs['__doc__'] = ""
        try:
            constraints = info.constraints[0]['fieldNames']
            if constraints:
                attrs['Constraint'] = tuple(str(n) for n in constraints)
        except AttributeError:
            pass
        instAttr = []
        instRel = []
        instMRel = []
        for field in info.fields:
            if field['name'] in parent.MetaAttr:
                continue
            elif field['relType'] == 'ATTRIBUTE':
                instAttr.append(str(field['name']))
            elif field['relType'] == 'ONE':
                instRel.append(str(field['name']))
            elif field['relType'] == 'MANY':
                instMRel.append(str(field['name']))
            else:
                raise InternalError("Invalid relType '%s'" % field['relType'])
        instAttr = frozenset(instAttr)
        if instAttr != parent.InstAttr:
            attrs['InstAttr'] = instAttr
        instRel = frozenset(instRel)
        if instRel != parent.InstRel:
            attrs['InstRel'] = instRel
        instMRel = frozenset(instMRel)
        if instMRel != parent.InstMRel:
            attrs['InstMRel'] = instMRel
        mixin = None
        if beanName in _extra_attrs:
            for minver, _e in _extra_attrs[beanName]:
                extra = dict(_e)
                if minver and minver > client.apiversion:
                    continue
                mixin = extra.pop('Mixin', None)
                attrs.update(extra)
        if mixin:
            bases = (parent, mixin)
        else:
            bases = (parent,)
        cls = type(str(beanName), bases, attrs)
        addType(typemap, cls)
    return typemap
