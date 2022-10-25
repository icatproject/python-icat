"""Test module icat.helper
"""

import datetime
import packaging.version
import pytest
from icat.helper import *

@pytest.mark.parametrize(("vstr", "checks"), [
    ("4.11.1", [
        (lambda v: v == "4.11.1", True),
        (lambda v: v < "4.11.1", False),
        (lambda v: v > "4.11.1", False),
        (lambda v: v < "5.0.0", True),
        (lambda v: v > "4.11.0", True),
        (lambda v: v > "4.9.3", True),
        (lambda v: v == packaging.version.Version("4.11.1"), True),
    ]),
    ("5.0.0-SNAPSHOT", [
        (lambda v: v == "5.0.0", False),
        (lambda v: v < "5.0.0", True),
        (lambda v: v > "4.11.1", True),
        (lambda v: v == "5.0.0-SNAPSHOT", True),
        (lambda v: v == "5.0.0a1", True),
        (lambda v: v < "5.0.0a2", True),
        (lambda v: v < "5.0.0b1", True),
    ]),
])
def test_version(vstr, checks):
    """Test class Version.
    """
    version = Version(vstr)
    for check, res in checks:
        assert check(version) == res

def test_helper_quote():
    """Test simpleqp_quote() and simpleqp_unquote()
    """

    name = b'rbeck'.decode('ascii')
    qps = simpleqp_quote(name)
    s = simpleqp_unquote(qps)
    assert s == name

    fullName = b'Rudolph Beck-D\xc3\xbclmen'.decode('utf-8')
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

@pytest.mark.parametrize(("s", "attrtype", "res"), [
    ("Foo", "String", "Foo"),
    ("42", "Integer", 42),
    ("5.3", "Double", 5.3),
    ("false", "boolean", False),
    ("0", "boolean", False),
    ("true", "boolean", True),
    ("1", "boolean", True),
])
def test_helper_parse_attr_string(s, attrtype, res):
    """Test parse_attr_string()
    """
    assert parse_attr_string(s, attrtype) == res

def test_helper_parse_attr_string_date():
    """Test parse_attr_string() for type Date
    """
    dstr = "2008-06-18T09:31:11+02:00"
    d = parse_attr_string(dstr, "Date")
    assert type(d) == datetime.datetime
    if d.tzinfo:
        # Suds jurko fork handles time zone information correctly and
        # returns "aware" datetime objects.  So we have a chance to
        # check the value.
        assert d.isoformat() == dstr

    dstr = "2008-06-18T07:31:11Z"
    d = parse_attr_string(dstr, "Date")
    assert type(d) == datetime.datetime
    if d.tzinfo:
        assert d.isoformat() == "2008-06-18T07:31:11+00:00"

cest = datetime.timezone(datetime.timedelta(hours=2))
mdt = datetime.timezone(datetime.timedelta(hours=-6))
@pytest.mark.parametrize(("dt", "ms"), [
    (datetime.datetime(2008, 6, 18, 7, 31, 11), 1213774271000), 
    ("2008-06-18T07:31:11", 1213774271000),
    pytest.param(datetime.datetime(2008, 6, 18, 7, 31, 11, 
                                   tzinfo=datetime.timezone.utc), 
                 1213774271000),
    ("2008-06-18T07:31:11Z", 1213774271000), 
    ("2008-06-18T07:31:11+00:00", 1213774271000), 
    pytest.param(datetime.datetime(2008, 6, 18, 9, 31, 11, tzinfo=cest), 
                 1213774271000),
    ("2008-06-18T09:31:11+02:00", 1213774271000), 
    pytest.param(datetime.datetime(2008, 6, 18, 1, 31, 11, tzinfo=mdt), 
                 1213774271000),
    ("2008-06-18T01:31:11-06:00", 1213774271000), 
])
def test_ms_timestamp(dt, ms):
    assert ms_timestamp(dt) == ms
