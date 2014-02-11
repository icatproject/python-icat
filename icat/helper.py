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
>>> facilityname = 'ESNF'
>>> facilitykey = "%s-%s" % ("name", simpleqp_quote(facilityname))
>>> name = 'Nickel(II) oxide SC'
>>> molecularFormula = 'NiO'
>>> stkey = "_".join(["%s-(%s)" % ("facility", facilitykey), 
...                   "%s-%s" % ("name", simpleqp_quote(name)), 
...                   "%s-%s" % ("molecularFormula", 
...                              simpleqp_quote(molecularFormula))])
>>> stkey
'facility-(name-ESNF)_name-Nickel=28II=29=20oxide=20SC_molecularFormula-NiO'
>>> parse_attr_val(stkey)
{'molecularFormula': 'NiO', 'name': 'Nickel=28II=29=20oxide=20SC', 'facility': 'name-ESNF'}
>>> invname = "2012-EDDI-0390-1"
>>> visitid = 1
>>> invkey = "_".join(["%s-(%s)" % ("facility", facilitykey), 
...                    "%s-%s" % ("name", simpleqp_quote(invname)), 
...                    "%s-%s" % ("visitId", simpleqp_quote(visitid))])
>>> dsname = "e208945"
>>> dskey = "_".join(["%s-(%s)" % ("investigation", invkey), 
...                   "%s-%s" % ("name", simpleqp_quote(dsname))])
>>> dfname = "e208945.dat"
>>> dfkey = "_".join(["%s-(%s)" % ("dataset", dskey), 
...                   "%s-%s" % ("name", simpleqp_quote(dfname))])
>>> dfkey
'dataset-(investigation-(facility-(name-ESNF)_name-2012=2DEDDI=2D0390=2D1_visitId-1)_name-e208945)_name-e208945=2Edat'
>>> df = parse_attr_val(dfkey)
>>> df['dataset']
'investigation-(facility-(name-ESNF)_name-2012=2DEDDI=2D0390=2D1_visitId-1)_name-e208945'
>>> ds = parse_attr_val(df['dataset'])
>>> ds
{'investigation': 'facility-(name-ESNF)_name-2012=2DEDDI=2D0390=2D1_visitId-1', 'name': 'e208945'}
>>> ds['investigation'] == invkey
True
"""

import sys
import doctest

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
    dict with any further processing.

    It might be easier to implement this using pyparsing, but this
    module is not in the standard library and I don't want to depend
    on external packages for this.
    """

    res = {}
    while len(avs) > 0:
        hyphen = avs.index('-')
        if hyphen == 0 or hyphen == len(avs)-1:
            raise ValueError("malformed '%s'" % s)
        attr = avs[:hyphen]
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
                raise ValueError("malformed '%s'" % s)
            value = avs[hyphen+2:i]
            if i == len(avs) - 1:
                avs = ""
            elif avs[i+1] == '_':
                avs = avs[i+2:]
            else:
                raise ValueError("malformed '%s'" % s)
        else:
            us = avs.find('_', hyphen+1)
            if us >= 0:
                value = avs[hyphen+1:us]
                avs = avs[us+1:]
            else:
                value = avs[hyphen+1:]
                avs = ""
        res[attr] = value
    return res


if __name__ == "__main__":
    doctest.testmod()
