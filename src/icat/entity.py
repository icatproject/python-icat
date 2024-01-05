"""Provide the Entity class.
"""

import re
from warnings import warn
import suds.sudsobject

from .listproxy import ListProxy
from .exception import InternalError, EntityTypeError, DataConsistencyError
from .helper import simpleqp_quote

__all__ = ['Entity']


class Entity():
    """The base of the classes representing the entities in the ICAT schema.

    Entity is the abstract base for a hierarchy of classes
    representing the entities in the ICAT schema.  It implements the
    basic behavior of these classes.

    Each Entity object is connected to an instance of
    :class:`suds.sudsobject.Object`, named *instance* in the
    following.  Instances are created by Suds based on the ICAT WSDL
    schema.  Entity objects mimic the behavior of the corresponding
    instance.  Attribute accesses are proxied to the instance.  A
    transparent conversion between Entity objects and Suds instances
    is performed where appropriate.
    """
    BeanName = None
    """Name of the entity in the ICAT schema, :const:`None` for abstract
    classes."""
    Constraint = ('id',)
    """Attribute or relation names that form a uniqueness constraint."""
    SelfAttr = frozenset(['client', 'instance', 'validate'])
    """Attributes stored in the Entity object itself."""
    InstAttr = frozenset(['id'])
    """Attributes of the entity in the ICAT schema, stored in the instance."""
    MetaAttr = frozenset(['createId', 'createTime', 'modId', 'modTime'])
    """Readonly meta attributes, retrieved from the instance."""
    InstRel = frozenset([])
    """Many to one relationships in the ICAT schema."""
    InstMRel = frozenset([])
    """One to many relationships in the ICAT schema."""
    AttrAlias = {}
    """Map of alias names for attributes and relationships."""
    SortAttrs = None
    """List of attributes used for sorting.  Uses Constraint if :const:`None`."""
    validate = None
    """Hook to add a pre create validation method.

    This may be set to a function that expects one argument, the
    entity object.  It will then be called before creating the object
    at the ICAT server.  The function is expected to raise an
    exception (preferably ValueError) in case of validation errors.
    """

    @classmethod
    def getInstanceName(cls):
        """Get the name of this class in the ICAT WSDL.

        .. versionadded:: 1.0.0
        """
        if cls is Entity:
            return 'entityBaseBean'
        else:
            return cls.__name__[0].lower() + cls.__name__[1:]

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
        return list(map(cls.getInstance, objs))

    @classmethod
    def getAttrInfo(cls, client, attr):
        """Get information on an attribute.

        Query the EntityInfo of the entity from the ICAT server and
        retrieve information on one of the attributes from it.

        :param client: the ICAT client.
        :type client: :class:`icat.client.Client`
        :param attr: name of the attribute.
        :type attr: :class:`str`
        :return: information on the attribute.
        :raise ValueError: if this is an abstract entity class or if
            no attribute by that name is found.
        """
        if cls.BeanName is None:
            raise ValueError("Cannot get info for an abstract entity class.")
        info = client.getEntityInfo(cls.BeanName)
        for f in info.fields:
            if f.name == attr:
                return f
        else:
            if attr in cls.MetaAttr:
                # ICAT server 4.4 and older did not add the meta
                # attributes in the entity info.  Create a fake
                # entityField to emulate the new behavior of ICAT
                # 4.5.0.
                f = client.factory.create('entityField')
                f.name = attr
                f.notNullable = False
                f.relType = "ATTRIBUTE"
                if attr in {'createTime', 'modTime'}:
                    f.type = "Date"
                else:
                    f.type = "String"
                return f
            else:
                raise ValueError("Unknown attribute name '%s'." % attr)

    @classmethod
    def getNaturalOrder(cls, client):
        """Return a natural order for this class.

        The order is a list of attributes suitable to be used in a
        ORDER BY clause in an ICAT search expression.  The natural
        order is the one that is as close as possible to sorting the
        objects by the :meth:`~icat.entity.Entity.__sortkey__`.  It is
        based on :attr:`~icat.entity.Entity.Constraint` or the
        :attr:`~icat.entity.Entity.SortAttrs`, if the latter are
        defined.  In any case, one to many relationships and nullable
        many to one relationships are removed from the list.
        """
        order = []
        attrs = list(cls.SortAttrs or cls.Constraint)
        if "id" in cls.Constraint and "id" not in attrs:
            attrs.append("id")
        for a in attrs:
            attrInfo = cls.getAttrInfo(client, a)
            if attrInfo.relType == "ATTRIBUTE":
                order.append(a)
            elif attrInfo.relType == "ONE":
                if not attrInfo.notNullable:
                    # skip, adding a nullable relation to ORDER BY
                    # would implicitly add a NOT NULL condition.
                    continue
                else:
                    rclass = client.getEntityClass(attrInfo.type)
                    rorder = rclass.getNaturalOrder(client)
                    order.extend(["%s.%s" % (a, ra) for ra in rorder])
            elif attrInfo.relType == "MANY":
                # skip, one to many relationships cannot be used in an
                # ORDER BY clause.
                continue
            else:
                raise InternalError("Invalid relType: '%s'" % attrInfo.relType)
        return order


    def __init__(self, client, instance, **kwargs):
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
            if not hasattr(self.instance, attr):
                # The list of objects in this one to many relation is
                # not present in the instance object.  There are two
                # possible causes for this: either this object does
                # not have any related objects or this relation has
                # not been included in the query when getting the
                # object from the server.  In the first case, setting
                # this to the empty list is the right thing to do.  In
                # the latter case, it might be completely wrong and we
                # should rather raise an AttributeError here.  But
                # there is no way at this point to distinguish between
                # the two cases, see ICAT Issue 130.
                setattr(self.instance, attr, [])
            l = EntityList(self.client, getattr(self.instance, attr))
            super().__setattr__(attr, l)
            return l
        elif attr == 'instancetype':
            return self.instance.__class__.__name__
        elif attr in self.AttrAlias:
            return self.__getattr__(self.AttrAlias[attr])
        else:
            raise AttributeError("%s object has no attribute %s" % 
                                 (type(self).__name__, attr))

    def __setattr__(self, attr, value):
        if attr in self.SelfAttr:
            super().__setattr__(attr, value)
        elif attr in self.InstAttr:
            setattr(self.instance, attr, value)
        elif attr in self.InstRel:
            setattr(self.instance, attr, self.getInstance(value))
        elif attr in self.InstMRel:
            setattr(self.instance, attr, [])
            l = EntityList(self.client, getattr(self.instance, attr))
            super().__setattr__(attr, l)
            l.extend(value)
        elif attr in self.AttrAlias:
            setattr(self, self.AttrAlias[attr], value)
        else:
            raise AttributeError("%s object cannot set attribute '%s'" %
                                 (type(self).__name__, attr))

    def __delattr__(self, attr):
        if attr in (self.InstAttr | self.InstRel):
            if hasattr(self.instance, attr):
                delattr(self.instance, attr)
        elif attr in self.InstMRel:
            if attr in self.__dict__:
                super().__delattr__(attr)
            if hasattr(self.instance, attr):
                delattr(self.instance, attr)
        elif attr in self.AttrAlias:
            delattr(self, self.AttrAlias[attr])
        else:
            raise AttributeError("%s object cannot delete attribute '%s'" %
                                 (type(self).__name__, attr))


    def copy(self):
        """Return a shallow copy of this entity object.

        Create a new object that has all attributes set to a copy of
        the corresponding values of this object.  The relations are
        copied by reference, i.e. the original and the copy refer to
        the same related object.

        >>> inv = client.new("Investigation", name="Investigation A")
        >>> ds = client.new("Dataset", investigation=inv, name="Dataset X")
        >>> cds = ds.copy()
        >>> cds.name
        'Dataset X'
        >>> cds.investigation.name
        'Investigation A'
        >>> cds.name = "Dataset Y"
        >>> cds.investigation.name = "Investigation B"
        >>> ds.name
        'Dataset X'
        >>> ds.investigation.name
        'Investigation B'
        """
        cobj = self.client.new(self.instance.__class__.__name__)
        for attr in (self.InstAttr | self.InstRel):
            value = getattr(self.instance, attr, None)
            setattr(cobj.instance, attr, value)
        for attr in self.InstMRel:
            if hasattr(self.instance, attr):
                values = getattr(self.instance, attr)
                setattr(cobj.instance, attr, values[:])
        return cobj


    def __eq__(self, e):
        if isinstance(e, Entity):
            return bool(id(self) == id(e) or 
                        (self.id and 
                         self.client == e.client and 
                         self.BeanName == e.BeanName and self.id == e.id))
        else:
            return NotImplemented

    def __ne__(self, e):
        if isinstance(e, Entity):
            return bool(id(self) != id(e) and 
                        (not self.id or 
                         self.client != e.client or 
                         self.BeanName != e.BeanName or self.id != e.id))
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.client) ^ ((hash(self.BeanName) ^ self.id) 
                                    if self.id else id(self))

    def __str__(self):
        return str(self.instance)

    def __repr__(self):
        return str(self)

    def __sortkey__(self):
        """Return a key for sorting.

        This is suitable to be passed as `key` to the
        :meth:`list.sort` method. E.g. if `l` is a list of
        :class:`~icat.entity.Entity` objects, you can sort it using:

        >>> l.sort(key=icat.entity.Entity.__sortkey__)
        """
        sortattrs = self.SortAttrs or self.Constraint
        s = [ self.BeanName ]
        for attr in sortattrs:
            v = getattr(self, attr, None)
            if attr in self.InstAttr:
                if v is None:
                    v = ''
                else:
                    v = str(v)
            elif attr in self.InstRel:
                if v is None:
                    v = []
                else:
                    v = v.__sortkey__()
            elif attr in self.InstMRel:
                v = [ r.__sortkey__() for r in v ]
                v.sort()
            else:
                raise InternalError("Invalid sorting attribute '%s' in %s."
                                    % (attr, self.BeanName))
            s.append(v)
        return s

    def as_dict(self):
        """Return a dict with the object's attributes.
        """
        d = {}
        for a in self.InstAttr | self.MetaAttr:
            d[a] = getattr(self, a)
        return d


    def getAttrType(self, attr):
        """Get the type of an attribute.

        Query this object's EntityInfo from the ICAT server and
        retrieve the type of one of the attributes from it.  In the
        case of a relation attribute, this yields the BeanName of the
        related object.

        :param attr: name of the attribute.
        :type attr: :class:`str`
        :return: name of the attribute type.
        :rtype: :class:`str`
        :raise ValueError: if no attribute by that name is found.
        """
        if attr in self.AttrAlias:
            attr = self.AttrAlias[attr]
        return self.getAttrInfo(self.client, attr).type


    def truncateRelations(self, keepInstRel=False):
        """Delete all relationships.

        Delete all attributes having relationships to other objects
        from this object.  Note that this is a local operation on the
        object in the client only.  It does not affect the
        corresponding object at the ICAT server.  This is useful if
        you only need to keep the object's attributes but not the
        (possibly large) tree of related objects in local memory.

        :param keepInstRel: if :const:`True`, delete only the one to
            many, but keep the many to one relationships.  This is
            particularly useful if you want to call
            :meth:`~icat.entity.Entity.update` for this object later
            on, because in this case, you'd definitely need to keep
            the many to one relationships, but you may want to avoid
            transmitting a large tree of objects in one to many
            relationships to the ICAT server in the call, as they'd be
            essentially useless then.
        :type keepInstRel: :class:`bool`

        .. versionchanged:: 1.1.0
            add the `keepInstRel` argument.
        """
        rels = self.InstMRel if keepInstRel else (self.InstRel | self.InstMRel)
        for r in rels:
            delattr(self, r)
        

    def getUniqueKey(self, keyindex=None):
        """Return a unique key.

        The key is a string that is guaranteed to be unique for all
        entities in the ICAT.  All attributes that form the uniqueness
        constraint must be set.  A :meth:`icat.client.Client.search`
        or :meth:`icat.client.Client.get` with the appropriate include
        clause may be required before calling this method.

        if `keyindex` is not :const:`None`, it is used as a cache of
        previously generated keys.  It must be a dict that maps entity
        ids to the keys returned by previous calls of
        :meth:`~icat.entity.Entity.getUniqueKey` on other entity
        objects.  The newly generated key will be added to this index.

        :param keyindex: cache of generated keys.
        :type keyindex: :class:`dict`
        :return: a unique key.
        :rtype: :class:`str`
        :raise DataConsistencyError: if a relation required in a
            constraint is not set.
        """

        kid = (self.BeanName, self.id)
        if keyindex is not None and kid in keyindex:
            return keyindex[kid]

        key = self.BeanName
        for c in self.Constraint:
            key += "_"
            if c in self.InstAttr:
                key += "%s-%s" % (c, simpleqp_quote(getattr(self, c, None)))
            elif c in self.InstRel:
                e = getattr(self, c, None)
                if e:
                    ek = e.getUniqueKey(keyindex)
                    key += "%s-(%s)" % (c, re.sub(r'^[A-Z-a-z]+_', '', ek))
                else:
                    raise DataConsistencyError("Required relation '%s' "
                                               "not present in %s"
                                               % (c, self.BeanName))
            else:
                raise InternalError("Invalid constraint '%s' in %s."
                                    % (c, self.BeanName))
        if keyindex is not None:
            keyindex[kid] = key
        return key

    def create(self):
        """Call :meth:`icat.client.Client.create` to create the object in the
        ICAT.
        """ 
        self.id = self.client.create(self)

    def update(self):
        """Call :meth:`icat.client.Client.update` to update the object in the
        ICAT.
        """ 
        self.client.update(self)

    def get(self, query=None):
        """Call :meth:`icat.client.Client.get` to get the object from the
        ICAT.
        """ 
        if self.BeanName is None:
            raise EntityTypeError("Cannot get an object of abstract type '%s'." 
                                  % self.instancetype)
        if self.id is None:
            raise ValueError("Id is not set. Must create me first.")
        if query is None:
            query = "%s INCLUDE 1" % self.BeanName
        nself = self.client.get(query, self.id)
        self.instance = nself.instance
        return self



class EntityList(ListProxy):
    """A list of Entity objects.

    It actually is a proxy to a list of
    :class:`suds.sudsobject.Object` instances.  List items are
    converted on the fly: Entity objects are converted to
    suds.sudsobject.Object when stored into the list and converted
    back to Entity objects when retrieved.
    """

    def __init__(self, client, instancelist):
        super().__init__(instancelist)
        self.client = client

    def __getitem__(self, index):
        item = super().__getitem__(index)
        if isinstance(index, slice):
            return [self.client.getEntity(i) for i in item]
        else:
            return self.client.getEntity(item)

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            instance = Entity.getInstances(value)
        else:
            instance = Entity.getInstance(value)
        super().__setitem__(index, instance)

    def insert(self, index, value):
        instance = Entity.getInstance(value)
        super().insert(index, instance)

