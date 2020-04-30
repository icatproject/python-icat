"""Verfify that deprecated features raise a deprecation warning.
"""

try:
    from importlib import reload
except ImportError:
    # Python 3.3 or older
    from imp import reload
import sys
import pytest
import icat
import icat.exception

# Deprecations not tested in this module:
# - Deprecated calls icat.ids.IDSClient.getPreparedData() and similar.
#   These calls require a valid prepareId and thus uploaded content in
#   IDS.  It's easier to test this in test_06_ids.py.
# - Predefined configuration variable configDir.
#   It's easier to test this in the setting of the test_01_config.py
#   module.

@pytest.mark.skipif(sys.version_info >= (3, 4),
                    reason="this Python version is not deprecated")
def test_deprecated_python_version():
    """Support for Python 2.7 and 3.3 is deprecated since 0.17.0.
    :mod:`icat` should check the Python version and raise a
    DeprecationWarning if applicable.
    """
    with pytest.deprecated_call():
        reload(icat)

def test_deprecated_module_icat_cgi():
    """:mod:`icat.cgi` is deprecated since 0.13.0.
    """
    with pytest.deprecated_call():
        import icat.cgi
        reload(icat.cgi)

def test_deprecated_module_icat_icatcheck():
    """:mod:`icat.icatcheck` is deprecated since 0.17.0.
    """
    with pytest.deprecated_call():
        import icat.icatcheck
        reload(icat.icatcheck)

def test_deprecated_stripCause():
    """:func:`icat.exception.stripCause` is deprecated since 0.14.0.
    """
    err = icat.exception.ICATError("some spurious error")
    with pytest.deprecated_call():
        icat.exception.stripCause(err)
