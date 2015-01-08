"""Provide the Query class.
"""

from warnings import warn
import icat.entity
from icat.exception import InternalError, QueryNullableOrderWarning

__all__ = ['Query']

substnames = {
    "datafileFormat":"dff",
    "dataset":"ds",
    "dataset.investigation":"i",
    "facility":"f",
    "grouping":"g",
    "instrumentScientists":"isc",
    "investigation":"i",
    "investigationGroups":"ig",
    "investigationInstruments":"ii",
    "investigationUsers":"iu",
    "parameters":"p",
    "parameters.type":"pt",
    "type":"t",
    "user":"u",
    "userGroups":"ug",
}
"""Symbolic names for the representation of related objects in
JOIN ... AS and INCLUDE ... AS.  Prescribing sensible names makes the
search expressions somewhat better readable.  There is no need for
completeness here.
"""

# ======================== Internal helper ===========================

def _parents(obj):
    """Iterate over the parents of obj as dot separated components.

    >>> list(_parents("a.bb.c.ddd.e.ff"))
    ['a', 'a.bb', 'a.bb.c', 'a.bb.c.ddd', 'a.bb.c.ddd.e']
    >>> list(_parents("abc"))
    []
    """
    s = 0
    while True:
        i = obj.find('.', s)
        if i < 0:
            break
        yield obj[:i]
        s = i+1

def _makesubst(objs):
    subst = {}
    substcount = 0
    for obj in sorted(objs):
        for o in _parents(obj):
            if o not in subst:
                if o in substnames and substnames[o] not in subst.values():
                    subst[o] = substnames[o]
                else:
                    substcount += 1
                    subst[o] = "s%d" % substcount
    return subst

def _dosubst(obj, subst, addas=True):
    i = obj.rfind('.')
    if i < 0:
        n = "o.%s" % (obj)
    else:
        n = "%s.%s" % (subst[obj[:i]], obj[i+1:])
    if addas and obj in subst:
        n += " AS %s" % (subst[obj])
    return n

# ========================== class Query =============================

class Query(object):
    """Build a query to search an ICAT server.

    The query uses the JPQL inspired syntax introduced with ICAT
    4.3.0.  It won't work with older ICAT servers.
    """

    def __init__(self, client, entity, 
                 order=None, conditions=None, includes=None, limit=None):

        """Initialize the query.

        :param client: the ICAT client.
        :type client: `Client`
        :param entity: the type of objects to search for.  This may
            either be an ``Entity`` subclass or the name of an entity
            type.
        :type entity: `Entity` or ``str``
        :param order: the sorting attributes to build the ORDER BY
            clause from.  See the `setOrder` method for details.
        :param conditions: the conditions to build the WHERE clause
            from.  See the `addConditions` method for details.
        :param includes: list of related objects to add to the INCLUDE
            clause.  See the `addIncludes` method for details.
        :param limit: a tuple (skip, count) to be used in the LIMIT
            clause.  See the `setLimit` method for details.
        """

        super(Query, self).__init__()
        self._init = True
        self.client = client

        if isinstance(entity, basestring):
            self.entity = self.client.getEntityClass(entity)
        elif issubclass(entity, icat.entity.Entity):
            if (entity in self.client.typemap.values() and 
                entity.BeanName is not None):
                self.entity = entity
            else:
                raise TypeError("Invalid entity type '%s'." % entity.__name__)
        else:
            raise TypeError("Invalid entity type '%s'." % type(entity))

        self.conditions = dict()
        self.addConditions(conditions)
        self.includes = set()
        self.addIncludes(includes)
        self.setOrder(order)
        self.setLimit(limit)
        self._init = None

    def setOrder(self, order):
        """Set the order to build the ORDER BY clause from.

        :param order: the list of the attributes used for sorting.
            A special value of `True` may be used to indicate the
            natural order of the entity type.  Any `False` value
            means no ORDER BY clause.
        :type order: ``list`` of ``str`` or ``bool``
        :raise ValueError: if the order contains invalid attributes
            that either do not exist or contain one to many
            relationships.
        """
        if order is True:

            self.order = self.entity.getNaturalOrder(self.client)

        elif order:

            self.order = []
            for obj in order:

                rclass = self.entity
                pattr = ""
                final = False
                for attr in obj.split('.'):

                    if pattr:
                        pattr += ".%s" % attr
                    else:
                        pattr = attr
                    if final:
                        # Last component was attribute, no further
                        # components in the name allowed.
                        raise ValueError("Invalid attribute '%s' for %s." 
                                         % (obj, self.entity.BeanName))

                    attrInfo = rclass.getAttrInfo(self.client, attr)
                    if attrInfo.relType == "ATTRIBUTE":
                        final = True
                    elif attrInfo.relType == "ONE":
                        if (not attrInfo.notNullable and 
                            pattr not in self.conditions):
                            if self._init:
                                sl=3
                            else:
                                sl=2
                            warn(QueryNullableOrderWarning(pattr), 
                                 stacklevel=sl)
                        rclass = self.client.getEntityClass(attrInfo.type)
                    elif attrInfo.relType == "MANY":
                        raise ValueError("Cannot use one to many relationship "
                                         "in '%s' to order %s." 
                                         % (obj, self.entity.BeanName))
                    else:
                        raise InternalError("Invalid relType: '%s'" 
                                            % attrInfo.relType)

                if final:
                    # obj is an attribute, use it right away.
                    self.order.append(obj)
                else:
                    # obj is a related object, use the natural order
                    # of its class.
                    rorder = rclass.getNaturalOrder(self.client)
                    self.order.extend(["%s.%s" % (obj, ra) for ra in rorder])

        else:

            self.order = []

    def addConditions(self, conditions):
        """Add conditions to the constraints to build the WHERE clause from.

        :param conditions: the conditions to restrict the search
            result.  This should be a mapping of attribute names to
            conditions on that attribute.  The latter may either be a
            string with a single condition or a list of strings to add
            more then one condition on a single attribute.  If the
            query already has a condition on a given attribute, it
            will be turned into a list with the new condition(s)
            appended.
        :type conditions: ``dict``
        """
        if conditions:
            for a in conditions.keys():
                if a in self.conditions:
                    conds = []
                    if isinstance(self.conditions[a], basestring):
                        conds.append(self.conditions[a])
                    else:
                        conds.extend(self.conditions[a])
                    if isinstance(conditions[a], basestring):
                        conds.append(conditions[a])
                    else:
                        conds.extend(conditions[a])
                    self.conditions[a] = conds
                else:
                    self.conditions[a] = conditions[a]

    def addIncludes(self, includes):
        """Add related objects to build the INCLUDE clause from.

        :param includes: list of related objects to add to the INCLUDE
            clause.
        :type includes: iterable of ``str``
        """
        if includes:
            self.includes.update(includes)

    def setLimit(self, limit):
        """Set the limits to build the LIMIT clause from.

        :param limit: a tuple (skip, count).
        :type limit: ``tuple``
        """
        if limit:
            self.limit = limit
        else:
            self.limit = None            

    def __repr__(self):
        """Return a formal representation of the query.
        """
        return ("%s(%s, %s, order=%s, conditions=%s, includes=%s, limit=%s)"
                % (self.__class__.__name__, 
                   repr(self.client), repr(self.entity), 
                   repr(self.order), repr(self.conditions), 
                   repr(self.includes), repr(self.limit)))

    def __str__(self):
        """Return a string representation of the query.
        """
        base = "SELECT o FROM %s o" % self.entity.BeanName
        joinattrs = set(self.order) | set(self.conditions.keys())
        subst = _makesubst(joinattrs)
        joins = ""
        for obj in sorted(subst.keys()):
            joins += " JOIN %s" % _dosubst(obj, subst)
        if self.conditions:
            conds = []
            for a in sorted(self.conditions.keys()):
                attr = _dosubst(a, subst, False)
                cond = self.conditions[a]
                if isinstance(cond, basestring):
                    conds.append("%s %s" % (attr, cond))
                else:
                    for c in cond:
                        conds.append("%s %s" % (attr, c))
            where = " WHERE " + " AND ".join(conds)
        else:
            where = ""
        if self.order:
            orders = [ _dosubst(a, subst, False) for a in self.order ]
            order = " ORDER BY " + ", ".join(orders)
        else:
            order = ""
        if self.includes:
            subst = _makesubst(self.includes)
            self.addIncludes(subst.keys())
            incl = [ _dosubst(obj, subst) for obj in sorted(self.includes) ]
            include = " INCLUDE " + ", ".join(incl)
        else:
            include = ""
        if self.limit:
            limit = " LIMIT %s, %s" % self.limit
        else:
            limit = ""
        return base + joins + where + order + include + limit

    def copy(self):
        """Return an independent clone of this query.
        """
        q = Query(self.client, self.entity)
        q.order = list(self.order)
        q.conditions = self.conditions.copy()
        q.includes = self.includes.copy()
        q.limit = self.limit
        return q
