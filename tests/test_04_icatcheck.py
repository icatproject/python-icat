"""Test compatibility of the client with the server version.
"""

from __future__ import print_function
import pytest
import icat
import icat.config
from icat.icatcheck import ICATChecker
from conftest import getConfig


@pytest.fixture(scope="module")
def checker():
    conf = getConfig(needlogin=False)
    client = icat.Client(conf.url, **conf.client_kwargs)
    return ICATChecker(client)


def test_schema(checker):
    """Test consistency of the schema in the client with the server.
    """
    assert checker.check() == 0, "Schema consistency warnings"

def test_exceptions(checker):
    """Test consistency of exceptions in the client with the server.
    """
    assert checker.checkExceptions() == 0, "Exception consistency warning"
