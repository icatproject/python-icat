"""A collection of internal helper routines.

**Note**: This module is intended for the internal use in python-icat
and is not considered to be part of the API.  No effort will be made
to keep anything in here compatible between different versions.

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

import sys
import datetime
import suds.sax.date


def simpleqp_quote(obj):
    """Simple quote in quoted-printable style."""
    esc = '='
    hex = '0123456789ABCDEF'
    asc = ('0123456789''ABCDEFGHIJKLMNOPQRSTUVWXYZ''abcdefghijklmnopqrstuvwxyz')
    if not isinstance(obj, basestring):
        obj = str(obj)
    s = obj.encode('utf-8')
    out = []
    for ch in s:
        # under Python 2 ch is a character (e.g. a string of length 1),
        # under Python 3 ch is an int.
        if isinstance(ch, int):
            i = ch
            c = chr(ch)
        else:
            i = ord(ch)
            c = ch
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
            c = i.next()
        except StopIteration:
            break
        if c == esc:
            try:
                hh = i.next()
                hl = i.next()
            except StopIteration:
                raise ValueError("Invalid quoted string '%s'" % qs)
            vh = hex.index(hh)
            vl = hex.index(hl)
            out.append(16*vh+vl)
        else:
            out.append(ord(c))

    # We got out as an int array.  Get an encoded string (e.g. str
    # under Python 2 and byte under Python 3) from it.
    if sys.version_info < (3, 0):
        s = ''.join([chr(i) for i in out])
    else:
        s = bytes(out)
    return s.decode('utf-8')

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
    if isinstance(dt, basestring):
        dt = parse_attr_string(dt, "Date")
    try:
        # datetime.timestamp() is new in Python 3.3.
        # timezone is new in Python 3.2.
        if not dt.tzinfo:
            # Unaware datetime values are assumed to be UTC.
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        ts = 1000 * dt.timestamp()
    except AttributeError:
        # Python 3.2 and older.
        if dt.tzinfo:
            # dt is aware.  Convert it to naive UTC.
            offs = dt.utcoffset()
            dt = dt.replace(tzinfo=None) - offs
        try:
            # timedelta.total_seconds() is new in Python 2.7 and 3.2.
            ts = 1000 * (dt - datetime.datetime(1970, 1, 1)).total_seconds()
        except AttributeError:
            # Python 2.6 or 3.1.
            td = dt - datetime.datetime(1970, 1, 1)
            ts = (1000 * (td.seconds + td.days * 24 * 3600) 
                  + td.microseconds / 1000)
    return int(ts)
