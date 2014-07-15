"""Test module icat.helper
"""

import pytest
from icat.helper import simpleqp_quote, simpleqp_unquote, parse_attr_val

def test_helper_quote():
    """Test simpleqp_quote() and simpleqp_unquote()
    """

    name = u'rbeck'
    qps = simpleqp_quote(name)
    s = simpleqp_unquote(qps)
    assert s == name

    fullName = u'Rudolph Beck-D\\xfclmen'
    qps = simpleqp_quote(fullName)
    s = simpleqp_unquote(qps)
    assert s == fullName

def test_helper_parse_attr_val():
    """Test parse_attr_val()
    """

    k = "name-jdoe"
    assert parse_attr_val(k) == {'name': 'jdoe'}

    facilityname = 'ESNF'
    facilitykey = "%s-%s" % ("name", simpleqp_quote(facilityname))
    name = 'Nickel(II) oxide SC'
    molecularFormula = 'NiO'
    stkey = "_".join(["%s-(%s)" % ("facility", facilitykey), 
                      "%s-%s" % ("name", simpleqp_quote(name)), 
                      "%s-%s" % ("molecularFormula", 
                                 simpleqp_quote(molecularFormula))])
    assert stkey == ('facility-(name-ESNF)_name-Nickel=28II=29=20oxide=20SC'
                     '_molecularFormula-NiO')
    d = {
        'facility': 'name-ESNF', 
        'molecularFormula': 'NiO', 
        'name': 'Nickel=28II=29=20oxide=20SC', 
    }
    assert parse_attr_val(stkey) == d

    invname = "2012-EDDI-0390-1"
    visitid = 1
    invkey = "_".join(["%s-(%s)" % ("facility", facilitykey), 
                       "%s-%s" % ("name", simpleqp_quote(invname)), 
                       "%s-%s" % ("visitId", simpleqp_quote(visitid))])
    dsname = "e208945"
    dskey = "_".join(["%s-(%s)" % ("investigation", invkey), 
                      "%s-%s" % ("name", simpleqp_quote(dsname))])
    dfname = "e208945.dat"
    dfkey = "_".join(["%s-(%s)" % ("dataset", dskey), 
                      "%s-%s" % ("name", simpleqp_quote(dfname))])
    assert dfkey == ('dataset-(investigation-(facility-(name-ESNF)_'
                     'name-2012=2DEDDI=2D0390=2D1_visitId-1)_name-e208945)_'
                     'name-e208945=2Edat')

    df = parse_attr_val(dfkey)
    assert df['dataset'] == ('investigation-(facility-(name-ESNF)_'
                             'name-2012=2DEDDI=2D0390=2D1_visitId-1)_'
                             'name-e208945')

    ds = parse_attr_val(df['dataset'])
    d = {
        'investigation': 'facility-(name-ESNF)_name-2012=2DEDDI=2D0390=2D1_visitId-1', 
        'name': 'e208945', 
    }
    assert ds == d
    assert ds['investigation'] == invkey

def test_helper_parse_attr_val_err():
    """Test various error conditions in parse_attr_val()
    """

    # A key without a value
    with pytest.raises(ValueError):
        parse_attr_val("xx")

    # First attrvaluestring part valid, but then a key without a value
    # in the second attrvaluestring part.
    with pytest.raises(ValueError):
        parse_attr_val("name-jdoe_xx")

    # First attrvaluestring part valid, then a key with the value
    # separator but still without a value in the second
    # attrvaluestring part.
    with pytest.raises(ValueError):
        parse_attr_val("name-jdoe_xx-")

    # First attrvaluestring part valid, but then a value without a key
    # in the second attrvaluestring part.
    with pytest.raises(ValueError):
        parse_attr_val("name-jdoe_-xx")

    # Valid example
    facilityname = 'ESNF'
    facilitykey = "%s-%s" % ("name", simpleqp_quote(facilityname))
    instrname = "E2"
    instrkey = "_".join(["%s-(%s)" % ("facility", facilitykey), 
                         "%s-%s" % ("name", simpleqp_quote(instrname))])
    d = {
        'facility': 'name-ESNF', 
        'name': 'E2', 
    }
    assert parse_attr_val(instrkey) == d

    # Spurious open parenthesis
    instrkey = "_".join(["%s-((%s)" % ("facility", facilitykey), 
                         "%s-%s" % ("name", simpleqp_quote(instrname))])
    with pytest.raises(ValueError):
        parse_attr_val(instrkey)

    # Spurious close parenthesis
    instrkey = "_".join(["%s-(%s))" % ("facility", facilitykey), 
                         "%s-%s" % ("name", simpleqp_quote(instrname))])
    with pytest.raises(ValueError):
        parse_attr_val(instrkey)

    # Extra stuff after close parenthesis, expecting end of string or
    # separator for next attrvaluestring part here.
    instrkey = "_".join(["%s-(%s)xx" % ("facility", facilitykey), 
                         "%s-%s" % ("name", simpleqp_quote(instrname))])
    with pytest.raises(ValueError):
        parse_attr_val(instrkey)