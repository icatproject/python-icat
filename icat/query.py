"""Provide the Query class.
"""

import icat.client
import icat.entity
import icat.entities
from icat.exception import InternalError

__all__ = ['Query']

def getentityclassbyname(client, name):
    """Return the Entity class corresponding to a BeanName for the client.
    """
    # FIXME: consider to make this a client method.
    for c in client.typemap.values():
        if name == c.BeanName:
            return c
    else:
        raise ValueError("Invalid entity type '%s'." % name)

def getnaturalordering(client, entity):
    """Return the natural ordering of the Enitity class entity.
    """
    # FIXME: consider to make this a client method or a class method
    # in Entity.
    ordering = []
    attrs = list(entity.SortAttrs or entity.Constraint)
    if "id" in entity.Constraint and "id" not in attrs:
        attrs.append("id")
    for a in attrs:
        if a in entity.InstAttr:
            ordering.append(a)
        elif a in entity.InstRel:
            rname = client.getEntityAttrType(entity.BeanName, a)
            rclass = getentityclassbyname(client, rname)
            rordering = getnaturalordering(client, rclass)
            ordering.extend(["%s.%s" % (a, ra) for ra in rordering])
        elif a in entity.InstMRel:
            # skip, one to many relationships cannot be used in an
            # ORDER BY clause.
            continue
        else:
            raise InternalError("Invalid sorting attribute '%s' in %s."
                                % (a, entity.BeanName))
    return ordering

def parents(obj):
    """Iterate over the parents of obj as dot separated components.

    >>> list(parents("a.bb.c.ddd.e.ff"))
    ['a', 'a.bb', 'a.bb.c', 'a.bb.c.ddd', 'a.bb.c.ddd.e']
    >>> list(parents("abc"))
    []
    """
    s = 0
    while True:
        i = obj.find('.', s)
        if i < 0:
            break
        yield obj[:i]
        s = i+1

def makesubst(objs):
    subst = {}
    substcount = 0
    for obj in sorted(objs):
        for o in parents(obj):
            if o not in subst:
                substcount += 1
                subst[o] = "s%d" % substcount
    return subst

def dosubst(obj, subst):
    i = obj.rfind('.')
    if i < 0:
        n = "o.%s" % (obj)
    else:
        n = "%s.%s" % (subst[obj[:i]], obj[i+1:])
    if obj in subst:
        n += " AS %s" % (subst[obj])
    return n

class Query(object):
    """Build a query to search an ICAT server.

    The query uses the JPQL inspired syntax introduced with ICAT
    4.3.0.  It won't work with older ICAT servers.
    """

    # FIXME: as a first version, we implement only a rather restricted
    # type of conditions in the WHERE clause, namely a list of
    # attribute equal value pairs combined by AND.  A more general
    # solution might be desirable: other operators, more general
    # boolean expressions.  In the restricted case, each attribute may
    # naturally only appear once.  In the general case, the same
    # attribute may appear more then once, e.g. "o.a > 5 AND o.a < 10".

    def __init__(self, client, entity, 
                 ordering=None, conditions=None, includes=None):

        """Initialize the query.

        :param client: the ICAT client.
        :type client: `Client`
        :param entity: the type of objects to search for.  This may
            either be an ``Entity`` subclass or the name of an entity
            type.
        :type entity: `Entity` or ``str``
        :param ordering: the sorting attributes to build the ORDER BY
            clause from.  See the `setOrdering` method for details.
        :param conditions: the conditions to build the WHERE clause
            from.  See the `addConditions` method for details.
        :param includes: list of related objects to add to the INCLUDE
            clause.  See the `addIncludes` method for details.
        """

        super(Query, self).__init__()
        self.client = client

        if isinstance(entity, basestring):
            self.entity = getentityclassbyname(self.client, entity)
        elif issubclass(entity, icat.entity.Entity):
            if (entity in self.client.typemap.values() and 
                entity.BeanName is not None):
                self.entity = entity
            else:
                raise TypeError("Invalid entity type '%s'." % entity.__name__)
        else:
            raise TypeError("Invalid entity type '%s'." % type(entity))

        self.setOrdering(ordering)
        self.conditions = dict()
        self.addConditions(conditions)
        self.includes = set()
        self.addIncludes(includes)

    def setOrdering(self, ordering):
        """Set the ordering to build the ORDER BY clause from.

        :param ordering: the list of the attributes used for sorting.
            A special value of `True` may be used to indicate the
            natural ordering of the entity type.  Any `False` value
            means no ORDER BY clause.
        :type ordering: ``list`` of ``str`` or ``bool``
        """
        if ordering is True:
            self.ordering = getnaturalordering(self.client, self.entity)
        elif ordering:
            # FIXME ...
            self.ordering = ordering
        else:
            self.ordering = []

    def addConditions(self, conditions):
        """Add conditions to the constraints to build the WHERE clause from.

        :param conditions: the conditions to restrict the search
            result.  This should be a mapping of attribute names to
            values.
        :type conditions:  ``dict``
        """
        if conditions:
            # FIXME ...
            self.conditions.update(conditions)

    def addIncludes(self, includes):
        """Add related objects to build the INCLUDE clause from.

        :param includes: list of related objects to add to the INCLUDE
            clause.
        :type includes: iterable of ``str``
        """
        if includes:
            # FIXME ...
            self.includes.update(includes)

    def __repr__(self):
        """Return a formal representation of the query.
        """
        return ("%s(%s, %s, ordering=%s, conditions=%s, includes=%s)"
                % (self.__class__.__name__, 
                   repr(self.client), repr(self.entity), 
                   repr(self.ordering), repr(self.conditions), 
                   repr(self.includes)))

    def __str__(self):
        """Return a string representation of the query.
        """
        base = "SELECT o FROM %s o" % self.entity.BeanName
        joinattrs = set(self.ordering) | set(self.conditions.keys())
        subst = makesubst(joinattrs)
        joins = ""
        for obj in sorted(subst.keys()):
            joins += " JOIN %s" % dosubst(obj, subst)
        if self.conditions:
            conds = [ "%s = %s" % (dosubst(a, subst), self.conditions[a]) 
                      for a in sorted(self.conditions.keys()) ]
            where = " WHERE " + " AND ".join(conds)
        else:
            where = ""
        if self.ordering:
            orders = [ dosubst(a, subst) for a in self.ordering ]
            order = " ORDER BY " + ", ".join(orders)
        else:
            order = ""
        if self.includes:
            subst = makesubst(self.includes)
            self.addIncludes(subst.keys())
            incl = [ dosubst(obj, subst) for obj in sorted(self.includes) ]
            include = " INCLUDE " + ", ".join(incl)
        else:
            include = ""
        return base + joins + where + order + include
