|doi| |rtd| |pypi|

.. |doi| image:: https://zenodo.org/badge/37250056.svg
   :target: https://zenodo.org/badge/latestdoi/37250056

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

The latest release version can be found at the
`release page on GitHub`__.

.. __: `GitHub release`_


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


Copyright and License
---------------------

Copyright 2013–2024
Helmholtz-Zentrum Berlin für Materialien und Energie GmbH

Licensed under the `Apache License`_, Version 2.0 (the "License"); you
may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.


.. _ICAT: https://icatproject.org/
.. _GitHub release: https://github.com/icatproject/python-icat/releases/latest
.. _Read the Docs site: https://python-icat.readthedocs.io/
.. _Apache License: https://www.apache.org/licenses/LICENSE-2.0
