"""Test exception handling.
"""

import pytest
import icat
import icat.config
from icat.ids import DataSelection
from conftest import getConfig, tmpSessionId


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(ids="optional")
    client.login(conf.auth, conf.credentials)
    return client


def provokeICATSessionError(client):
    print("Provoke an ICATSessionError ...")
    invalidid = '-=- INVALID ID -=-'
    with tmpSessionId(client, invalidid):
        client.search("Facility")

def provokeICATParameterError(client):
    print("Provoke an ICATParameterError ...")
    client.search("Bogus")

@pytest.mark.parametrize("errcond", [
    provokeICATSessionError,
    provokeICATParameterError,
])
def test_icat_exception(client, errcond):
    """Test handling of exceptions raised by the ICAT server.

    Errors raised by the ICAT server should get properly translated to
    exceptions in the icat.ICATError hierarchy.
    """
    # Deliberatly not verifying the particular exception class, such
    # as ICATSessionError and ICATParameterError.  This would be a
    # test of the sematic of the error in question.  But this is a
    # server thing and out of scope of testing the client.
    with pytest.raises(icat.ICATError) as einfo:
        errcond(client)
    err = einfo.value
    print(repr(err))
    assert hasattr(err, 'message')
    assert hasattr(err, 'fault')
    assert err.offset is None
    assert getattr(err, '__cause__', None) is None


def test_icat_exception_many(client):
    """Test handling of exceptions raised from createMany().

    The offset attribute should be set for an excepton raised during a
    createMany() or deleteMany() call, to indicate which one of the
    arguments caused the error.
    """
    # Get an existing and a non-existing Dataset.
    dataset1 = client.assertedSearch("Dataset [name='e208341']")[0]
    dataset2 = client.new("Dataset", id=-11, name='e208342-invalid')
    df1 = client.new("Datafile", name="df_a.dat", dataset=dataset1)
    df2 = client.new("Datafile", name="df_b.dat", dataset=dataset2)
    df3 = client.new("Datafile", name="df_c.dat", dataset=dataset1)
    df4 = client.new("Datafile", name="df_d.dat", dataset=dataset2)
    print("Provoke an ICATInternalError ...")
    with pytest.raises(icat.ICATError) as einfo:
        client.createMany([ df1, df2, df3, df4 ])
    err = einfo.value
    print(repr(err))
    assert hasattr(err, 'message')
    assert hasattr(err, 'fault')
    # The first offending object, df2, was at index 1.
    assert err.offset == 1
    assert getattr(err, '__cause__', None) is None


def test_icat_exception_non_ascii(client):
    """Deal with non-ASCII characters in error messages.

    It may happen that part of the user input is cited in the error
    message from the ICAT server and that this input contains
    non-ASCII characters.  It is not important whether these non-ASCII
    characters are always reproduced correctly, but the error handling
    must at least deal with them gracefully.
    """
    keyword = b"Schl\xc3\xbcsselwort".decode('utf-8')
    print("Provoke an ICATParameterError ...")
    with pytest.raises(icat.ICATError) as einfo:
        client.getEntityInfo(keyword)
    err = einfo.value
    print(repr(err))
    assert keyword in err.fault.faultstring


def provokeIDSBadRequestError(client):
    print("Provoke an IDSBadRequestError ...")
    invalidid = '-=- INVALID ID -=-'
    client.ids.isPrepared(invalidid)

def provokeIDSNotFoundError(client):
    print("Provoke an IDSNotFoundError ...")
    selection = DataSelection({'datasetIds':[-11]})
    client.ids.getData(selection)

@pytest.mark.parametrize("errcond", [
    provokeIDSBadRequestError,
    provokeIDSNotFoundError,
])
def test_ids_exception(client, errcond):
    """Test handling of exceptions raised by the IDS server.

    Errors raised by the IDS server should get properly translated to
    exceptions in the icat.IDSError hierarchy.

    There used to be bugs in the client that caused a HTTP error to be
    raised rather than the corresponding IDSError exception.  (Fixed
    in 56905f1.)
    """
    # Same comment as in test_icat_exception() applies.
    if not client.ids:
        pytest.skip("no IDS configured")
    with pytest.raises(icat.IDSError) as einfo:
        errcond(client)
    err = einfo.value
    print(repr(err))
    assert hasattr(err, 'message')
    assert hasattr(err, 'status')
    assert hasattr(err, 'type')
    assert err.offset is None
    assert getattr(err, '__cause__', None) is None


def test_server_error_from_string():
    """The constructor of ServerError also accepts a string argument.

    This simplifies raising ICATErrors and IDSErrors from custom code
    which is mainly useful for testing.
    """
    msg = "foo error"
    err = icat.ICATInternalError(msg)
    print(repr(err))
    assert isinstance(err, icat.exception.ServerError)
    assert err.message == msg
    assert err.offset is None
