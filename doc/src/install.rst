.. include:: _meta.rst

Install instructions
====================

See :ref:`install-using-pip` for the short version of the install
instructions.



System requirements
-------------------

Python
......

+ 3.6 and newer.

Required library packages
.........................

The following packages are required to install and use python-icat.
They will automatically be installed as dependencies if you install
using pip.

+ `setuptools`_

+ `packaging`_

+ :ref:`suds`, see below.

+ `lxml`_

  Needed for the :mod:`icat.ingest` module and to use the XML backend
  of :ref:`icatdump` and :ref:`icatingest`.  Not needed for the
  :ref:`python-icat core API <modref-core>`.

Optional library packages
.........................

These packages are only needed to use certain extra features.  They
are not required to install python-icat and use its core features:

+ `PyYAML`_

  Only needed to use the YAML backend of :ref:`icatdump` and
  :ref:`icatingest` and to run the example scripts.

  The test suite uses :ref:`icatingest` with the YAML backend to
  create reference content in the test ICAT server.  While it is
  technically possible to run the tests without PyYAML, most of the
  tests will be skipped in that case, so the results will not be very
  meaningful.

+ `git-props`_

  This package is used to extract some metadata such as the version
  number out of git, the version control system.  All releases embed
  that metadata in the distribution.  So this package is only needed
  to build out of the plain development source tree as cloned from
  GitHub, but not to build a release distribution.

+ `pytest`_ >= 3.1.0

  Only if you want to run the tests.

+ `pytest-dependency`_ >= 0.2

  Only if you want to run the tests.

+ `distutils-pytest`_ >= 0.2

  Only if you want to run the tests.

Note that the example scripts in doc/examples may have additional
dependencies.  In particular, a few of them need the `Requests`_
package.


.. _suds:

Suds
....

Suds is a lightweight SOAP-based web service client for Python.  The
original version was written by Jeff Ortel, but is not maintained
since very long time and does not work anymore.  There are several
forks around, most of them short-lived.  Two of them have been
evaluated with python-icat and found to work: `suds-jurko`_, the fork
by Jurko Gospodnetić and the more recent `suds-community`_.  The
latter has officially been renamed back to suds since version 1.0.0.

Note that suds-community does not work with ICAT server 4.8.0 and
older, see `Issue #72`_ for details.  So you'd need to use suds-jurko
when you need to talk to those older ICAT servers.  On the other hand,
suds-jurko does not seem to be maintained any more and can not be
installed with setuptools 58.0.0 and newer.

When you install python-icat using pip, suds-community will be
installed as a dependency by default.  If you want to use any other
Suds clone you need to install it first in a separate step, before
installing python-icat.  E.g. do something like the following if you
want to use python-icat with suds-jurko::

  $ pip install suds-jurko
  $ pip install python-icat


Installation
------------

.. _install-using-pip:

Installation using pip
......................

You can install python-icat from the
`Python Package Index (PyPI) <PyPI site_>`_ using pip::

  $ pip install python-icat

Note that while installing from PyPI is convenient, there is no way to
verify the integrity of the source distribution, which may be
considered a security risk.

Installation from the source distribution
.........................................

Note that the manual build does not automatically check the
dependencies.  So we assume that you have all the systems requirements
installed.  Steps to manually build from the source distribution:

1. Download the sources.

   From the `Release Page <GitHub latest release_>`_ you may download
   the source distribution file |distribution_source|_ and the
   detached signature file |distribution_signature|_

2. Check the signature (optional).

   You may verify the integrity of the source distribution by checking
   the signature (showing the output for version 1.2.0 as an example)::

     $ gpg --verify python-icat-1.2.0.tar.gz.asc
     gpg: assuming signed data in 'python-icat-1.2.0.tar.gz'
     gpg: Signature made Tue Oct 31 07:01:55 2023 CET
     gpg:                using RSA key 760465DAF652737A61EC0C9D83F336432C7FCC91
     gpg: Good signature from "Rolf Krahl <rolf.krahl@helmholtz-berlin.de>" [full]

   The signature should be made by the key
   :download:`0x760465DAF652737A61EC0C9D83F336432C7FCC91
   <83F336432C7FCC91.pub>`.  The fingerprint of that key is::

     7604 65DA F652 737A 61EC  0C9D 83F3 3643 2C7F CC91

3. Unpack and change into the source directory.

4. Build (optional)::

     $ python setup.py build

5. Test (optional, see below)::

     $ python setup.py test

6. Install::

     $ python setup.py install

The last step might require admin privileges in order to write into
the site-packages directory of your Python installation.

Building from development sources
.................................

For production use, it is always recommended to use the latest release
version, see above.  If you need some not yet released bleeding edge
feature or if you want to participate in the development, you may also
clone the `source repository from GitHub`__.

Note that some source files are dynamically created and thus missing
in the development sources.  If you want to build from the development
sources, you may use the provided Makefile.  E.g. type ``make build``,
``make test``, and ``make sdist``.

.. __: `GitHub repository`_


Test
----

There is no need to run the tests at all.  The test suite is mostly
useful to the maintainer of python-icat.

Most tests require a test ICAT server to talk to.  These tests are
disabled by default, unless you configure such a test server.  To do
so, place an icat.cfg file into tests/data.  This file must have at
least the configuration sections `root`, `useroffice`, `acord`,
`ahau`, `jbotu`, `jdoe`, `nbour`, and `rbeck` with the options and
credentials to access the test server as the respective user.  See
doc/examples for an example.  Obviously, this implies that your
authentication plugin must also have these users configured.

**WARNING**: the tests are destructive!  They will delete all content
from the test server and replace it with example content.  Do not
configure the tests to access a production server!

You can safely run the tests without configuring any test server.  But
most of the test will be skipped then.


.. _setuptools: https://github.com/pypa/setuptools/
.. _packaging: https://github.com/pypa/packaging/
.. _suds-jurko: https://pypi.org/project/suds-jurko/
.. _suds-community: https://github.com/suds-community/suds/
.. _PyYAML: https://github.com/yaml/pyyaml/
.. _lxml: https://lxml.de/
.. _Requests: https://requests.readthedocs.io/
.. _git-props: https://github.com/RKrahl/git-props/
.. _pytest: https://docs.pytest.org/en/latest/
.. _pytest-dependency: https://pypi.org/project/pytest-dependency/
.. _distutils-pytest: https://github.com/RKrahl/distutils-pytest/
.. _PyPI site: https://pypi.org/project/python-icat/
.. _GitHub latest release: https://github.com/icatproject/python-icat/releases/latest/
.. _GitHub repository: https://github.com/icatproject/python-icat/
.. _Issue #72: https://github.com/icatproject/python-icat/issues/72
