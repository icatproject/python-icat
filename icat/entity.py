"""Provide the Entity class.
"""

import re
import suds.sudsobject
from icat.listproxy import ListProxy
from icat.exception import InternalError
from icat.helper import simpleqp_quote

class Entity(object):
    """The base of the classes representing the entities in the ICAT schema.

    ``Entity`` is the abstract base for a hierarchy of classes
    representing the entities in the ICAT schema.  It implements the
    basic behavior of these classes.

    Each ``Entity`` object is connected to an instance of the
    ``suds.sudsobject.Object`` class, named *instance* in the
    following.  Instances are created by Suds based on the ICAT WSDL
    schema.  ``Entity`` objects mimic the behavior of the corresponding
    instance.  Attribute accesses are proxied to the instance.  A
    transparent conversion between ``Entity`` objects and Suds
    instances is performed where appropriate.
    """
    BeanName = None
    """Name of the entity in the ICAT schema, ``None`` for abstract classes."""
    Constraint = ('id',)
    """Attribute or relation names that form a uniqueness constraint."""
    SelfAttr = frozenset(['client', 'instance'])
    """Attributes stored in the ``Entity`` object itself."""
    InstAttr = frozenset(['id'])
    """Attributes of the entity in the ICAT schema, stored in the instance."""
    MetaAttr = frozenset(['createId', 'createTime', 'modId', 'modTime'])
    """Readonly meta attributes, retrieved from the instance."""
    InstRel = frozenset([])
    """Many to one relationships in the ICAT schema."""
    InstMRel = frozenset([])
    """One to many relationships in the ICAT schema."""
    AttrAlias = {}
    """Map of alias names for attributes and many to one relationships."""
    MRelAlias = {}
    """Map of alias names for one to many relationships."""


    @classmethod
    def getInstance(cls, obj):
        """Get the corresponding instance from an object."""
        if obj is None:
            return None
        elif isinstance(obj, suds.sudsobject.Object):
            return obj
        elif isinstance(obj, Entity):
            return obj.instance
        else:
            raise TypeError("invalid argument type '%s'" % type(obj))

    @classmethod
    def getInstances(cls, objs):
        """Translate a list of objects into the list of corresponding
        instances.
        """
        return map(cls.getInstance, objs)


    def __init__(self, client, instance, **kwargs):
        super(Entity, self).__init__()
        self.client = client
        self.instance = instance
        for a in kwargs:
            self.__setattr__(a, kwargs[a])


    def __getattr__(self, attr):
        if attr in self.InstAttr or attr in self.MetaAttr:
            return getattr(self.instance, attr, None)
        elif attr in self.InstRel:
            return self.client.new(getattr(self.instance, attr, None))
        elif attr in self.InstMRel:
            instancelist = getattr(self.instance, attr, None)
            if instancelist is None:
                raise AttributeError("Instance list '%s' is not present. " 
                                     "Get the object again from the server, "
                                     "using an INCLUDE statement in the "
                                     "search expression." % attr)
            l = EntityList(self.client, instancelist)
            super(Entity, self).__setattr__(attr, l)
            return l
        elif attr == 'instancetype':
            return self.instance.__class__.__name__
        elif attr in self.AttrAlias:
            return self.__getattr__(self.AttrAlias[attr])
        elif attr in self.MRelAlias:
            return self.__getattr__(self.MRelAlias[attr])
        else:
            raise AttributeError("%s object has no attribute %s" % 
                                 (type(self).__name__, attr))

    def __setattr__(self, attr, value):
        if attr in self.SelfAttr:
            super(Entity, self).__setattr__(attr, value)
        elif attr in self.InstAttr:
            setattr(self.instance, attr, value)
        elif attr in self.InstRel:
            setattr(self.instance, attr, self.getInstance(value))
        elif attr in self.AttrAlias:
            setattr(self, self.AttrAlias[attr], value)
        else:
            raise AttributeError("%s object cannot set attribute '%s'" %
                                 (type(self).__name__, attr))


    def __eq__(self, e):
        if isinstance(e, Entity):
            return self.instancetype == e.instancetype and self.id == e.id
        else:
            return NotImplemented

    def __ne__(self, e):
        if isinstance(e, Entity):
            return not (self.instancetype == e.instancetype and self.id == e.id)
        else:
            return NotImplemented

    def __str__(self):
        return str(self.instance)

    def __repr__(self):
        return str(self)


    def getUniqueKey(self, autoget=False, keyindex=None):
        """Return a unique kay.

        The key is a string that is guaranteed to be unique for all
        entities in the ICAT.  All attributes that form the uniqueness
        constraint must be set.  A ``search`` or ``get`` with the
        appropriate INCLUDE statement may be required before calling
        this method.

        If autoget is ``True`` the method will call ``get`` with the
        appropriate arguments.  Note that this may discard information
        on other relations currently present in the entity object.

        if keyindex is not ``None``, it is used as a cache of
        previously generated keys.  It must be a dict that maps entity
        ids to the keys returned by previous calls of getUniqueKey()
        on other entity objects.  The newly generated key will be
        added to this index.

        :param autoget: flag whether ``get`` shall be called in order
            to have all needed attributes set.
        :type autoget: ``bool``
        :param keyindex: cache of generated keys.
        :type keyindex: ``dict``
        :return: a unique key.
        :rtype: ``str``
        """

        if autoget:
            inclattr = [a for a in self.Constraint if a in self.InstRel]
            if inclattr:
                info = self.client.getEntityInfo(self.BeanName)
                incltypes = [f.type for f in info.fields if f.name in inclattr]
                self.get("%s INCLUDE %s" 
                         % (self.BeanName, ", ".join(incltypes)))
            else:
                self.get(self.BeanName)

        key = self.BeanName
        for c in self.Constraint:
            key += "_"
            if c in self.InstAttr:
                key += "%s-%s" % (c, simpleqp_quote(getattr(self, c, None)))
            elif c in self.InstRel:
                e = getattr(self, c, None)
                if e:
                    if keyindex is not None and e.id in keyindex:
                        ek = keyindex[e.id]
                    else:
                        ek = e.getUniqueKey(autoget, keyindex)
                    key += "%s-(%s)" % (c, re.sub(r'^[A-Z-a-z]+_', '', ek))
                else:
                    key += "%s-%s" % (c, None)
            else:
                raise InternalError("Invalid constraint '%s' in %s."
                                    % (c, self.BeanName))
        if keyindex is not None:
            keyindex[self.id] = key
        return key

    def create(self):
        """Call the ``create`` client API method to create the object
        in the ICAT.""" 
        self.id = self.client.create(self.instance)

    def update(self):
        """Call the ``update`` client API method to update the object
        in the ICAT.""" 
        self.client.update(self.instance)

    def get(self, query=None):
        """Call the ``get`` client API method to get the object from
        the ICAT.""" 
        if self.BeanName is None:
            raise TypeError("Cannot get an object of abstract type '%s'." % 
                            self.instancetype)
        if self.id is None:
            raise ValueError("Id is not set. Must create me first.")
        if query is None:
            query = "%s INCLUDE 1" % self.BeanName
        nself = self.client.get(query, self.id)
        self.instance = nself.instance
        return self



class EntityList(ListProxy):
    """A list of Entity objects.

    It actually is a proxy to a list of ``suds.sudsobject`` instances.
    List items are converted on the fly: `Entity` objects are
    converted to ``sudsobjects`` when stored into the list and
    converted back to ``Entity`` objects when retrieved.
    """

    def __init__(self, client, instancelist):
        super(EntityList, self).__init__(instancelist)
        self.client = client


    def __getitem__(self, index):
        item = super(EntityList, self).__getitem__(index)
        if isinstance(index, slice):
            return map(lambda i: self.client.getEntity(i), item)
        else:
            return self.client.getEntity(item)

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            instance = Entity.getInstances(value)
        else:
            instance = Entity.getInstance(value)
        super(EntityList, self).__setitem__(index, instance)

    def insert(self, index, value):
        instance = Entity.getInstance(value)
        super(EntityList, self).insert(index, instance)

