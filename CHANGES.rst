Changelog
=========


.. _changes-1_5_0:

1.5.0 (2024-10-11)
~~~~~~~~~~~~~~~~~~

New features
------------

+ `#160`_, `#161`_, `#163`_: Add class attributes to
  :class:`icat.ingest.IngestReader` to make some prescribed values in
  the transformation to ICAT data file format configurable.

Bug fixes and minor changes
---------------------------

+ `#162`_: Minor updates in the tool chain
+ `#164`_: Fix `dumpinvestigation.py` example script

.. _#160: https://github.com/icatproject/python-icat/issues/160
.. _#161: https://github.com/icatproject/python-icat/pull/161
.. _#162: https://github.com/icatproject/python-icat/pull/162
.. _#163: https://github.com/icatproject/python-icat/pull/163
.. _#164: https://github.com/icatproject/python-icat/pull/164


.. _changes-1_4_0:

1.4.0 (2024-08-30)
~~~~~~~~~~~~~~~~~~

New features
------------

+ `#155`_, `#156`_: Add an option to disable parsing of command line
  arguments in :class:`icat.config.Config`.

Bug fixes and minor changes
---------------------------

+ `#152`_: Fix a documentation error
+ `#154`_: Fix a duplicate test name

Misc
----

+ `#157`_: :mod:`icat.ingest` now considered stable.

.. _#152: https://github.com/icatproject/python-icat/pull/152
.. _#154: https://github.com/icatproject/python-icat/pull/154
.. _#155: https://github.com/icatproject/python-icat/issues/155
.. _#156: https://github.com/icatproject/python-icat/pull/156
.. _#157: https://github.com/icatproject/python-icat/pull/157


.. _changes-1_3_0:

1.3.0 (2024-03-21)
~~~~~~~~~~~~~~~~~~

New features
------------

+ `#143`_, `#144`_: Make it easier to configure XSLT files to use for
  processing the input in custom versions of
  :class:`icat.ingest.IngestReader`.

+ `#148`_, `#149`_: Inject an additional element with environment
  information into the input data in :class:`icat.ingest.IngestReader`.

+ `#146`_, `#147`_, `#151`_: Better error handling in
  :class:`icat.ingest.IngestReader`.

Incompatible changes
--------------------

+ `#144`_: Drop class attribute
  :attr:`icat.ingest.IngestReader.XSLT_name` in favour of
  :attr:`icat.ingest.IngestReader.XSLT_Map`.

  Note that :mod:`icat.ingest` has been declared experimental for now.

Bug fixes and minor changes
---------------------------

+ `#141`_, `#142`_, `#150`_: Review documentation.

+ `#145`_: Review build tool chain.

.. _#141: https://github.com/icatproject/python-icat/issues/141
.. _#142: https://github.com/icatproject/python-icat/pull/142
.. _#143: https://github.com/icatproject/python-icat/issues/143
.. _#144: https://github.com/icatproject/python-icat/pull/144
.. _#145: https://github.com/icatproject/python-icat/pull/145
.. _#146: https://github.com/icatproject/python-icat/issues/146
.. _#147: https://github.com/icatproject/python-icat/pull/147
.. _#148: https://github.com/icatproject/python-icat/issues/148
.. _#149: https://github.com/icatproject/python-icat/pull/149
.. _#150: https://github.com/icatproject/python-icat/pull/150
.. _#151: https://github.com/icatproject/python-icat/pull/151


.. _changes-1_2_0:

1.2.0 (2023-10-31)
~~~~~~~~~~~~~~~~~~

New features
------------

+ `#125`_, `#140`_: Add support to link datasets with samples in
  :mod:`icat.ingest`.

+ `#122`_, `#133`_: Allow referencing related objects by reference key
  in object references in XML ICAT data file format.

Incompatible changes
--------------------

+ `#138`_, `#139`_: Fix the input that :mod:`icat.ingest` generates on
  the fly to be valid according to the ICAT data file schema.  This
  also affects the input that the module accepts: the order of
  subelements of `data` need to be changed such that
  `datasetTechnique` comes before `datasetInstrument`.

  Note that :mod:`icat.ingest` has been declared experimental for now.

Bug fixes and minor changes
---------------------------

+ `#131`_, `#135`_: Fix :meth:`icat.ids.IDSClient.getApiVersion` to
  yield correct results for ids.server 2.0.0 and newer.

+ `#132`_, `#136`_: Fix a spurious :exc:`AttributeError` on cleanup
  after connecting to an invalid url.

+ `#130`_, `#137`_: Review test suite.

.. _#122: https://github.com/icatproject/python-icat/issues/122
.. _#125: https://github.com/icatproject/python-icat/issues/125
.. _#130: https://github.com/icatproject/python-icat/issues/130
.. _#131: https://github.com/icatproject/python-icat/issues/131
.. _#132: https://github.com/icatproject/python-icat/issues/132
.. _#133: https://github.com/icatproject/python-icat/pull/133
.. _#135: https://github.com/icatproject/python-icat/pull/135
.. _#136: https://github.com/icatproject/python-icat/pull/136
.. _#137: https://github.com/icatproject/python-icat/pull/137
.. _#138: https://github.com/icatproject/python-icat/issues/138
.. _#139: https://github.com/icatproject/python-icat/pull/139
.. _#140: https://github.com/icatproject/python-icat/pull/140


.. _changes-1_1_0:

1.1.0 (2023-06-30)
~~~~~~~~~~~~~~~~~~

New features
------------

+ `#113`_, `#123`_: Add module :mod:`icat.ingest`.

+ `#124`_: Add an optional keyword argument `keepInstRel` to
  :meth:`icat.entity.Entity.truncateRelations`.

Bug fixes and minor changes
---------------------------

+ `#126`_, `#127`_: Update outdated documentation.

+ `#112`_, `#118`_: Extend icatdata XSD adding extra attributes to
  reference objects.

+ `#111`_, `#121`_: Change the type of
  :attr:`icat.client.Client.Register` to
  :class:`weakref.WeakValueDictionary`, fixing a memory leak.

+ `#119`_, `#120`_: Remove `_config` attribute from
  :class:`icat.config.Configuration`.

+ `#115`_, `#116`_: Fix the test suite to work if either PyYAML or
  lxml is not available.

+ `#128`_: Return an empty list from
  :func:`icat.dump_queries.getDataPublicationQueries` when talking to
  an ICAT server older than 5.0.

+ `#117`_: Fixed deprecation warnings from upcoming Python 3.12.

+ `#129`_: Review the build of the documentation at Read the Docs.

.. _#111: https://github.com/icatproject/python-icat/issues/111
.. _#112: https://github.com/icatproject/python-icat/issues/112
.. _#113: https://github.com/icatproject/python-icat/issues/113
.. _#115: https://github.com/icatproject/python-icat/issues/115
.. _#116: https://github.com/icatproject/python-icat/pull/116
.. _#117: https://github.com/icatproject/python-icat/pull/117
.. _#118: https://github.com/icatproject/python-icat/pull/118
.. _#119: https://github.com/icatproject/python-icat/issues/119
.. _#120: https://github.com/icatproject/python-icat/pull/120
.. _#121: https://github.com/icatproject/python-icat/pull/121
.. _#123: https://github.com/icatproject/python-icat/pull/123
.. _#124: https://github.com/icatproject/python-icat/pull/124
.. _#126: https://github.com/icatproject/python-icat/issues/126
.. _#127: https://github.com/icatproject/python-icat/pull/127
.. _#128: https://github.com/icatproject/python-icat/pull/128
.. _#129: https://github.com/icatproject/python-icat/pull/129


.. _changes-1_0_0:

1.0.0 (2022-12-21)
~~~~~~~~~~~~~~~~~~

New features
------------

+ `#73`_, `#106`_: Add support for the ICAT schema 5.0 extensions.

+ `#102`_, `#104`_: Make the `obj` argument to
  :meth:`icat.client.Client.new` case insensitive.

+ `#77`_, `#103`_: Add a keyword argument `preset` to allow directly
  passing configuration values to the constructor of class
  :class:`icat.config.Config`.

+ `#66`_, `#75`_: Add pathlib support: methods that take a file name
  argument also accept a :class:`pathlib.Path` object.  Internal
  representation of file system paths are changed to use
  :class:`pathlib.Path` where appropriate.  The predefined
  configuarion variable `configFile` now supports tilde expansion.
  Note incompatible changes below.

+ `#74`_: :class:`icat.ids.DataSelection` also accepts
  `DataCollection` as argument.

Incompatible changes and deprecations
-------------------------------------

+ The order and arrangement of data objects in the dump file created
  by :ref:`icatdump` has been changed.  In some cases, older versions
  of :ref:`icatingest` will fail to read dump files written by new
  versions of :ref:`icatdump`.

+ As a consequence of switching to pathlib for file system paths some
  return values and variables are now :class:`pathlib.Path` objects
  rather then :class:`str`.  This affects:

  - the return value of :func:`icat.config.cfgpath`,
  - the predefined configuarion variable `configFile`,
  - the module variable :data:`icat.config.cfgdirs`.

+ Drop support for Python 2 and Python 3.3.

+ Drop keyword argument `attribute` and method
  :meth:`icat.query.Query.setAttribute` from class
  :class:`icat.query.Query`, deprecated in 0.18.0.

+ Drop module :mod:`icat.cgi`, deprecated in 0.13.0.

+ Drop module :mod:`icat.icatcheck` and exception
  :exc:`icat.exception.GenealogyError`, deprecated in 0.17.0.

+ Drop methods :meth:`icat.ids.IDSClient.resetPrepared`,
  :meth:`icat.ids.IDSClient.getPreparedDatafileIds`,
  :meth:`icat.ids.IDSClient.getPreparedData`,
  :meth:`icat.ids.IDSClient.getPreparedDataUrl`,
  :meth:`icat.client.Client.getPreparedData`, and
  :meth:`icat.client.Client.getPreparedDataUrl`, deprecated in 0.17.0.

+ Drop the predefined configuration variable `configDir`, deprecated
  in 0.13.0.

+ Drop helper function :func:`icat.exception.stripCause`, deprecated
  in 0.14.0.

+ Deprecate :data:`icat.config.defaultsection`.  Use the new `preset`
  keyword argument to :class:`icat.config.Config` instead.

Bug fixes and minor changes
---------------------------

+ `#98`_, `#105`_: Review build tool chain.  Add a helper class
  :class:`icat.helper.Version`.

+ `#101`_: Fix tests failing with PyYAML 6.0.

+ Some (more) example scripts now require ICAT 4.4.0 or newer.

.. _#66: https://github.com/icatproject/python-icat/issues/66
.. _#73: https://github.com/icatproject/python-icat/issues/73
.. _#74: https://github.com/icatproject/python-icat/issues/74
.. _#75: https://github.com/icatproject/python-icat/pull/75
.. _#77: https://github.com/icatproject/python-icat/issues/77
.. _#98: https://github.com/icatproject/python-icat/issues/98
.. _#101: https://github.com/icatproject/python-icat/pull/101
.. _#102: https://github.com/icatproject/python-icat/issues/102
.. _#103: https://github.com/icatproject/python-icat/pull/103
.. _#104: https://github.com/icatproject/python-icat/pull/104
.. _#105: https://github.com/icatproject/python-icat/pull/105
.. _#106: https://github.com/icatproject/python-icat/pull/106


.. _changes-0_21_0:

0.21.0 (2022-01-28)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#100`_: Add read only attributes
  :attr:`icat.query.Query.select_clause`,
  :attr:`icat.query.Query.join_clause`,
  :attr:`icat.query.Query.where_clause`,
  :attr:`icat.query.Query.order_clause`,
  :attr:`icat.query.Query.include_clause`, and
  :attr:`icat.query.Query.limit_clause` to access the respective
  clauses of the query string.

.. _#100: https://github.com/icatproject/python-icat/pull/100


.. _changes-0_20_1:

0.20.1 (2021-11-04)
~~~~~~~~~~~~~~~~~~~

Bug fixes and minor changes
---------------------------

+ `#96`_: Fix failing build of the documentation at Read the Docs.

.. _#96: https://github.com/icatproject/python-icat/pull/96


.. _changes-0_20_0:

0.20.0 (2021-10-29)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#86`_, `#89`_: allow SQL functions to be used on the attributes in
  the arguments to :meth:`icat.query.Query.setOrder` and
  :meth:`icat.query.Query.addConditions`.

Incompatible changes and new bugs
---------------------------------

+ `#94`_: the implementation of `#89`_ changed the internal data
  structures in :attr:`icat.query.Query.conditions` and
  :attr:`icat.query.Query.order`.  These attributes are considered
  internal and are deliberately not documented, so one could argue
  that this is not an incompatible change.  But the changes also have
  an impact on the return value of :meth:`icat.query.Query.__repr__`
  such that it is not suitable to recreate the query object.

Bug fixes and minor changes
---------------------------

+ `#90`_, `#91`_, `#95`_: :attr:`icat.query.Query.join_specs` was not
  taken into account in :meth:`icat.query.Query.copy` and
  :meth:`icat.query.Query.__repr__`.

.. _#86: https://github.com/icatproject/python-icat/issues/86
.. _#89: https://github.com/icatproject/python-icat/pull/89
.. _#90: https://github.com/icatproject/python-icat/issues/90
.. _#91: https://github.com/icatproject/python-icat/issues/91
.. _#94: https://github.com/icatproject/python-icat/issues/94
.. _#95: https://github.com/icatproject/python-icat/pull/95


.. _changes-0_19_0:

0.19.0 (2021-07-20)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#85`_: add an argument `join_specs` to the constructor of class
  :class:`icat.query.Query` and a corresponding method
  :meth:`icat.query.Query.setJoinSpecs` to override the join
  specification to be used in the created query for selected related
  objects.

Bug fixes and minor changes
---------------------------

+ `#83`_, `#84`_: enable ordering on one to many relationships in
  class :class:`icat.query.Query`.

+ `#84`_: Add warning classes
  :exc:`icat.exception.QueryOneToManyOrderWarning` and
  :exc:`icat.exception.QueryWarning`, the latter being a common base
  class for warnings emitted during creation of a query.

.. _#83: https://github.com/icatproject/python-icat/issues/83
.. _#84: https://github.com/icatproject/python-icat/pull/84
.. _#85: https://github.com/icatproject/python-icat/pull/85


.. _changes-0_18_1:

0.18.1 (2021-04-13)
~~~~~~~~~~~~~~~~~~~

Bug fixes and minor changes
---------------------------

+ `#82`_: Change the search result in the case of multiple fields from
  list to tuple.

+ `#76`_, `#81`_: work around an issue in icat.server using `DISTINCT`
  in search queries for multiple fields.

.. _#76: https://github.com/icatproject/python-icat/issues/76
.. _#81: https://github.com/icatproject/python-icat/pull/81
.. _#82: https://github.com/icatproject/python-icat/pull/82


.. _changes-0_18_0:

0.18.0 (2021-03-29)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#76`_, `#78`_: add client side support for searching for multiple
  fields introduced in icat.server 4.11.0.  Add support for building
  the corresponding queries in the in class :class:`icat.query.Query`.

Incompatible changes and deprecations
-------------------------------------

+ Since :class:`icat.query.Query` now also accepts a list of attribute
  names rather then only a single one, the corresponding keyword
  argument `attribute` has been renamed to `attributes` (in the
  plural).  Accordingly, the method
  :meth:`icat.query.Query.setAttribute` has been renamed to
  :meth:`icat.query.Query.setAttributes`.  The old names are retained
  as aliases, but are deprecated.

Bug fixes and minor changes
---------------------------

+ `#79`_: fix an encoding issue in :attr:`icat.client.Client.apiversion`,
  only relevant with Python 2.

+ `#80`_: add :exc:`TypeError` as additional ancestor of
  :exc:`icat.exception.EntityTypeError`.

.. _#76: https://github.com/icatproject/python-icat/issues/76
.. _#78: https://github.com/icatproject/python-icat/pull/78
.. _#79: https://github.com/icatproject/python-icat/pull/79
.. _#80: https://github.com/icatproject/python-icat/pull/80


.. _changes-0_17_0:

0.17.0 (2020-04-30)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#65`_: Add support for the extended IDS API calls
  :meth:`icat.ids.IDSClient.getSize` and
  :meth:`icat.ids.IDSClient.getStatus` accepting a preparedId as
  introduced in ids.server 1.11.0.  Also extend the methods
  :meth:`icat.ids.IDSClient.reset`,
  :meth:`icat.ids.IDSClient.getDatafileIds`,
  :meth:`icat.ids.IDSClient.getData`,
  :meth:`icat.ids.IDSClient.getDataUrl`,
  :meth:`icat.client.Client.getData`, and
  :meth:`icat.client.Client.getDataUrl` to accept a preparedId in the
  place of a data selection.

+ `#63`_: Set a default path in the URL for ICAT and IDS respectively.

Incompatible changes and deprecations
-------------------------------------

+ Drop support for ICAT 4.2.*, deprecated in 0.13.0.

+ `#61`_, `#64`_: Review :mod:`icat.entities`.  The entity classes
  from the ICAT schema are now dynamically created based on the
  information gathered with the
  :meth:`icat.client.Client.getEntityInfo` ICAT API call.  Code that
  relied on the internals of :mod:`icat.entities` such as the class
  hierarchy or that referenced any of the entity classes directly will
  need to be revisited.  Note that common python-icat programs don't
  need to do any of that.  So it is assumed that most existing
  programs are not concerned.

+ Deprecate :meth:`icat.ids.IDSClient.resetPrepared`,
  :meth:`icat.ids.IDSClient.getPreparedDatafileIds`,
  :meth:`icat.ids.IDSClient.getPreparedData`,
  :meth:`icat.ids.IDSClient.getPreparedDataUrl`,
  :meth:`icat.client.Client.getPreparedData`, and
  :meth:`icat.client.Client.getPreparedDataUrl`.  Call the
  corresponding methods without `Prepared` in the name with the same
  arguments instead.

+ Deprecate support for Python 2 and Python 3.3.

+ Deprecate module :mod:`icat.icatcheck`.
  This module was not intended to be used in python-icat programs
  anyway.

Bug fixes and minor changes
---------------------------

+ `#68`_: :ref:`wipeicat` enters an infinite loop if Datafiles are
  missing from IDS storage.

+ `#19`_, `#69`_: Review documentation and add tutorial.

+ `#62`_: Minor fixes in the error handling in `setup.py`.

+ Fix icatdata-4.10.xsd: :attr:`Study.endDate` was erroneously not
  marked as optional.

+ `#70`_: Fix several errors in the tests.

+ `#58`_: Use specific test data for different ICAT versions.

+ `#67`_, `#71`_, `#72`_: document the option to use suds-community
  instead of suds-jurko.

Misc
----

+ Do not include the documentation in the source distribution.  Rely
  on the online documentation (see link in the README.rst) instead.

.. _#19: https://github.com/icatproject/python-icat/issues/19
.. _#58: https://github.com/icatproject/python-icat/issues/58
.. _#61: https://github.com/icatproject/python-icat/issues/61
.. _#62: https://github.com/icatproject/python-icat/issues/62
.. _#63: https://github.com/icatproject/python-icat/issues/63
.. _#64: https://github.com/icatproject/python-icat/pull/64
.. _#65: https://github.com/icatproject/python-icat/pull/65
.. _#67: https://github.com/icatproject/python-icat/issues/67
.. _#68: https://github.com/icatproject/python-icat/issues/68
.. _#69: https://github.com/icatproject/python-icat/pull/69
.. _#70: https://github.com/icatproject/python-icat/pull/70
.. _#71: https://github.com/icatproject/python-icat/pull/71
.. _#72: https://github.com/icatproject/python-icat/issues/72


.. _changes-0_16_0:

0.16.0 (2019-09-26)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#59`_: Add support for sub-commands in :mod:`icat.config`.

Incompatible changes and deprecations
-------------------------------------

+ Drop support for Python 2.6.

Bug fixes and minor changes
---------------------------

+ `#60`_: Fix bad coding style dealing with function parameters.

+ Use :mod:`setuptools_scm` to manage the version number.

.. _#59: https://github.com/icatproject/python-icat/issues/59
.. _#60: https://github.com/icatproject/python-icat/pull/60


.. _changes-0_15_1:

0.15.1 (2019-07-12)
~~~~~~~~~~~~~~~~~~~

Bug fixes and minor changes
---------------------------

+ Issue `#56`_: :ref:`icatdump` fails to include
  :attr:`Shift.instrument`.

+ Issue `#57`_: :meth:`icat.client.Client.searchChunked` still
  susceptible to LIMIT clause bug in icat.server (`Issue
  icatproject/icat.server#128`__).

+ Call :func:`yaml.safe_load` rather then :func:`yaml.load`, fixing a
  deprecation warning from PyYAML 5.1.

.. __: https://github.com/icatproject/icat.server/issues/128
.. _#56: https://github.com/icatproject/python-icat/issues/56
.. _#57: https://github.com/icatproject/python-icat/issues/57


.. _changes-0_15_0:

0.15.0 (2019-03-27)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#53`_: Add support for ICAT 4.10.0 including schema changes in that
  version.

Incompatible changes and deprecations
-------------------------------------

+ Require pytest 3.1.0 or newer to run the test suite.  Note that this
  pytest version in turn requires Python 2.6, 2.7, or 3.3 and newer.

+ Drop support for Python 3.1 and 3.2.  There is no known issue with
  these Python versions in python-icat (so far).  But since we can't
  test this any more, see above, we drop the claim to support them.

Bug fixes and minor changes
---------------------------

+ `#49`_: Module icat.eval is outdated.

+ `#50`_, `#52`_: Fix DeprecationWarnings.

+ `#51`_: Fix a compatibility issue with pytest 4.1.0 in the tests.

+ `#54`_: Fix a UnicodeDecodeError in the tests.

.. _#49: https://github.com/icatproject/python-icat/issues/49
.. _#50: https://github.com/icatproject/python-icat/issues/50
.. _#51: https://github.com/icatproject/python-icat/issues/51
.. _#52: https://github.com/icatproject/python-icat/issues/52
.. _#53: https://github.com/icatproject/python-icat/pull/53
.. _#54: https://github.com/icatproject/python-icat/issues/54


.. _changes-0_14_2:

0.14.2 (2018-10-25)
~~~~~~~~~~~~~~~~~~~

Bug fixes and minor changes
---------------------------

+ Add a hook to control internal diverting of :attr:`sys.err` in the
  :mod:`icat.config` module.  This is intentionally not documented as
  it goes deeply into the internals of this module and most users will
  probably not need it.


.. _changes-0_14_1:

0.14.1 (2018-06-05)
~~~~~~~~~~~~~~~~~~~

Bug fixes and minor changes
---------------------------

+ Fix a misleading error message if the IDS server returns an error
  for the Write API call.


.. _changes-0_14_0:

0.14.0 (2018-06-01)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#45`_: Add support for the IDS Write API call introduced in
  ids.server 1.9.0.

+ `#46`_, `#47`_: Add a :meth:`ìcat.client.Client.autoRefresh` method.
  The scripts :ref:`icatdump` and :ref:`icatingest` call this method
  periodically to prevent the session from expiring.

+ `#48`_: Add support for an ordering direction qualifier in class
  :class:`icat.query.Query`.

+ `#44`_: Add method :meth:`icat.entity.Entity.as_dict`.

+ `#40`_: Add method :meth:`icat.client.Client.clone`.

Incompatible changes and deprecations
-------------------------------------

+ Deprecate function :func:`icat.exception.stripCause`.

  This was an internal helper function not really meant to be part of
  the API.  The functionality has been moved in a base class of the
  exception hierarchy.

Bug fixes and minor changes
---------------------------

+ Add the :meth:`icat.ids.IDSClient.version` API call introduced in
  ids.server 1.8.0.

+ `#41`_: Incomprehensible error messages with Python 3.

+ `#43`_: :meth:`icat.client.Client.logout` should silently ignore
  :exc:`icat.exception.ICATSessionError`.

+ Minor changes in the error handling.  Add new exception
  :exc:`icat.exception.EntityTypeError`.

+ Documentation fixes.

.. _#40: https://github.com/icatproject/python-icat/issues/40
.. _#41: https://github.com/icatproject/python-icat/issues/41
.. _#43: https://github.com/icatproject/python-icat/issues/43
.. _#44: https://github.com/icatproject/python-icat/pull/44
.. _#45: https://github.com/icatproject/python-icat/pull/45
.. _#46: https://github.com/icatproject/python-icat/issues/46
.. _#47: https://github.com/icatproject/python-icat/pull/47
.. _#48: https://github.com/icatproject/python-icat/issues/48


.. _changes-0_13_1:

0.13.1 (2017-07-12)
~~~~~~~~~~~~~~~~~~~

Bug fixes and minor changes
---------------------------

+ `#38`_: There should be a way to access the kwargs used to create
  the client in config.

.. _#38: https://github.com/icatproject/python-icat/issues/38


.. _changes-0_13_0:

0.13.0 (2017-06-09)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#11`_: Support discovery of info about available ICAT
  authenticators.

  If supported by the ICAT server (icat.server 4.9.0 and newer), the
  :mod:`icat.config` module queries the server for information on
  available authenticators and the credential keys they require for
  login.  The configuration variables for these keys are then adapted
  accordingly.  Note incompatible changes below.

+ Review :ref:`wipeicat`.  This was an example script, but is now
  promoted to be a regular utility script that gets installed.

+ `#32`_: Add support for using aggregate functions in class
  :class:`icat.query.Query`.

+ `#30`_: Add a predefined config variable type
  :func:`icat.config.cfgpath`.

+ `#31`_: Add a flag to add the default variables to the
  :class:`icat.config.Config` constructor (default: True).

+ :class:`icat.dumpfile_xml.XMLDumpFileReader` also accepts a XML tree
  object as input.

+ Verify support for ICAT 4.9.0.  Add new ICAT API method
  :meth:`icat.client.Client.getVersion`.

Incompatible changes and deprecations
-------------------------------------

+ As a consequence of the discovery of available authenticators, the
  workflow during configuration need to be changed.  Until now, the
  beginning of a typical python-icat program would look like::

        config = icat.config.Config()
        # Optionally, add custom configuration variables:
        # config.add_variable(...)
        conf = config.getconfig()
        client = icat.Client(conf.url, **conf.client_kwargs)

  E.g. first the configuration variables are set up, then the
  configuration is applied and finally the :class:`icat.client.Client`
  object is created using the configuration values.  With the
  discovery of authenticators, the :class:`icat.config.Config` object
  itself needs a working :class:`icat.client.Client` object in order
  to connect to the ICAT server and query the authenticator info.  The
  :class:`icat.client.Client` object will now be created in the
  :class:`icat.config.Config` constructor and returned along with the
  configuration values by :meth:`icat.config.Config.getconfig`.  You
  will need to replace the code from above by::

        config = icat.config.Config()
        # Optionally, add custom configuration variables:
        # config.add_variable(...)
        client, conf = config.getconfig()

  The derived configuration variable `client_kwargs` that was used to
  pass additional arguments from the configuration to the Client
  constructor is no longer needed and has been removed.

  The optional argument `args` has been moved from the
  :meth:`icat.config.Config.getconfig` call to the
  :class:`icat.config.Config` constructor, retaining the same
  semantics.  E.g. you must change in your code::

        config = icat.config.Config()
        conf = config.getconfig(args)
        client = icat.Client(conf.url, **conf.client_kwargs)

  to::

        config = icat.config.Config(args)
        client, conf = config.getconfig()

+ Deprecate support for ICAT 4.2.*.

  Note that already now significant parts of python-icat require
  features from ICAT 4.3 such as the JPQL like query language.  The
  only workaround is to upgrade your icat.server.

+ Deprecate module :mod:`icat.cgi`.

  It is assumed that this has never actually been used in production.
  For web applications it is recommended to use the Python Web Server
  Gateway Interface (WSGI) rather then CGI.

+ Deprecate the predefined configuration variable `configDir`.

  The main use case for this variable was to be substituted in the
  default value for the path of an additional configuration file.  The
  typical usage was the definition of a configuration variable like::

        config = icat.config.Config()
        config.add_variable('extracfg', ("--extracfg",),
                            dict(help="Extra config file"),
                            default="%(configDir)s/extra.xml", subst=True)

  This set the default path for the extra config file to the same
  directory the main configuration file was found in.  Using the new
  config variable type :func:`icat.config.cfgpath` you can replace
  this by::

        config = icat.config.Config()
        config.add_variable('extracfg', ("--extracfg",),
                            dict(help="Extra config file"),
                            default="extra.xml", type=icat.config.cfgpath)

  This will search the extra config file in all the default config
  directories, regardless where the main configuration file was found.

+ The fixes for `#35`_ and `#36`_ require some changes in the
  semantics in the `f` and the `mode` argument to
  :func:`icat.dumpfile.open_dumpfile`.  Most users will probably not
  notice the difference.

Bug fixes and minor changes
---------------------------

+ Changed the default for the :class:`icat.config.Config` constructor
  argument `ids` from :const:`False` to ``"optional"``.

+ Improved :meth:`icat.client.Client.searchChunked`.  This version is
  not susceptible to `Issue icatproject/icat.server#128`__ anymore.

+ Move the management of dependencies of tests into a separate package
  `pytest-dependency`_ that is distributed independently.

+ `#34`_: :exc:`TypeError` in the :class:`icat.client.Client`
  constructor if setting the `sslContext` keyword argument.

+ `#35`_: :exc:`io.UnsupportedOperation` is raised if
  :func:`icat.dumpfile.open_dumpfile` is called with an in-memory
  stream.

+ `#36`_: :class:`icat.dumpfile.DumpFileReader` and
  :class:`icat.dumpfile.DumpFileWriter` must not close file.

+ `#37`_: :exc:`TypeError` is raised when writing a YAML dumpfile to
  :class:`io.StringIO`.

.. __: https://github.com/icatproject/icat.server/issues/128
.. _#11: https://github.com/icatproject/python-icat/issues/11
.. _#30: https://github.com/icatproject/python-icat/issues/30
.. _#31: https://github.com/icatproject/python-icat/issues/31
.. _#32: https://github.com/icatproject/python-icat/issues/32
.. _#34: https://github.com/icatproject/python-icat/issues/34
.. _#35: https://github.com/icatproject/python-icat/issues/35
.. _#36: https://github.com/icatproject/python-icat/issues/36
.. _#37: https://github.com/icatproject/python-icat/issues/37
.. _pytest-dependency: https://pypi.python.org/pypi/pytest_dependency/


.. _changes-0_12_0:

0.12.0 (2016-10-10)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ Verify support for ICAT 4.8.0 and IDS 1.7.0.

+ Add methods :meth:`icat.ids.IDSClient.reset` and
  :meth:`icat.ids.IDSClient.resetPrepared`.

+ `#28`_: Add support for searching for attributes in class
  :class:`icat.query.Query`.

Bug fixes and minor changes
---------------------------

+ Sort objects in :ref:`icatdump` before writing them to the dump file.
  This keeps the order independent from the collation used in the ICAT
  database backend.

+ `#2`_: for Python 3.6 (expected to be released in Dec 2016) and
  newer, use the support for chunked transfer encoding in the standard
  lib.  Keep our own implementation in module :mod:`icat.chunkedhttp`
  only for compatibility with older Python versions.

+ Improved the example script :ref:`wipeicat`.

+ Add an example script `dumprules.py`.

+ Add missing schema definition for the ICAT XML data file format for
  ICAT 4.7.

+ Fix an :exc:`AttributeError` during error handling.

.. _#2: https://github.com/icatproject/python-icat/issues/2
.. _#28: https://github.com/icatproject/python-icat/issues/28


.. _changes-0_11_0:

0.11.0 (2016-06-01)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ `#12`_, `#23`_: add support for ICAT 4.7.0 and IDS 1.6.0.  ICAT
  4.7.0 had some small schema changes that have been taken into
  account.

Incompatible changes
--------------------

+ Remove the `autoget` argument from
  :meth:`icat.entity.Entity.getUniqueKey`.  Deprecated since 0.9.0.

Bug fixes and minor changes
---------------------------

+ `#21`_: configuration variable `promptPass` is ignored when set in
  the configuration file.

+ `#18`_: Documentation: missing stuff in the module index.

+ `#20`_: add test on compatibility with icat.server.

+ `#24`_, `#25`_: test failures caused by different timezone settings
  of the test server.

+ Use a separate module `distutils_pytest`_ to run the tests from
  `setup.py`.

+ :mod:`icat.icatcheck`: move checking of exceptions into a separate
  method :meth:`icat.icatcheck.ICATChecker.checkExceptions`.  Do not
  report exceptions defined in the client, but not found in the
  schema.

+ Many fixes in the example script :ref:`wipeicat`.

+ Fix a missing import in the `icatexport.py` example script.

+ Somewhat clearer error messages for some special cases of
  :exc:`icat.exception.SearchAssertionError`.

Misc
----

+ Change license to Apache 2.0.

.. _#12: https://github.com/icatproject/python-icat/issues/12
.. _#18: https://github.com/icatproject/python-icat/issues/18
.. _#20: https://github.com/icatproject/python-icat/issues/20
.. _#21: https://github.com/icatproject/python-icat/issues/21
.. _#23: https://github.com/icatproject/python-icat/issues/23
.. _#24: https://github.com/icatproject/python-icat/issues/24
.. _#25: https://github.com/icatproject/python-icat/issues/25
.. _distutils_pytest: https://github.com/RKrahl/distutils-pytest


.. _changes-0_10_0:

0.10.0 (2015-12-06)
~~~~~~~~~~~~~~~~~~~

New features
------------

+ Add a method :meth:`icat.entity.Entity.copy`.

+ Implement setting an INCLUDE 1 clause equivalent in class
  :class:`icat.query.Query`.

+ Add an optional argument `includes` to
  :meth:`icat.client.Client.searchMatching`.

+ Add a hook for a custom method to validate entity objects before
  creating them at the ICAT server.

+ Add support for ids.server 1.5.0:

  - Add :meth:`icat.ids.IDSClient.getDatafileIds` and
    :meth:`icat.ids.IDSClient.getPreparedDatafileIds` calls.

  - :meth:`icat.ids.IDSClient.getStatus` allows `sessionId` to be
    None.

+ Add new exception class
  :exc:`icat.exception.ICATNotImplementedError` that is supposed to be
  raised by the upcoming version 4.6.0 of icat.server.

Bug fixes and minor changes
---------------------------

+ `#13`_: :meth:`icat.client.Client.searchChunked` raises exception if
  the query contains a percent character.

+ `#15`_: :ref:`icatdump` raises
  :exc:`icat.exception.DataConsistencyError` for
  `DataCollectionParameter`.

+ `#14`_: :meth:`icat.entity.Entity.__sortkey__` may raise
  :exc:`RuntimeError` "maximum recursion depth exceeded".

+ Allow a :class:`icat.ids.DataSelection` to be created from (almost)
  any Iterator, not just a :class:`Sequence`.  Store the object ids in
  :class:`icat.ids.DataSelection` internally in a :class:`set` rather
  then a :class:`list`.

+ Add optional arguments `objindex` to
  :meth:`icat.dumpfile.DumpFileReader.getobjs` and `keyindex` to
  :meth:`icat.dumpfile.DumpFileWriter.writedata` to allow the caller
  to control these internal indices.

+ Add optional argument `chunksize` to
  :meth:`icat.dumpfile.DumpFileWriter.writedata`.

+ The constructor of class :class:`icat.query.Query` checks the
  version of the ICAT server and raises an error if too old.

+ The :meth:`icat.ids.IDSClient.getIcatUrl` call checks the version of
  the IDS server.

+ Some changes in the test suite, add more tests.

.. _#13: https://github.com/icatproject/python-icat/issues/13
.. _#14: https://github.com/icatproject/python-icat/issues/14
.. _#15: https://github.com/icatproject/python-icat/issues/15


.. _changes-0_9_0:

0.9.0 (2015-08-13)
~~~~~~~~~~~~~~~~~~

New features
------------

+ `#4`_: Extend :ref:`icatrestore <icatingest>` to become a generic
  ingestion tool.

  Rename :ref:`icatrestore <icatingest>` to :ref:`icatingest`.

  Allow referencing of objects by attribute rather then by unique key
  in the input file for :ref:`icatingest` (only in the XML backend).

  Allow adding references to already existing objects in the input
  file for :ref:`icatingest` (only in the XML backend).

  Change the name of the root element in the input file for
  :ref:`icatingest` (and the output of :ref:`icatdump`) from
  `icatdump` to `icatdata` (only in the XML backend).

+ Implement upload of Datafiles to IDS rather then only creating the
  ICAT object from :ref:`icatingest`.

+ Implement handling of duplicates in :ref:`icatingest`.  The same
  options (`THROW`, `IGNORE`, `CHECK`, and `OVERWRITE`) as in the
  import call in the ICAT restful interface are supported.

+ `#1`_: add a test suite.

+ `#3`_: use Sphinx to generate the API documentation.

+ Add method :meth:`icat.client.Client.searchMatching`.

+ Add the :meth:`icat.ids.IDSClient.getIcatUrl` call introduced with
  IDS 1.4.0.

Incompatible changes and deprecations
-------------------------------------

+ The Lucene calls that have been removed in ICAT 4.5.0 are also
  removed from the client.

+ Deprecate the use of the `autoget` argument in
  :meth:`icat.entity.Entity.getUniqueKey`.

Bug fixes and minor changes
---------------------------

+ `#6`_: :class:`icat.query.Query`: adding a condition on a meta
  attribute fails.

+ `#10`_: client.putData: IDSInternalError is raised if
  datafile.datafileCreateTime is set.

+ Ignore import errors from the backend modules in :ref:`icatingest` and
  :ref:`icatdump`.  This means one can use the scripts also if the
  prerequisites for some backends are not fulfilled, only the
  concerned backends are not available then.

+ `#5`_, compatibility with ICAT 4.5: entity ids are not guaranteed to
  be unique among all entities, but only for entities of the same
  type.

+ `#5`_, compatibility with ICAT 4.5:
  :meth:`icat.client.Client.getEntityInfo` also lists `createId`,
  `createTime`, `modId`, and `modTime` as attributes.  This need to be
  taken into account in :mod:`icat.icatcheck`.

+ The last fix in 0.8.0 on the string representation operator
  :meth:`icat.query.Query.__str__` was not complete, the operator
  still had unwanted side effects.

+ Fix a bug in the handling of errors raised from the ICAT or the IDS
  server.  This bug affected only Python 3.

+ Add proper type checking and conversion for setting an attribute
  that corresponds to a one to many relationship in class
  :class:`icat.entity.Entity`.  Accept any iterable of entities as
  value.

+ `#9`_: :ref:`icatingest` with `duplicate=CHECK` may fail when
  attributes are not strings.  Note that this bug was only present in
  an alpha version, but not in any earlier release version.

+ Source repository moved to Git.  This gives rise to a few tiny
  changes.  To name the most visible ones: python2_6.patch is now auto
  generated by comparing two source branches and must be applied with
  `-p1` instead of `-p0`, the format of the icat module variable
  :attr:`icat.__revision__` has changed.

+ Review default exports of modules.  Mark some helper functions as
  internal.

.. _#1: https://github.com/icatproject/python-icat/issues/1
.. _#3: https://github.com/icatproject/python-icat/issues/3
.. _#4: https://github.com/icatproject/python-icat/issues/4
.. _#5: https://github.com/icatproject/python-icat/issues/5
.. _#6: https://github.com/icatproject/python-icat/issues/6
.. _#9: https://github.com/icatproject/python-icat/issues/9
.. _#10: https://github.com/icatproject/python-icat/issues/10


.. _changes-0_8_0:

0.8.0 (2015-05-08)
~~~~~~~~~~~~~~~~~~

New features
------------

+ Enable verification of the SSL server certificate in HTTPS
  connections.  Add a new configuration variable `checkCert` to
  control this.  It is set to :const:`True` by default.

  Note that this requires either Python 2.7.9 or 3.2 or newer.  With
  older Python version, this configuration option has no effect.

+ Add type conversion of configuration variables.

+ Add substituting the values of configuration variables in other
  variables.

+ Add another derived configuration variable `configDir`.

+ Default search path for the configuration file: add an appropriate
  path on Windows, add ``/etc/icat`` and ``~/.config/icat`` to the
  path if not on Windows.

+ Add `icatexport.py` and `icatimport.py` example scripts that use the
  corresponding calls to the ICAT RESTful interface to dump and
  restore the ICAT content.

+ The constructor of :exc:`icat.exception.ICATError` and the
  :func:`icat.exception.translateError` function are now able to
  construct exceptions based on a dict such as those returned by the
  ICAT RESTful interface in case of an error.

  Unified handling of errors raised from the ICAT and the IDS server.

Incompatible changes
--------------------

+ As a consequence of the unified handling of errors, the exception
  class hierarchy has been reviewed, with a somewhat more clear
  separation of exceptions raised by other libraries, exceptions
  raised by the server, and exceptions raised by python-icat
  respectively.

  If you put assumptions on the exception hierarchy in your code, this
  might need a review.  In particular,
  :exc:`icat.exception.IDSResponseError` is not derived from
  :exc:`icat.exception.IDSError` any more.
  :exc:`icat.exception.IDSServerError` has been removed.

  I.e., replace all references to :exc:`icat.exception.IDSServerError`
  by :exc:`icat.exception.IDSError` in your code.  Furthermore, if you
  catch :exc:`icat.exception.IDSError` in your code with the intention
  to catch both, errors from the IDS server and
  :exc:`icat.exception.IDSResponseError` in one branch, replace::

    try:
        # ...
    except IDSError:
        # ...

  by ::

    try:
        # ...
    except (IDSError, IDSResponseError):
        # ...

Bug fixes and minor changes
---------------------------

+ The :class:`icat.query.Query` class now checks the attributes
  referenced in conditions and includes for validity.

+ Fix a regression introduced with version 0.7.0 that caused non-ASCII
  characters in queries not to work.

+ Fix :exc:`icat.exception.ICATError` and
  :exc:`icat.exception.IDSError` to gracefully deal with non-ASCII
  characters in error messages.  Add a common abstract base class
  :exc:`icat.exception.ICATException` that cares about this.

+ Fix: the string representation operator
  :meth:`icat.query.Query.__str__` should not modify the query object.

+ Cosmetic improvement in the formal representation operator
  :meth:`icat.query.Query.__repr__`.


.. _changes-0_7_0:

0.7.0 (2015-02-11)
~~~~~~~~~~~~~~~~~~

New features
------------

+ Add a module :mod:`icat.query` with a class
  :class:`icat.query.Query` that can be used to build ICAT search
  expressions.  Instances of the class may be used in place of search
  expression strings where appropriate.

  Numerous examples on how to use this new class can be found in
  `querytest.py` in the examples.

+ Add a class method :meth:`icat.entity.Entity.getNaturalOrder` that
  returns a list of attributes suitable to be used in an ORDER BY
  clause in an ICAT search expression.

+ Add a class method :meth:`icat.entity.Entity.getAttrInfo` that
  queries the EntityInfo from the ICAT server and extracts the
  information on an attribute.

+ Add a method :meth:`icat.client.Client.getEntityClass` that returns
  the :class:`icat.entity.Entity` subclass corresponding to a name.

+ Add a warning class :exc:`icat.exception.QueryNullableOrderWarning`.

+ Add an optional argument `username` to the
  :meth:`icat.ids.IDSClient.getLink` method.


.. _changes-0_6_0:

0.6.0 (2014-12-15)
~~~~~~~~~~~~~~~~~~

New features
------------

+ Add support for ICAT 4.4.0: add new :class:`icat.entity.Entity` type
  `InvestigationGroup`, `role` has been added to the constraint in
  `InvestigationUser`.

+ Add new API method :meth:`icat.ids.IDSClient.getApiVersion` that
  will be introduced with the upcoming version 1.3.0 of IDS.  This
  method may also be called with older IDS servers: if it is not
  available because the server does not support it yet, the server
  version is guessed from visible features in the API.

  :class:`icat.ids.IDSClient` checks the API version on init.

+ Add new API methods :meth:`icat.ids.IDSClient.isReadOnly`,
  :meth:`icat.ids.IDSClient.isTwoLevel`,
  :meth:`icat.ids.IDSClient.getLink`, and
  :meth:`icat.ids.IDSClient.getSize` introduced with IDS 1.2.0.

+ Add `no_proxy` support.  The proxy configuration variables,
  `http_proxy`, `https_proxy`, and `no_proxy` are set in the
  environment.  [Suggested by Alistair Mills]

+ Rework the dump file backend API for :ref:`icatdump` and
  :ref:`icatrestore <icatingest>`.  As a result, writing custom dump
  or restore scripts is much cleaner and easier now.

  This may cause compatibility issues for users who either wrote their
  own dump file backend or for users who wrote custom dump or restore
  scripts, using the XML or YAML backends.  In the first case, compare
  the old XML and YAML backends with the new versions and you'll
  easily see what needs to get adapted.  In the latter case, have a
  look into the new versions of :ref:`icatdump` and :ref:`icatrestore
  <icatingest>` to see how to use the new backend API.

+ Add method :meth:`icat.client.Client.searchChunked`.

+ Add method :meth:`icat.entity.Entity.getAttrType`.

Incompatible changes
--------------------

+ Move the `group` argument to method
  :meth:`icat.client.Client.createRules` to the last position and make
  it optional, having default :const:`None`.

  In the client code, replace::

    client.createRules(group, crudFlags, what)

  by ::

    client.createRules(crudFlags, what, group)

+ The :meth:`icat.client.Client.putData` method returns the new
  Datafile object created by IDS rather then only its id.

  If you depend on the old behavior in the client code, replace::

    dfid = client.putData(file, datafile)

  by ::

    df = client.putData(file, datafile)
    dfid = df.id

Minor changes and fixes
-----------------------

+ The :meth:`icat.client.Client.searchText` and
  :meth:`icat.client.Client.luceneSearch` client method have been
  deprecated.  They are destined to be dropped from the ICAT server or
  at least changed in version 4.5.0 and might get removed from
  python-icat in a future release as well.

  The methods now emit a deprecation warning when called.  Note
  however that Python by default ignores deprecation warnings, so you
  won't see this unless you switch them on.

+ Fixed overly strict type checking in the constructor arguments of
  :class:`icat.ids.DataSelection` and as a consequence also in the
  arguments of the ICAT client methods
  :meth:`icat.client.Client.getData`,
  :meth:`icat.client.Client.getDataUrl`,
  :meth:`icat.client.Client.prepareData`, and
  :meth:`icat.client.Client.deleteData`: now, any
  :class:`Sequence` of entity objects will be accepted, in particular
  an :class:`icat.entity.EntityList`.

+ Change :meth:`icat.ids.IDSClient.archive` and
  :meth:`icat.ids.IDSClient.restore` to not to return anything.  While
  formally, this might be considered an incompatible change, these
  methods never returned anything meaningful in the past.

+ Slightly modified the `==` and `!=` operator for
  :class:`icat.entity.Entity`.  Add a
  :meth:`icat.entity.Entity.__hash__` method.  The latter means that
  you will more likely get what you expect when you create a set of
  :class:`icat.entity.Entity` objects or use them as keys in a dict.

+ The module :mod:`icat.eval` now only does its work (parsing command
  line arguments and connecting to an ICAT server) when called from
  the Python command line.  When imported as a regular module, it will
  essentially do nothing.  This avoids errors to occur when imported.

+ `setup.py` raises an error with Python 2.6 if python2_6.patch has
  not been applied.

+ Add missing `MANIFEST.in` in the source distribution.

+ Remove the work around the Suds datetime value bug (setting the
  environment variable TZ to ``UTC``) from :mod:`icat`.  Instead,
  document it along with other known issues in the README.

+ Minor fixes in the sorting of entity objects.

+ Add an optional argument args to
  :meth:`icat.config.Config.getconfig`.  If set to a list of strings,
  it replaces :attr:`sys.argv`.  Mainly useful for testing.

+ Add comparison operators to class :class:`icat.listproxy.ListProxy`.


.. _changes-0_5_1:

0.5.1 (2014-07-07)
~~~~~~~~~~~~~~~~~~

+ Add a module :mod:`icat.eval` that is intended to be run using the
  ``-m`` command line switch to Python.  It allows to evaluate Python
  expressions within an ICAT session as one liners directly from the
  command line, as for example::

    # get all Dataset ids
    $ python -m icat.eval -e 'client.search("Dataset.id")' -s root
    [102284L, 102288L, 102289L, 102293L]

+ Fix an issue in the error handling in the IDS client that caused an
  :exc:`urllib2.HTTPError` to be raised instead of an
  :exc:`icat.exception.IDSServerError` in the case of an error from
  the IDS server and thus the loss of all details about the error
  reported in the reply from the server.

+ Add specific exception classes for the different error codes raised
  by the IDS server.

+ Fix compatibility issue with Python 3.3 that caused the HTTP method
  to be set to :const:`None` in some IDS methods, which in turn caused
  an internal server error to be raised in the IDS server.

+ Fix compatibility issues with Python 3.4: some methods have been
  removed from class :class:`urllib.request.Request` which caused an
  :exc:`AttributeError` in the :class:`icat.ids.IDSClient`.

+ Fix: failed to connect to an ICAT server if it advertises a version
  number having a trailing "-SNAPSHOT" in
  :meth:`icat.client.Client.getApiVersion`.  For compatibility, a
  trailing "-SNAPSHOT" will be replaced by "a1" in the
  client.apiversion attribute.

+ Suppress misleading context information introduced with Python 3
  (PEP 3134) from the traceback in some error messages.
  Unfortunately, the fix only works for Python 3.3 and newer.

+ Make example files compatible across Python versions without
  modifications, such as running 2to3 on them.


.. _changes-0_5_0:

0.5.0 (2014-06-24)
~~~~~~~~~~~~~~~~~~

+ Integrate an IDS client in the ICAT client.

+ Improved :ref:`icatdump` and :ref:`icatrestore <icatingest>`:

  - Changed the logical structure of the dump file format which
    significantly simplified the scripts.  Note that old dump files
    are not compatible with the new versions.

  - Add support for XML dump files.  A XML Schema Definition for the
    dump file format is provided in the doc directory.

  The scripts are now considered to be legitimate tools (though still
  alpha) rather then mere examples.  Consequently, they will be
  installed into the bin directory.

+ Implicitly set a one to many relation to an empty list if it is
  accessed but not present in an :class:`icat.entity.Entity` object
  rather then raising an :exc:`AttributeError`.  See `ICAT Issue
  112`__.

+ Allow setting one to many relationship attributes and deletion of
  attributes in :class:`icat.entity.Entity`.  Add method
  :meth:`icat.entity.Entity.truncateRelations`.  Truncate dummy
  relations set by the factory in newly created entity objects.

+ Cache the result from :meth:`icat.client.Client.getEntityInfo` in
  the client.

+ Add a method :meth:`icat.entity.Entity.__sortkey__` that return a
  key that when used as a sorting key in :meth:`list.sort` allows any
  list of entity objects to have a well defined order.  Sorting is
  based on the Constraint attributes.  Add a class variable
  :attr:`icat.entity.Entity.SortAttrs` that overrides this and will be
  set as a fall back for those entity classes that do not have a
  suitable Constraint.

.. __: https://github.com/icatproject/icat.server/issues/112


.. _changes-0_4_0:

0.4.0 (2014-02-11)
~~~~~~~~~~~~~~~~~~

+ Add support for the jurko fork of Suds and for Python 3.

+ Add a new method :meth:`icat.client.Client.searchUniqueKey`.

+ Add an optional argument `keyindex` to method
  :meth:`icat.entity.Entity.getUniqueKey` that is used as a cache of
  previously generated keys.  Remove the argument `addbean`.  It had
  been documented as for internal use only, so this is not considered
  an incompatible change.

+ Add a new exception :exc:`icat.exception.DataConsistencyError`.
  Raise this in :meth:`icat.entity.Entity.getUniqueKey` if a relation
  that is required in a constraint is not set.

+ Rename :exc:`icat.exception.SearchResultError` to
  :exc:`icat.exception.SearchAssertionError`.  SearchResultError was a
  misnomer here, as this exception class is very specific to
  :meth:`icat.client.Client.assertedSearch`.  Add a new generic
  exception class :exc:`icat.exception.SearchResultError` and derive
  :exc:`icat.exception.SearchAssertionError` from it.  This way, the
  change should not create any compatibility problems in client
  programs.

+ Add a check in :mod:`icat.icatcheck` that the
  :exc:`icat.exception.ICATError` subclasses are in sync with
  `icatExceptionType` as defined in the schema.

+ Bugfix: The code dealing with exceptions raised by the ICAT server
  did require all attributes in IcatException sent by the server to be
  set, although some of these attributes are marked as optional in the
  schema.

+ Do not delete the Suds cache directory in
  :meth:`icat.client.Client.cleanup`.

+ Installation: python-icat requires Python 2.6 or newer.  Raise an
  error if `setup.py` is run by a too old Python version.

+ Move some internal routines in a separate module :mod:`icat.helper`.

+ Greatly improved example scripts :ref:`icatdump` and
  :ref:`icatrestore <icatingest>`.


.. _changes-0_3_0:

0.3.0 (2014-01-10)
~~~~~~~~~~~~~~~~~~

+ Add support for ICAT 4.3.1.  (Compatibility with ICAT 4.3.2 has also
  been tested but did not require any changes.)

+ Implement alias names for entity attributes.  This facilitates
  compatibility of client programs to different ICAT versions.  E.g. a
  client program may use `rule.grouping` regardless of the ICAT
  version, for ICAT 4.2.* this is aliased to `rule.group`.

+ Add a method :meth:`icat.client.Client.assertedSearch`.

+ Add a method :meth:`icat.entity.Entity.getUniqueKey`.

+ Add entity methods :meth:`Group.getUsers` and
  :meth:`Instrument.getInstrumentScientists`.

+ WARNING, incompatible change!

  Changed entity methods :meth:`Instrument.addInstrumentScientist` and
  :meth:`Investigation.addInvestigationUser` to not to create the
  respective user any more, but rather expect a list of existing users
  as argument.  Renamed :meth:`Group.addUser`,
  :meth:`Instrument.addInstrumentScientist`, and
  :meth:`Investigation.addInvestigationUser` to :meth:`addUsers`,
  :meth:`addInstrumentScientists`, and :meth:`addInvestigationUsers`
  (note the plural "s") respectively.

  In the client code, replace::

    pi = investigation.addInvestigationUser(uid, fullName=userName,
                                            search=True,
                                            role="Principal Investigator")

  by ::

    pi = client.createUser(uid, fullName=userName, search=True)
    investigation.addInvestigationUsers([pi], role="Principal Investigator")

+ Work around a bug in the way SUDS deals with datetime values: set
  the local time zone to ``UTC``.

+ Add example scripts :ref:`icatdump` and :ref:`icatrestore <icatingest>`.


.. _changes-0_2_0:

0.2.0 (2013-11-18)
~~~~~~~~~~~~~~~~~~

+ Rework internals of :mod:`icat.config`.

+ Bugfix: :class:`icat.config.Config` required a password to be set
  even if prompt for password was requested.

+ Add support for configuration via environment variables.

+ Add support of HTTP proxy settings.  [Suggested by Alistair Mills]

+ WARNING, incompatible change!
  The configuration read by :mod:`icat.config` is not stored as
  attributes on the :class:`icat.config.Config` object itself, but
  rather :meth:`icat.config.Config.getconfig` returns an object with
  these attributes set.  This keeps the configuration values cleanly
  separated from the attributes of the :class:`icat.config.Config`
  object.

  In the client code, replace::

    conf = icat.config.Config()
    conf.getconfig()

  by ::

    config = icat.config.Config()
    conf = config.getconfig()

+ Move :exc:`ConfigError` from :mod:`icat.config` to
  :mod:`icat.exception`.

+ Move :exc:`GenealogyError` from :mod:`icat.icatcheck` to
  :mod:`icat.exception`.

+ Review export of symbols.  Most client programs should only need to
  import :mod:`icat` and :mod:`icat.config`.


.. _changes-0_1_0:

0.1.0 (2013-11-01)
~~~~~~~~~~~~~~~~~~

+ Initial version
