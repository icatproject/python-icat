"""A collection of internal helper routines.

.. note::
   This module is intended for the internal use in python-icat and is
   not considered to be part of the API.  No effort will be made to
   keep anything in here compatible between different versions.

>>> name = 'rbeck'
>>> qps = simpleqp_quote(name)
>>> qps
'rbeck'
>>> s = simpleqp_unquote(qps)
>>> s
u'rbeck'
>>> name == s
True
>>> fullName = u'Rudolph Beck-D\\xfclmen'
>>> qps = simpleqp_quote(fullName)
>>> qps
'Rudolph=20Beck=2DD=C3=BClmen'
>>> s = simpleqp_unquote(qps)
>>> s
u'Rudolph Beck-D\\xfclmen'
>>> fullName == s
True
>>> parse_attr_val("name-jdoe")
{'name': 'jdoe'}
>>> key = "facility-(name-ESNF)_name-2010=2DE2=2D0489=2D1_visitId-1"
>>> d = parse_attr_val(key)
>>> d
{'visitId': '1', 'name': '2010=2DE2=2D0489=2D1', 'facility': 'name-ESNF'}
>>> parse_attr_val(d['facility'])
{'name': 'ESNF'}
"""

from contextlib import contextmanager
import datetime
import logging
import re
import packaging.version
import suds.sax.date


class Version(packaging.version.Version):
    """A variant of packaging.version.Version.

    This version class features a special handling of the '-SNAPSHOT'
    suffix being used for ICAT prereleases.  It furthermore adds
    comparison with strings.

    >>> version = Version('4.11.1')
    >>> version == '4.11.1'
    True
    >>> version < '4.9.3'
    False
    >>> version = Version('5.0.0-SNAPSHOT')
    >>> version
    <Version('5.0.0a1')>
    >>> version > '4.11.1'
    True
    >>> version < '5.0.0'
    True
    >>> version == '5.0.0a1'
    True

    .. versionadded:: 1.0.0
    """
    def __init__(self, version):
        super().__init__(re.sub(r'-SNAPSHOT$', 'a1', version))
    def __lt__(self, other):
        if isinstance(other, str):
            other = type(self)(other)
        return super().__lt__(other)
    def __le__(self, other):
        if isinstance(other, str):
            other = type(self)(other)
        return super().__le__(other)
    def __eq__(self, other):
        if isinstance(other, str):
            other = type(self)(other)
        return super().__eq__(other)
    def __ge__(self, other):
        if isinstance(other, str):
            other = type(self)(other)
        return super().__ge__(other)
    def __gt__(self, other):
        if isinstance(other, str):
            other = type(self)(other)
        return super().__gt__(other)
    def __ne__(self, other):
        if isinstance(other, str):
            other = type(self)(other)
        return super().__ne__(other)


def simpleqp_quote(obj):
    """Simple quote in quoted-printable style."""
    esc = '='
    hex = '0123456789ABCDEF'
    asc = ('0123456789''ABCDEFGHIJKLMNOPQRSTUVWXYZ''abcdefghijklmnopqrstuvwxyz')
    if not isinstance(obj, str):
        obj = str(obj)
    s = obj.encode('utf-8')
    out = []
    for i in s:
        c = chr(i)
        if c in asc:
            out.append(c)
        else:
            out.append(esc + hex[i//16] + hex[i%16])
    return ''.join(out)

def simpleqp_unquote(qs):
    """Simple unquote from quoted-printable style."""
    esc = '='
    hex = '0123456789ABCDEF'
    out = []
    i = iter(qs)
    while True:
        try:
            c = next(i)
        except StopIteration:
            break
        if c == esc:
            try:
                hh = next(i)
                hl = next(i)
            except StopIteration:
                raise ValueError("Invalid quoted string '%s'" % qs)
            vh = hex.index(hh)
            vl = hex.index(hl)
            out.append(16*vh+vl)
        else:
            out.append(ord(c))
    return bytes(out).decode('utf-8')

def parse_attr_val(avs):
    """Parse an attribute value list string.

    Parse a string representing a list of attribute and value pairs in
    the form::

        attrvaluestring ::= attrvalue 
                        |   attrvalue '_' attrvaluestring
        attrvalue       ::= attr '-' value
        value           ::= simplevalue 
                        |   '(' attrvaluestring ')'
        attr            ::= [A-Za-z]+
        simplevalue     ::= [0-9A-Za-z=]+

    Return a dict with the attributes as keys.  In the case of an
    attrvaluestring in parenthesis, this string is set as value in the
    dict without any further processing.
    """

    # It might be easier to implement this using pyparsing, but this
    # module is not in the standard library and I don't want to depend
    # on external packages for this.

    res = {}
    while len(avs) > 0:
        hyphen = avs.index('-')
        if hyphen == 0 or hyphen == len(avs)-1:
            raise ValueError("malformed '%s'" % avs)
        attr = avs[:hyphen]
        # FIXME: Should check that attr matches [A-Za-z]+ here.
        if avs[hyphen+1] == '(':
            # Need to find the matching ')'
            op = 0
            for i in range(hyphen+1,len(avs)):
                if avs[i] == '(':
                    op += 1
                elif avs[i] == ')':
                    op -= 1
                    if op == 0:
                        break
            if op > 0:
                raise ValueError("malformed '%s'" % avs)
            value = avs[hyphen+2:i]
            if i == len(avs) - 1:
                avs = ""
            elif avs[i+1] == '_':
                avs = avs[i+2:]
            else:
                raise ValueError("malformed '%s'" % avs)
        else:
            us = avs.find('_', hyphen+1)
            if us >= 0:
                value = avs[hyphen+1:us]
                avs = avs[us+1:]
            else:
                value = avs[hyphen+1:]
                avs = ""
            # FIXME: Should check that value matches [0-9A-Za-z=]+ here.
        res[attr] = value
    return res


def parse_attr_string(s, attrtype):
    """Parse the string representation of an entity attribute.

    Note: for Date we use the parser from :mod:`suds.sax.date`.  If
    this is the original Suds version, this parser is buggy and might
    yield wrong results.  But the same buggy parser is also applied by
    Suds internally for the Date values coming from the ICAT server.
    Since we are mainly interested to compare with values from the
    ICAT server, we have a fair chance that this comparision
    nevertheless yields valid results.
    """
    if s is None:
        return None
    if attrtype in ['String', 'ParameterValueType', 'StudyStatus']:
        return s
    elif attrtype in ['Integer', 'Long']:
        return int(s)
    elif attrtype == 'Double':
        return float(s)
    elif attrtype == 'boolean':
        # This is somewhat too liberal.  Valid values according XML
        # Schema Definition are only {"0", "false", "1", "true"} (case
        # sensitive).
        if s.lower() in ["0", "no", "n", "false", "f", "off"]:
            return False
        elif s.lower() in ["1", "yes", "y", "true", "t", "on"]:
            return True
        else:
            raise ValueError("Invalid boolean value '%s'" % s)
    elif attrtype == 'Date':
        d = suds.sax.date.DateTime(s)
        try:
            # jurko fork
            return d.value
        except AttributeError:
            # original Suds
            return d.datetime
    else:
        raise ValueError("Invalid attribute type '%s'" % attrtype)


def ms_timestamp(dt):
    """Convert :class:`datetime.datetime` or string to timestamp in
    milliseconds since epoch.
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = parse_attr_string(dt, "Date")
    if not dt.tzinfo:
        # Unaware datetime values are assumed to be UTC.
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    ts = 1000 * dt.timestamp()
    return int(ts)


@contextmanager
def disable_logger(name):
    """Context manager to temporarily disable a logger.
    """
    logger = logging.getLogger(name)
    sav_state = logger.disabled
    logger.disabled = True
    yield
    logger.disabled = sav_state
