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

@pytest.mark.skipif(sys.version_info >= (3, 4),
                    reason="this Python version is not deprecated")
def test_deprecated_python_version():
    """Support for Python 2.7 and 3.3 is deprecated since 0.17.0.
    :mod:`icat` should check the Python version and raise a
    DeprecationWarning if applicable.
    """
    with pytest.deprecated_call():
        reload(icat)
