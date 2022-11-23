|rtd| |pypi|

.. |rtd| image:: https://img.shields.io/readthedocs/python-icat/latest
   :target: https://python-icat.readthedocs.io/en/latest/
   :alt: Documentation build status

.. |pypi| image:: https://img.shields.io/pypi/v/python-icat
   :target: https://pypi.org/project/python-icat/
   :alt: PyPI version

python-icat – Python interface to ICAT and IDS
==============================================

This package provides a collection of modules for writing Python
programs that access an `ICAT`_ service using the SOAP interface.  It
is based on Suds and extends it with ICAT specific features.

Download
--------

The latest release version can be found in the
`Python Package Index (PyPI)`__.

.. __: `PyPI site`_


System requirements
-------------------

Python
......

+ 3.4 and newer.

Required library packages
.........................

+ `setuptools`_

+ `packaging`_

+ Suds.  The original version by Jeff Ortel is not maintained anymore
  since very long time and not supported.  There are several forks
  around, most of them short-lived.  Two of them have been evaluated
  with python-icat and found to work: the `fork by Jurko
  Gospodnetić`__ and the more recent `suds-community`_.  The latter
  has officially been renamed back to suds since version 1.0.0.  Note
  that suds-community does not work with older ICAT servers, see
  below.

.. __: `suds-jurko`_

Optional library packages
.........................

These packages are only needed to use certain extra features.  They
are not required to install or use python-icat itself:

+ `PyYAML`_

  Only needed to use the YAML backend of icatdump.py and icatingest.py
  and to run the example scripts (see below).

+ `lxml`_

  Only needed to use the XML backend of icatdump.py and icatingest.py.

+ `setuptools_scm`_

  The version number is managed using this package.  All source
  distributions add a static text file with the version number and
  fall back using that if `setuptools_scm` is not available.  So this
  package is only needed to build out of the plain development source
  tree as cloned from GitHub.

+ `pytest`_ >= 3.1.0

  Only if you want to run the tests.

+ `pytest-dependency`_ >= 0.2

  Only if you want to run the tests.

+ `distutils-pytest`_

  Only if you want to run the tests.


Installation
------------

Installation from PyPI
......................

You can install python-icat from PyPI using pip::

  $ pip install python-icat

Installation from the source distribution
.........................................

Steps to manually build from the source distribution:

1. Download the sources, unpack, and change into the source directory.

2. Build::

     $ python setup.py build

3. Test (optional, see below)::

     $ python setup.py test

4. Install::

     $ python setup.py install

The last step might require admin privileges in order to write into
the site-packages directory of your Python installation.

Building from development sources
.................................

For production use, it is always recommended to use the latest release
version from PyPI, see above.  If you need some not yet released
bleeding edge feature or if you want to participate in the
development, you may also clone the `source repository from GitHub`__.

Note that some source files are dynamically created and thus missing
in the development sources.  If you want to build from the development
sources, you may use the provided Makefile.  E.g. type ``make build``,
``make test``, and ``make sdist``.

.. __: `GitHub repository`_


Documentation
-------------

See the `online documentation`__.

Example scripts can be found in doc/examples.  This is mostly an
unsorted collection of test scripts that I initially wrote for myself
to try things out.

Almost all scripts use example_data.yaml as input for test data.  Of
course for real production, the input will come from different
sources, out of some workflow from the site.  But this would be
dynamic and site specific and thus not suitable, neither for testing
nor for the inclusion into example scripts.  So its easier to have
just one blob of dummy input data in one single file.  That is also
the reason why the example scripts require PyYAML.

.. __: `Read the Docs site`_


Test
----

There is no need to run the tests at all.  The test suite is mostly
useful to the maintainer of python-icat.

Most tests require a test ICAT server to talk to.  These tests are
disabled by default, unless you configure such a test server.  To do
so, place an icat.cfg file into tests/data.  This file must have at
least the configuration sections "root", "useroffice", "acord",
"ahau", "jbotu", "jdoe", "nbour", and "rbeck" with the options and
credentials to access the test server as the respective user.  See
doc/examples for an example.  Obviously, this implies that your
authentication plugin must also have these users configured.

**WARNING**: the tests are destructive!  They will delete all content
from the test server and replace it with example content.  Do not
configure the tests to access a production server!

You can safely run the tests without configuring any test server.  You
will just get many skipped tests then.


Bugs and limitations
--------------------

+ There are issues with ICAT server 4.8.0 and older when using
  suds-community, see `Issue #72`_ for details.  Use suds-jurko when
  you need to talk to those older ICAT servers.  On the other hand,
  suds-jurko does not seem to be maintained any more and can not be
  installed with setuptools 58.0.0 and newer.

+ If supported by the ICAT server (icat.server 4.9.0 and newer), the
  icat.config module queries the server for information on available
  authenticators and the credential keys they require for login.  The
  configuration variables for these keys are then adapted accordingly.
  Therefore, the set of configuration variables depends on the ICAT
  server and the available authentication plugins.  But the help
  message displayed by the `--help` command line option is static.  As
  a result, this help message is not always accurate.  When connecting
  to a specific ICAT service, it may happen that different
  configuration variables and thus command line arguments are
  effective then those shown by the generic help message.

+ The return value of the formal string representation operator of
  class Query can not be used to recreate another query object with
  the same value as required by Python standards, see `Issue #94`_ for
  details.

+ The entries in the no_proxy configuration variable are matched
  against the host part of the URL by simple string comparison.  The
  host is excluded from proxy use if its name ends with any item in
  no_proxy.  It is not checked whether the matching part starts with a
  domain component.  E.g. setting no_proxy=ion.example.org will not
  only exclude icat.ion.example.org, but also lion.example.org,
  although the latter is not in the ion.example.org domain.  IP
  addresses are not supported in no_proxy.  This is a limitation in
  the implementation of the underlying Python library.


Copyright and License
---------------------

Copyright 2013–2022
Helmholtz-Zentrum Berlin für Materialien und Energie GmbH

Licensed under the `Apache License`_, Version 2.0 (the "License"); you
may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.


.. _ICAT: https://icatproject.org/
.. _PyPI site: https://pypi.org/project/python-icat/
.. _setuptools: https://github.com/pypa/setuptools/
.. _packaging: https://github.com/pypa/packaging
.. _suds-jurko: https://bitbucket.org/jurko/suds
.. _suds-community: https://github.com/suds-community/suds
.. _PyYAML: https://github.com/yaml/pyyaml
.. _lxml: https://lxml.de/
.. _Requests: https://requests.readthedocs.io/
.. _setuptools_scm: https://github.com/pypa/setuptools_scm/
.. _pytest: https://docs.pytest.org/en/latest/
.. _pytest-dependency: https://pypi.org/project/pytest-dependency/
.. _distutils-pytest: https://github.com/RKrahl/distutils-pytest
.. _Read the Docs site: https://python-icat.readthedocs.io/
.. _GitHub repository: https://github.com/icatproject/python-icat
.. _Issue #72: https://github.com/icatproject/python-icat/issues/72
.. _Issue #94: https://github.com/icatproject/python-icat/issues/94
.. _PEP 440: https://www.python.org/dev/peps/pep-0440/
.. _Semantic Versioning: https://semver.org/
.. _Apache License: https://www.apache.org/licenses/LICENSE-2.0
