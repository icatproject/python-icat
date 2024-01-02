"""Provide the Query class.
"""

from collections import OrderedDict
import re
from warnings import warn
from collections.abc import Mapping

from .entity import Entity
from .exception import *

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

aggregate_fcts = frozenset([
    "DISTINCT",
    "COUNT",
    "COUNT:DISTINCT",
    "MIN",
    "MAX",
    "AVG",
    "AVG:DISTINCT",
    "SUM",
    "SUM:DISTINCT",
])
"""Allowed values for the `function` argument to the
:meth:`icat.query.Query.setAggregate` method.
"""

jpql_join_specs = frozenset([
    "JOIN",
    "INNER JOIN",
    "LEFT JOIN",
    "LEFT OUTER JOIN",
])
"""Allowed values for the `join_specs` argument to the
:meth:`icat.query.Query.setJoinSpecs` method.
"""

# ========================== class Query =============================

class Query():
    """Build a query to search an ICAT server.

    The query uses the JPQL inspired syntax introduced with ICAT
    4.3.0.  It won't work with older ICAT servers.

    :param client: the ICAT client.
    :type client: :class:`icat.client.Client`
    :param entity: the type of objects to search for.  This may either
        be an :class:`icat.entity.Entity` subclass or the name of an
        entity type.
    :param attributes: the attributes that the query shall return.  See
        the :meth:`~icat.query.Query.setAttributes` method for details.
    :param aggregate: the aggregate function to be applied in the
        SELECT clause, if any.  See the
        :meth:`~icat.query.Query.setAggregate` method for details.
    :param order: the sorting attributes to build the ORDER BY clause
        from.  See the :meth:`~icat.query.Query.setOrder` method for
        details.
    :param conditions: the conditions to build the WHERE clause from.
        See the :meth:`~icat.query.Query.addConditions` method for
        details.
    :param includes: list of related objects to add to the INCLUDE
        clause.  See the :meth:`~icat.query.Query.addIncludes` method
        for details.
    :param limit: a tuple (skip, count) to be used in the LIMIT
        clause.  See the :meth:`~icat.query.Query.setLimit` method for
        details.
    :param join_specs: a mapping to override the join specification
        for selected related objects.  See the
        :meth:`~icat.query.Query.setJoinSpecs` method for details.
    :raise TypeError: if `entity` is not a valid entity type or if any
        of the keyword arguments have an invalid type, see the
        corresponding method for details.
    :raise ValueError: if any of the keyword arguments is not valid,
        see the corresponding method for details.

    .. versionchanged:: 0.18.0
        add support for queries requesting a list of attributes rather
        than a single one.  Consequently, the keyword argument
        `attribute` has been renamed to `attributes` (in the plural).
    .. versionchanged:: 0.19.0
        add the `join_specs` argument.
    """

    _db_func_re = re.compile(r"(?:([A-Za-z_]+)\()?([A-Za-z.]+)(?(1)\))")

    def __init__(self, client, entity,
                 attributes=None, aggregate=None, order=None,
                 conditions=None, includes=None, limit=None,
                 join_specs=None):
        """Initialize the query.
        """

        self._init = True
        self.client = client

        if isinstance(entity, str):
            self.entity = self.client.getEntityClass(entity)
        elif issubclass(entity, Entity):
            if (entity in self.client.typemap.values() and
                entity.BeanName is not None):
                self.entity = entity
            else:
                raise EntityTypeError("Invalid entity type '%s'."
                                      % entity.__name__)
        else:
            raise EntityTypeError("Invalid entity type '%s'." % type(entity))

        self.setAttributes(attributes)
        self.setAggregate(aggregate)
        self.conditions = dict()
        self.addConditions(conditions)
        self.includes = set()
        self.addIncludes(includes)
        self.setJoinSpecs(join_specs)
        self.setOrder(order)
        self.setLimit(limit)
        self._init = None
        self._subst = None

    def _attrpath(self, attrname):
        """Follow the attribute path along related objects and iterate over
        the components.
        """
        rclass = self.entity
        pattr = ""
        for attr in attrname.split('.'):
            if pattr:
                pattr += ".%s" % attr
            else:
                pattr = attr
            if rclass is None:
                # Last component was not a relation, no further components
                # in the name allowed.
                raise ValueError("Invalid attrname '%s' for %s."
                                 % (attrname, self.entity.BeanName))
            attrInfo = rclass.getAttrInfo(self.client, attr)
            if attrInfo.relType == "ATTRIBUTE":
                rclass = None
            elif (attrInfo.relType == "ONE" or
                  attrInfo.relType == "MANY"):
                rclass = self.client.getEntityClass(attrInfo.type)
            else:
                raise InternalError("Invalid relType: '%s'" % attrInfo.relType)
            yield (pattr, attrInfo, rclass)

    def _makesubst(self, objs):
        subst = {}
        substcount = 0
        for obj in sorted(objs):
            i = obj.rfind('.')
            if i < 0:
                continue
            obj = obj[:i]
            for (o, attrInfo, oclass) in self._attrpath(obj):
                if o not in subst:
                    if o in substnames and substnames[o] not in subst.values():
                        subst[o] = substnames[o]
                    else:
                        substcount += 1
                        subst[o] = "s%d" % substcount
        return subst

    def _dosubst(self, obj, subst, addas=True):
        # Note: some old versions of icat.server require the path
        # mentioned in the WHERE clause to contain at least one dot.
        # So the query
        #
        #   SELECT o FROM Rule o JOIN o.grouping AS g WHERE g IS NOT NULL
        #
        # will raise an ICATParameterError with icat.server 4.6.1 and
        # older, while it will work for icat.server 4.7.0 and newer.
        # To remain compatible with the old versions, we always keep
        # one dot after substitution.
        i = obj.rfind('.')
        if i < 0:
            n = "o.%s" % (obj)
        else:
            n = "%s.%s" % (subst[obj[:i]], obj[i+1:])
        if addas and obj in subst:
            n += " AS %s" % (subst[obj])
        return n

    def _split_db_functs(self, attr):
        m = self._db_func_re.fullmatch(attr)
        if not m:
            raise ValueError("Invalid attribute '%s'" % attr)
        return m.group(2,1)

    def _get_subst(self):
        if self._subst is None:
            joinattrs = ( set(self.order.keys()) |
                          set(self.conditions.keys()) |
                          set(self.attributes) )
            self._subst = self._makesubst(joinattrs)
        return self._subst

    def setAttributes(self, attributes):
        """Set the attributes that the query shall return.

        :param attributes: the names of the attributes.  This can
            either be a single name or a list of names.  The result of
            the search will be a list with either a single attribute
            value or a list of attribute values respectively for each
            matching entity object.  If attributes is :const:`None`,
            the result will be the list of matching objects instead.
        :type attributes: :class:`str` or iterable of :class:`str`
        :raise ValueError: if any name in `attributes` is not valid or
            if multiple attributes are provided, but the ICAT server
            does not support this.

        .. versionchanged:: 0.18.0
            also accept a list of attribute names.  Renamed from
            :meth:`setAttribute` to :meth:`setAttributes` (in the
            plural).
        """
        self._subst = None
        self.attributes = []
        if attributes:
            if isinstance(attributes, str):
                attributes = [ attributes ]
            if (len(attributes) > 1 and
                not self.client._has_wsdl_type('fieldSet')):
                raise ValueError("This ICAT server does not support queries "
                                 "searching for multiple attributes")
            for attr in attributes:
                # Get the attribute path only to verify that the
                # attribute is valid.
                for (pattr, attrInfo, rclass) in self._attrpath(attr):
                    pass
                self.attributes.append(attr)

    def setAggregate(self, function):
        """Set the aggregate function to be applied to the result.

        Note that the Query class does not verify whether the
        aggregate function makes any sense for the selected result.
        E.g. the SUM of entity objects or the AVG of strings will
        certainly not work in an ICAT search expression, but it is not
        within the scope of the Query class to reject such nonsense
        beforehand.  Furthermore, "DISTINCT" requires icat.server
        4.7.0 or newer to work.  Again, this is not checked by the
        Query class.

        :param function: the aggregate function to be applied in the
            SELECT clause, if any.  Valid values are "DISTINCT",
            "COUNT", "MIN", "MAX", "AVG", "SUM", or :const:`None`.
            ":DISTINCT", may be appended to "COUNT", "AVG", and "SUM"
            to combine the respective function with "DISTINCT".
        :type function: :class:`str`
        :raise ValueError: if `function` is not valid.
        """
        if function:
            if function not in aggregate_fcts:
                raise ValueError("Invalid aggregate function '%s'" % function)
            self.aggregate = function
        else:
            self.aggregate = None

    def setJoinSpecs(self, join_specs):
        """Override the join specifications.

        :param join_specs: a mapping of related object names to join
            specifications.  Allowed values are "JOIN", "INNER JOIN",
            "LEFT JOIN", and "LEFT OUTER JOIN".  Any entry in this
            mapping overrides how this particular related object is to
            be joined.  The default for any relation not included in
            the mapping is "JOIN".  A special value of :const:`None`
            for `join_specs` is equivalent to the empty mapping.
        :type join_specs: :class:`dict`
        :raise TypeError: if `join_specs` is not a mapping.
        :raise ValueError: if any key in `join_specs` is not a name of
            a related object or if any value is not in the allowed
            set.

        .. versionadded:: 0.19.0
        """
        if join_specs:
            if not isinstance(join_specs, Mapping):
                raise TypeError("join_specs must be a mapping")
            for obj, js in join_specs.items():
                for (pattr, attrInfo, rclass) in self._attrpath(obj):
                    pass
                if rclass is None:
                    raise ValueError("%s.%s is not a related object"
                                     % (self.entity.BeanName, obj))
                if js not in jpql_join_specs:
                    raise ValueError("invalid join specification %s" % js)
            self.join_specs = join_specs
        else:
            self.join_specs = dict()

    def setOrder(self, order):
        """Set the order to build the ORDER BY clause from.

        :param order: the list of the attributes used for sorting.  A
            special value of :const:`True` may be used to indicate the
            natural order of the entity type.  Any false value means
            no ORDER BY clause.  The attribute name can be wrapped
            with a JPQL function (such as "LENGTH(title)").  Rather
            than only an attribute name, any item in the list may also
            be a tuple of an attribute name and an order direction,
            the latter being either "ASC" or "DESC" for ascending or
            descending order respectively.
        :type order: iterable or :class:`bool`
        :raise ValueError: if any attribute in `order` is not valid or
            if any attribute appears more than once in the resulting
            ORDER BY clause.

        .. versionchanged:: 0.19.0
            allow one to many relationships in `order`.  Emit a
            :exc:`~icat.exception.QueryOneToManyOrderWarning` rather
            than raising a :exc:`ValueError` in this case.
        .. versionchanged:: 0.20.0
            allow a JPQL function in the attribute.
        """
        self._subst = None
        # Note: with Python 3.7 and newer we could simplify this using
        # a standard dict() rather than an OrderedDict().
        self.order = OrderedDict()

        if order is True:

            for a in self.entity.getNaturalOrder(self.client):
                self.order[a] = "%s"

        elif order:

            for obj in order:

                if isinstance(obj, tuple):
                    obj, direction = obj
                    if direction not in ("ASC", "DESC"):
                        raise ValueError("Invalid ordering direction '%s'"
                                         % direction)
                else:
                    direction = None
                attr, jpql_func = self._split_db_functs(obj)

                for (pattr, attrInfo, rclass) in self._attrpath(attr):
                    if attrInfo.relType == "ONE":
                        if (not attrInfo.notNullable and
                            pattr not in self.conditions and
                            pattr not in self.join_specs):
                            sl = 3 if self._init else 2
                            warn(QueryNullableOrderWarning(pattr),
                                 stacklevel=sl)
                    elif attrInfo.relType == "MANY":
                        if (pattr not in self.join_specs):
                            sl = 3 if self._init else 2
                            warn(QueryOneToManyOrderWarning(pattr),
                                 stacklevel=sl)

                if jpql_func:
                    if rclass is not None:
                        raise ValueError("Cannot apply a JPQL function "
                                         "to a related object: %s" % obj)
                    if direction:
                        vstr = "%s(%%s) %s" % (jpql_func, direction)
                    else:
                        vstr = "%s(%%s)" % jpql_func
                else:
                    if direction:
                        vstr = "%%s %s" % direction
                    else:
                        vstr = "%s"
                if rclass is None:
                    # attr is an attribute, use it right away.
                    if attr in self.order:
                        raise ValueError("Cannot add %s more than once" % attr)
                    self.order[attr] = vstr
                else:
                    # attr is a related object, use the natural order
                    # of its class.
                    for ra in rclass.getNaturalOrder(self.client):
                        rattr = "%s.%s" % (attr, ra)
                        if rattr in self.order:
                            raise ValueError("Cannot add %s more than once"
                                             % rattr)
                        self.order[rattr] = vstr

    def addConditions(self, conditions):
        """Add conditions to the constraints to build the WHERE clause from.

        :param conditions: the conditions to restrict the search
            result.  This must be a mapping of attribute names to
            conditions on that attribute.  The latter may either be a
            string with a single condition or a list of strings to add
            more then one condition on a single attribute.  The
            attribute name (the key of the condition) can be wrapped
            with a JPQL function (such as "UPPER(title)").  If the
            query already has a condition on a given attribute, the
            previous condition(s) will be retained and the new
            condition(s) added to that.
        :type conditions: :class:`dict`
        :raise ValueError: if any key in `conditions` is not valid.

        .. versionchanged:: 0.20.0
            allow a JPQL function in the attribute.
        """
        def _cond_value(rhs, func):
            rhs = rhs.replace('%', '%%')
            if func:
                return "%s(%%s) %s" % (func, rhs)
            else:
                return "%%s %s" % (rhs)
        if conditions:
            self._subst = None
            for k in conditions.keys():
                if isinstance(conditions[k], str):
                    conds = [conditions[k]]
                else:
                    conds = conditions[k]
                a, jpql_func = self._split_db_functs(k)
                for (pattr, attrInfo, rclass) in self._attrpath(a):
                    pass
                v = [ _cond_value(rhs, jpql_func) for rhs in conds ]
                if a in self.conditions:
                    self.conditions[a].extend(v)
                else:
                    self.conditions[a] = v

    def addIncludes(self, includes):
        """Add related objects to build the INCLUDE clause from.

        :param includes: list of related objects to add to the INCLUDE
            clause.  A special value of "1" may be used to set (the
            equivalent of) an "INCLUDE 1" clause.
        :type includes: iterable of :class:`str`
        :raise ValueError: if any item in `includes` is not a related object.
        """
        if includes == "1":
            includes = list(self.entity.InstRel)
        if includes:
            for iobj in includes:
                for (pattr, attrInfo, rclass) in self._attrpath(iobj):
                    pass
                if rclass is None:
                    raise ValueError("%s.%s is not a related object."
                                     % (self.entity.BeanName, iobj))
            self.includes.update(includes)

    def setLimit(self, limit):
        """Set the limits to build the LIMIT clause from.

        :param limit: a tuple (skip, count).
        :type limit: :class:`tuple`
        :raise TypeError: if `limit` is not a tuple of two elements.
        """
        if limit:
            if not(isinstance(limit, tuple) and len(limit) == 2):
                raise TypeError("limit must be a tuple of two elements.")
            self.limit = limit
        else:
            self.limit = None

    @property
    def select_clause(self):
        """The SELECT clause of the query.

        .. versionadded:: 0.21.0
        """
        subst = self._get_subst()
        if self.attributes:
            attrs = []
            for a in self.attributes:
                if self.client.apiversion >= "4.7.0":
                    attrs.append(self._dosubst(a, subst, False))
                else:
                    # Old versions of icat.server do not accept
                    # substitution in the SELECT clause.
                    attrs.append("o.%s" % a)
            res = ", ".join(attrs)
        else:
            res = "o"
        if self.aggregate:
            if len(self.attributes) > 1 and self.aggregate == "DISTINCT":
                # See discussion in #76
                res = "%s %s" % (self.aggregate, res)
            else:
                for fct in reversed(self.aggregate.split(':')):
                    res = "%s(%s)" % (fct, res)
        return "SELECT %s FROM %s o" % (res, self.entity.BeanName)

    @property
    def join_clause(self):
        """The JOIN clause of the query.

        .. versionadded:: 0.21.0
        """
        subst = self._get_subst()
        joins = []
        for obj in sorted(subst.keys()):
            js = self.join_specs.get(obj, "JOIN")
            joins.append("%s %s" % (js, self._dosubst(obj, subst)))
        if joins:
            return " ".join(joins)
        else:
            return None

    @property
    def where_clause(self):
        """The WHERE clause of the query.

        .. versionadded:: 0.21.0
        """
        subst = self._get_subst()
        if self.conditions:
            conds = []
            for a in sorted(self.conditions.keys()):
                attr = self._dosubst(a, subst, False)
                for c in self.conditions[a]:
                    conds.append(c % attr)
            return "WHERE " + " AND ".join(conds)
        else:
            return None

    @property
    def order_clause(self):
        """The ORDER BY clause of the query.

        .. versionadded:: 0.21.0
        """
        subst = self._get_subst()
        if self.order:
            orders = []
            for a in self.order.keys():
                orders.append(self.order[a] % self._dosubst(a, subst, False))
            return "ORDER BY " + ", ".join(orders)
        else:
            return None

    @property
    def include_clause(self):
        """The INCLUDE clause of the query.

        .. versionadded:: 0.21.0
        """
        if self.includes:
            subst = self._makesubst(self.includes)
            includes = set(self.includes)
            includes.update(subst.keys())
            incl = [ self._dosubst(obj, subst) for obj in sorted(includes) ]
            return "INCLUDE " + ", ".join(incl)
        else:
            return None

    @property
    def limit_clause(self):
        """The LIMIT clause of the query.

        .. versionadded:: 0.21.0
        """
        if self.limit:
            return "LIMIT %s, %s" % self.limit
        else:
            return None

    def __repr__(self):
        """Return a formal representation of the query.
        """
        return ("%s(%s, %s, attributes=%s, aggregate=%s, order=%s, "
                "conditions=%s, includes=%s, limit=%s, join_specs=%s)"
                % (self.__class__.__name__,
                   repr(self.client), repr(self.entity.BeanName),
                   repr(self.attributes), repr(self.aggregate),
                   repr(self.order), repr(self.conditions),
                   repr(self.includes), repr(self.limit),
                   repr(self.join_specs)))

    def __str__(self):
        """Return a string representation of the query.
        """
        clauses = filter(None, (
            self.select_clause,
            self.join_clause,
            self.where_clause,
            self.order_clause,
            self.include_clause,
            self.limit_clause,
        ))
        return " ".join(clauses)

    def copy(self):
        """Return an independent clone of this query.
        """
        q = Query(self.client, self.entity)
        q.attributes = list(self.attributes)
        q.aggregate = self.aggregate
        q.order = self.order.copy()
        q.conditions = dict()
        for k, v in self.conditions.items():
            q.conditions[k] = self.conditions[k].copy()
        q.includes = self.includes.copy()
        q.limit = self.limit
        q.join_specs = self.join_specs.copy()
        return q
