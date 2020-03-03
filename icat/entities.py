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

from icat.entity import Entity
from icat.exception import InternalError


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
    for beanName in client.getEntityNames():
        info = client.getEntityInfo(beanName)
        attrs = { 'BeanName': str(beanName), }
        try:
            attrs['__doc__'] = str(info.classComment)
        except AttributeError:
            pass
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
            if field['name'] in Entity.MetaAttr:
                continue
            elif field['relType'] == 'ATTRIBUTE':
                instAttr.append(str(field['name']))
            elif field['relType'] == 'ONE':
                instRel.append(str(field['name']))
            elif field['relType'] == 'MANY':
                instMRel.append(str(field['name']))
            else:
                raise InternalError("Invalid relType '%s'" % field['relType'])
        if instAttr and frozenset(instAttr) != Entity.InstAttr:
            attrs['InstAttr'] = frozenset(instAttr)
        if instRel:
            attrs['InstRel'] = frozenset(instRel)
        if instMRel:
            attrs['InstMRel'] = frozenset(instMRel)
        if beanName in _extra_attrs:
            for minver, extra in _extra_attrs[beanName]:
                if minver and minver > client.apiversion:
                    continue
                attrs.update(extra)
        instanceName = beanName[0].lower() + beanName[1:]
        typemap[instanceName] = type(str(beanName), (Entity,), attrs)
    return typemap
