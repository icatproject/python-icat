:mod:`icat.dumpfile` --- Backend for icatdump and icatingest
============================================================

.. py:module:: icat.dumpfile

This module provides the base classes
:class:`icat.dumpfile.DumpFileReader` and
:class:`icat.dumpfile.DumpFileWriter` that define the API and the
logic for reading and writing :ref:`ICAT-data-files`.  The actual work
is done in file format specific backend modules that should provide
subclasses that must implement the abstract methods.

.. autoclass:: icat.dumpfile.DumpFileReader
    :members:
    :show-inheritance:

.. autoclass:: icat.dumpfile.DumpFileWriter
    :members:
    :show-inheritance:

.. autodata:: icat.dumpfile.Backends

.. autofunction:: icat.dumpfile.register_backend

.. autofunction:: icat.dumpfile.open_dumpfile
