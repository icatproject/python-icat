"""Provide the Entity class.
"""

import suds.sudsobject
from icat.listproxy import ListProxy

class Entity(object):
    """The base of the classes representing the entities in the ICAT schema.

    C{Entity} is the abstract base for a hierarchy of classes
    representing the entities in the ICAT schema.  It implements the
    basic behavior of these classes.

    Each C{Entity} object is connected to an instance of the
    C{suds.sudsobject.Object} class, named I{instance} in the
    following.  Instances are created by Suds based on the ICAT WSDL
    schema.  C{Entity} objects mimic the behavior of the corresponding
    instance.  Attribute accesses are proxied to the instance.  A
    transparent conversion between C{Entity} objects and Suds
    instances is performed where appropriate.
    """
    BeanName = None
    """Name of the entity in the ICAT schema, C{None} for abstract classes."""
    SelfAttr = frozenset(['client', 'instance'])
    """Attributes stored in the C{Entity} object itself."""
    InstAttr = frozenset(['id'])
    """Attributes of the entity in the ICAT schema, stored in the instance."""
    MetaAttr = frozenset(['createId', 'createTime', 'modId', 'modTime'])
    """Readonly meta attributes, retrieved from the instance."""
    InstRel = frozenset([])
    """Many to one relationships in the ICAT schema."""
    InstMRel = frozenset([])
    """One to many relationships in the ICAT schema."""


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


    def create(self):
        """Call the C{create} client API method to create the object
        in the ICAT.""" 
        self.id = self.client.create(self.instance)

    def update(self):
        """Call the C{update} client API method to update the object
        in the ICAT.""" 
        self.client.update(self.instance)

    def get(self, query=None):
        """Call the C{get} client API method to get the object from
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

    It actually is a proxy to a list of suds.sudsobject instances.
    List items are converted on the fly: Entity objects are converted
    to sudsobjects when stored into the list and converted back to
    Entity objects when retrieved.
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

