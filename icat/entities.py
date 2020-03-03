"""Provide the classes corresponding to the entities in the ICAT schema.

Entity classes defined in this module are derived from the abstract
base class :class:`icat.entity.Entity`.  They override the class
attributes :attr:`icat.entity.Entity.BeanName`,
:attr:`icat.entity.Entity.Constraint`,
:attr:`icat.entity.Entity.InstAttr`,
:attr:`icat.entity.Entity.InstRel`,
:attr:`icat.entity.Entity.InstMRel`,
:attr:`icat.entity.Entity.AttrAlias`, and
:attr:`icat.entity.Entity.SortAttrs` as appropriate.

.. note::
   This module is used internally in :mod:`icat.client`.  Most users
   will not need to use it directly.
"""

import itertools
from icat.entity import Entity
from icat.exception import InternalError


class GroupingMixin:

    def addUsers(self, users):
        ugs = []
        uids = set()
        for u in users:
            if u.id in uids:
                continue
            ugs.append(self.client.new('userGroup', user=u, grouping=self))
            uids.add(u.id)
        if ugs:
            self.client.createMany(ugs)

    def getUsers(self, attribute=None):
        if attribute is not None:
            query = ("User.%s <-> UserGroup <-> %s [id=%d]" 
                     % (attribute, self.BeanName, self.id))
        else:
            query = ("User <-> UserGroup <-> %s [id=%d]" 
                     % (self.BeanName, self.id))
        return self.client.search(query)


class InstrumentMixin:

    def addInstrumentScientists(self, users):
        iss = []
        for u in users:
            iss.append(self.client.new('instrumentScientist', 
                                       instrument=self, user=u))
        if iss:
            self.client.createMany(iss)

    def getInstrumentScientists(self, attribute=None):
        if attribute is not None:
            query = ("User.%s <-> InstrumentScientist <-> Instrument [id=%d]" 
                     % (attribute, self.id))
        else:
            query = ("User <-> InstrumentScientist <-> Instrument [id=%d]" 
                     % (self.id))
        return self.client.search(query)


class InvestigationMixin:

    def addInstrument(self, instrument):
        ii = self.client.new('investigationInstrument', 
                             investigation=self, instrument=instrument)
        ii.create()

    def addKeywords(self, keywords):
        kws = []
        for k in keywords:
            kws.append(self.client.new('keyword', name=k, investigation=self))
        if kws:
            self.client.createMany(kws)

    def addInvestigationUsers(self, users, role='Investigator'):
        ius = []
        for u in users:
            ius.append(self.client.new('investigationUser', 
                                       investigation=self, user=u, role=role))
        if ius:
            self.client.createMany(ius)


class Investigation44Mixin(InvestigationMixin):

    def addInvestigationGroup(self, group, role=None):
        ig = self.client.new('investigationGroup', investigation=self)
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
    typemap = {}
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
            for minver, extra in _extra_attrs[beanName]:
                if minver and minver > client.apiversion:
                    continue
                mixin = extra.pop('Mixin', None)
                attrs.update(extra)
        if mixin:
            bases = (parent, mixin)
        else:
            bases = (parent,)
        instanceName = beanName[0].lower() + beanName[1:]
        typemap[instanceName] = type(str(beanName), bases, attrs)
    return typemap
