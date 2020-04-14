python-icat --- Python interface to ICAT and IDS
================================================

The `ICAT`_ server is a metadata catalogue to support Large Facility
experimental data, linking all aspects of the research chain from
proposal through to publication.  It provides SOAP and RESTful web
service interfaces to an underlying database.

python-icat is a Python package that provides a collection of modules
for writing programs that access an ICAT service using the SOAP
interface.  It is based on Suds and extends it with ICAT specific
features.

The most important features include:

* Provide clients for ICAT and IDS.
* Keep the general structure and flexibility of Suds.
* Define Python classes to represent the entity object types from the
  ICAT schema.
* Read configuration from various sources, such as command line
  arguments, environment variables, and configuration files.
* Build JPQL expressions to search the ICAT server.
* Dump and restore ICAT content to and from a flat file.  This is
  suitable as a general ingestion tool to ICAT.

.. _ICAT: http://www.icatproject.org/


Parts of the documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   tutorial
   moduleref
   scripts
   changelog


Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`search`

