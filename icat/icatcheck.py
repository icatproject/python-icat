"""Check the compatibility of the client with the ICAT server.

This module provides tests to check the compatibility of the client
with the WSDL description got from the ICAT server.  It is mainly
useful for the package maintainer.
"""

import re
import logging
from icat.entity import Entity
import icat.exception
from icat.exception import *

__all__ = ['ICATChecker']

log = logging.getLogger(__name__)


class EntityInfo(object):
    """Provide informations on an entity defined in the server."""

    def __init__(self, name, client):
        super(EntityInfo, self).__init__()
        self.name = name
        self.beanname = self.guessbeanname()
        self.info = client.getEntityInfo(self.beanname)
        self.classname = self.beanname

    def guessbeanname(self):
        """Guess the bean name from a WSDL type.

        Assume the bean name is equal to the type having the first
        letter capitalized.
        """
        t = self.name
        return t[0].upper() + t[1:]

    def getconstraint(self):
        """Return the constraint."""
        try:
            cl = [str(f) for f in self.info.constraints[0].fieldNames]
        except AttributeError:
            cl = ['id']
        return tuple(cl)

    def getfieldnames(self, relType=None):
        """Return the names of certain fields in the entity info."""
        if relType is None:
            names = [str(f.name) for f in self.info.fields]
        else:
            names = [str(f.name) for f in self.info.fields \
                         if f.relType == relType]
        return frozenset(names)

    def getattrs(self):
        """Return the attributes (relType == ATTRIBUTE)."""
        return self.getfieldnames('ATTRIBUTE')

    def getrelations(self):
        """Return the many to one relations (relType == ONE)."""
        return self.getfieldnames('ONE')

    def getmanyrelations(self):
        """Return the one to many relations (relType == MANY)."""
        return self.getfieldnames('MANY')

    def _cmpattrs(self, infoattrs, entityattrs, cname, typestr):
        """Helper for check()."""
        nwarn = 0
        missing = infoattrs - entityattrs
        if missing:
            log.warning("%s: missing %s: %s", cname, typestr, list(missing))
            nwarn += 1
        spurious = entityattrs - infoattrs
        if spurious:
            log.warning("%s: spurious %s: %s", cname, typestr, list(spurious))
            nwarn += 1
        return nwarn

    def check(self, entity):
        """Check whether the entity is consistent with this entity info.

        The entity is supposed to be a subclass of Entity.  Report any
        abnormalities as warnings to the logger.  Return the number of
        warnings emitted.
        """

        nwarn = 0

        if entity is None:
            return nwarn

        if not issubclass(entity, Entity):
            raise TypeError("invalid argument %s, expect subclass of Entity" % 
                            entity)
        cname = entity.__name__

        beanname = self.beanname
        if entity.BeanName is not None and entity.BeanName != beanname:
            log.warning("%s: wrong BeanName '%s', should be '%s'", 
                        cname, entity.BeanName, beanname)
            nwarn += 1

        constraint = self.getconstraint()
        if entity.Constraint != constraint:
            log.warning("%s: wrong Constraint '%s', should be '%s'", 
                        cname, entity.Constraint, constraint)
            nwarn += 1

        nwarn += self._cmpattrs(self.getattrs(), entity.InstAttr, 
                                cname, "attributes")
        nwarn += self._cmpattrs(self.getrelations(), entity.InstRel, 
                                cname, "many to one relations")
        nwarn += self._cmpattrs(self.getmanyrelations(), entity.InstMRel, 
                                cname, "one to many relations")

        return nwarn


    def pythonsrc(self, baseclass=None):
        """Generate Python source code that matches this entity info."""

        classname = self.classname
        baseclassname = 'object'
        classcomment = getattr(self.info, 'classComment', None)
        beanname = self.beanname
        addbeanname = True
        constraint = self.getconstraint()
        attrs = self.getattrs()
        rels = self.getrelations()
        mrels = self.getmanyrelations()

        if baseclass is not None and baseclass is not self:
            baseclassname = baseclass.classname
            if beanname == baseclass.beanname:
                addbeanname = False
            if constraint == baseclass.getconstraint():
                constraint = None
            if attrs == baseclass.getattrs():
                attrs = None
            if rels == baseclass.getrelations():
                rels = None
            if mrels == baseclass.getmanyrelations():
                mrels = None

        src = "class %s(%s):\n" % (classname, baseclassname)
        if classcomment:
            src += "    \"\"\"%s\"\"\"\n" % (classcomment)
        if addbeanname:
            src += "    BeanName = %s\n" % (repr(beanname))
        if constraint is not None:
            src += "    Constraint = %s\n" % (repr(constraint))
        if attrs is not None:
            src += "    InstAttr = %s\n" % (attrs)
        if rels is not None:
            src += "    InstRel = %s\n" % (rels)
        if mrels is not None:
            src += "    InstMRel = %s\n" % (mrels)
        src += "\n"

        return src


class ICATChecker(object):
    """Provide checks for the ICAT schema from a given server.

    Check that the entities defined in the ICAT client are in sync
    with the WSDL schema got from the ICAT server.
    """

    def __init__(self, client):
        super(ICATChecker, self).__init__()
        self.client = client
        try:
            sdl = client.sd
        except AttributeError:
            raise TypeError("No ServiceDefinition found on client.")
        if len(sdl) == 1:
            self.sd = sdl[0]
        else:
            raise ValueError("Expected the client to have one ServiceDefinition")
        self.schema = self.getentities()


    def gettypes(self):
        """Return a list of the types defined in the WSDL."""
        return [str(self.sd.xlate(t[0])) for t in self.sd.types]

    def getentities(self):
        """Search for entities defined at the server.

        Return a dict with type names as keys and EntityInfo objects
        as values.
        """
        entities = {}

        # The following will create lots of errors in suds.client, one
        # for every type that is not an entity.  Disable their logger
        # temporarily to avoid cluttering the log.
        sudslog = logging.getLogger('suds.client')
        sudssav = sudslog.disabled
        sudslog.disabled = True
        for t in self.gettypes():
            try:
                info = EntityInfo(t, self.client)
            except ICATError:
                continue
            entities[t] = info
        sudslog.disabled = sudssav

        return entities


    def check(self):
        """Check consistency of the ICAT client with the server schema.

        Report any abnormalities as warnings to the logger.  Returns
        the number of warnings emitted.
        """

        nwarn = 0

        # Check that the set of entity types is the same as in the
        # schema.
        schemanames = set(self.schema.keys())
        clientnames = set(self.client.typemap.keys())
        missing = schemanames - clientnames
        if missing:
            log.warning("missing entities: %s", list(missing))
            nwarn += 1
        spurious = clientnames - schemanames
        if spurious:
            log.warning("spurious entities: %s", list(spurious))
            nwarn += 1

        # For each entity type, check that its definition is
        # consistent with the schema.
        for n in schemanames & clientnames:
            log.debug("checking entity type %s ...", n)
            nwarn += self.schema[n].check(self.client.typemap[n])

        # Check that the ICAT exception types correspond to the
        # icatExceptionType as defined in the schema.
        icatExceptionType = self.client.factory.create('icatExceptionType')
        schemaexceptions = set(icatExceptionType.__keylist__)
        clientexceptions = set(icat.exception.IcatExceptionTypeMap.keys())
        missing = schemaexceptions - clientexceptions
        if missing:
            log.warning("missing exception types: %s", list(missing))
            nwarn += 1
        spurious = clientexceptions - schemaexceptions
        if spurious:
            log.warning("spurious exception types: %s", list(spurious))
            nwarn += 1

        return nwarn

    def _genealogy(self, rules):
        """Set up the genealogy of entity types."""

        tree = { t:{'level':0, 'base':None} for t in self.schema.keys() }
        for t in tree:
            log.debug("checking ancestors of %s ...", t)
            for r in rules:
                if re.match(r[0], t):
                    b = r[1]
                    if b == t:
                        b = None
                    tree[t]['base'] = b
                    c = t
                    l = tree[c]['level']
                    while b is not None:
                        log.debug("  ... %s is derived from %s", c, b)
                        c = b
                        try:
                            tree[c]
                        except KeyError:
                            raise GenealogyError("Unknown base type '%s' "
                                                 "in rules." % c)
                        if c == t:
                            raise GenealogyError("Loop in the genealogy tree "
                                                 "detected.")
                        l = max(tree[c]['level'], l+1)
                        tree[c]['level'] = l
                        b = tree[c]['base']
                    break

        # Check that there is only one root in the tree
        if len([t for t in tree if tree[t]['base'] is None]) != 1:
            raise GenealogyError("No unique root of genealogy tree.")

        return tree


    def pythonsrc(self, genealogyrules=[(r'','entityBaseBean')], baseclassname='Entity'):
        """Generate Python source code matching the ICAT schema.

        Generate source code for a set of classes that match the
        entity info found at the server.  The source code is returned
        as a string.

        The Python classes are created as a hierarchy.  It is assumed
        that there is one abstract base type which is the root of the
        genealogy tree.  In the case of the ICAT 4.2.* schema, this
        assumptions holds, the base is ``entityBaseBean``.

        The parameter genealogyrules defines the rules for the tree.
        It must be a list of tupels, each having two elements, a
        regular expression and the name of a parent type.  Each type
        matching the regular expression is assumed to be derived from
        the parent.  The first match in the list wins.  The last
        element in the list should be a default rule of the form
        ``(r'','base')``, where base is the name of the root.

        Entity classes having children in the hierarchy are assumed to
        be abstract.  In this case the attribut ``BeanName`` is set to
        ``None``.

        The parameter baseclassname is the name for the base class at
        the root of the tree used in the Python output.
        """

        try:
            tree = self._genealogy(genealogyrules)
        except GenealogyError as e:
            log.error("%s Dropping class genealogy in Python output.", 
                      e.args[0])
            tree = { t:{'level':0, 'base':None} for t in self.schema.keys() }
        else:
            base = [t for t in tree if tree[t]['base'] is None][0]
            self.schema[base].classname = baseclassname

        # Abstract entity classes are marked by setting BeanName to
        # None.
        for t in tree:
            if tree[t]['level'] > 0:
                self.schema[t].beanname = None

        types = tree.keys()
        types.sort(key=lambda t: (-tree[t]['level'], t))

        src = ""
        for t in types:
            try:
                b = self.schema[tree[t]['base']]
            except KeyError:
                b = None
            src += self.schema[t].pythonsrc(b)
            src += "\n"

        return src
