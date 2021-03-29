Searching for objects in the ICAT server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are many ways to search for objects in ICAT using python-icat.
Until now, we have seen how we can manually write JPQL query strings
and pass them to the :meth:`~icat.client.Client.search` method::

  $ python -i login.py -s myicat_root
  Login to https://icat.example.com:8181 was successful.
  User: simple/root
  >>> client.search("SELECT f FROM Facility f INCLUDE f.parameterTypes LIMIT 1,1")
  [(facility){
     createId = "simple/root"
     createTime = 2019-11-26 12:40:02+01:00
     id = 2
     modId = "simple/root"
     modTime = 2019-11-26 12:49:28+01:00
     daysUntilRelease = 1826
     fullName = "Fac2 Facility"
     name = "Fac2"
   }]

However, as our queries get more complicated, this can be a bit
inconvenient.  The :mod:`icat.query` module provides an easier and
less error-prone way to build queries.  In addition, the
:class:`icat.client.Client` class has some useful methods as well.

But before we get into that, we will make sure that we actually have
some well defined and rich content to search for.  Run the following
commands at the command line::

  $ wipeicat -s myicat_root
  $ icatingest -s myicat_root -i icatdump-4.10.yaml

:ref:`wipeicat` and :ref:`icatingest` are two scripts that get
installed with python-icat.  Depending on the situation, these scripts
may be installed either with or without a trailing ``.py`` extension.
The file `icatdump-4.10.yaml` can be found in the python-icat source
distribution.  The first command deletes all content from the ICAT
server that we may have created in the previous sections.  The second
command reads the `icatdump-4.10.yaml` file and creates all objects
listed therein in the ICAT server.

.. note::
   As the name suggests, the content in `icatdump-4.10.yaml` requires
   an ICAT server version 4.10 or newer.  If you are using an older
   ICAT, you may just as well use the `icatdump-4.7.yaml` or
   `icatdump-4.4.yaml` file instead, matching the respective older
   versions.  For the sake of this tutorial, the difference does not
   matter.

.. note::
   The search results in the following examples may depend on the user
   you log into ICAT as, because not all users have read access to all
   data.  The examples assume that your user name (as displayed by the
   `login.py` script) is `db/nbour`.  If that does not work for you,
   you may as well log in as root.

Building advanced queries
-------------------------

The :mod:`icat.query` module provides the :class:`~icat.query.Query`
class.  We need to import it first::

  $ python -i login.py -s myicat_nbour
  Login to https://icat.example.com:8181 was successful.
  User: db/nbour
  >>> from icat.query import Query

Now let's have a look at some examples.  We start with a simple query
that lists all investigations::

  >>> query = Query(client, "Investigation")
  >>> print(query)
  SELECT o FROM Investigation o
  >>> client.search(query)
  [(investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:27+01:00
     id = 1
     modId = "simple/root"
     modTime = 2020-02-05 16:49:27+01:00
     name = "08100122-EF"
     startDate = 2008-03-13 11:39:42+01:00
     title = "Durol single crystal"
     visitId = "1.1-P"
   }, (investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:28+01:00
     id = 2
     modId = "simple/root"
     modTime = 2020-02-05 16:49:28+01:00
     endDate = 2010-10-12 17:00:00+02:00
     name = "10100601-ST"
     startDate = 2010-09-30 12:27:24+02:00
     title = "Ni-Mn-Ga flat cone"
     visitId = "1.1-N"
   }, (investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:33+01:00
     id = 3
     modId = "simple/root"
     modTime = 2020-02-05 16:49:33+01:00
     endDate = 2012-08-06 03:10:08+02:00
     name = "12100409-ST"
     startDate = 2012-07-26 17:44:24+02:00
     title = "NiO SC OF1 JUH HHL"
     visitId = "1.1-P"
   }]

In order to search for a particular investigation, we may add an
appropriate condition.  The `conditions` argument to
:class:`~icat.query.Query` should be a mapping of attribute names to
conditions on that attribute::

  >>> query = Query(client, "Investigation", conditions={"name": "= '10100601-ST'"})
  >>> print(query)
  SELECT o FROM Investigation o WHERE o.name = '10100601-ST'
  >>> client.search(query)
  [(investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:28+01:00
     id = 2
     modId = "simple/root"
     modTime = 2020-02-05 16:49:28+01:00
     endDate = 2010-10-12 17:00:00+02:00
     name = "10100601-ST"
     startDate = 2010-09-30 12:27:24+02:00
     title = "Ni-Mn-Ga flat cone"
     visitId = "1.1-N"
   }]

We may also include related objects in the search results::

  >>> query = Query(client, "Investigation", conditions={"name": "= '10100601-ST'"}, includes=["datasets"])
  >>> print(query)
  SELECT o FROM Investigation o WHERE o.name = '10100601-ST' INCLUDE o.datasets
  >>> client.search(query)
  [(investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:28+01:00
     id = 2
     modId = "simple/root"
     modTime = 2020-02-05 16:49:28+01:00
     datasets[] =
        (dataset){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:29+01:00
           id = 3
           modId = "simple/root"
           modTime = 2020-02-05 16:49:29+01:00
           complete = False
           endDate = 2010-10-01 08:17:48+02:00
           name = "e208339"
           startDate = 2010-09-30 12:27:24+02:00
        },
        (dataset){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:32+01:00
           id = 4
           modId = "simple/root"
           modTime = 2020-02-05 16:49:32+01:00
           complete = False
           endDate = 2010-10-05 10:32:21+02:00
           name = "e208341"
           startDate = 2010-10-02 04:00:21+02:00
        },
        (dataset){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:32+01:00
           id = 5
           modId = "simple/root"
           modTime = 2020-02-05 16:49:32+01:00
           complete = False
           endDate = 2010-10-12 17:00:00+02:00
           name = "e208342"
           startDate = 2010-10-09 07:00:00+02:00
        },
     endDate = 2010-10-12 17:00:00+02:00
     name = "10100601-ST"
     startDate = 2010-09-30 12:27:24+02:00
     title = "Ni-Mn-Ga flat cone"
     visitId = "1.1-N"
   }]

The conditions in a query may also be put on the attributes of related
objects.  This allows rather complex queries.  Let us search for the
datasets in this investigation that have been measured in a magnetic
field larger then 5 Tesla and include its parameters in the result::

  >>> conditions = {
  ...     "investigation.name": "= '10100601-ST'",
  ...     "parameters.type.name": "= 'Magnetic field'",
  ...     "parameters.type.units": "= 'T'",
  ...     "parameters.numericValue": "> 5.0",
  ... }
  >>> query = Query(client, "Dataset", conditions=conditions, includes=["parameters.type"])
  >>> print(query)
  SELECT o FROM Dataset o JOIN o.investigation AS i JOIN o.parameters AS p JOIN p.type AS pt WHERE i.name = '10100601-ST' AND p.numericValue > 5.0 AND pt.name = 'Magnetic field' AND pt.units = 'T' INCLUDE o.parameters AS p, p.type
  >>> client.search(query)
  [(dataset){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:29+01:00
     id = 3
     modId = "simple/root"
     modTime = 2020-02-05 16:49:29+01:00
     complete = False
     endDate = 2010-10-01 08:17:48+02:00
     name = "e208339"
     parameters[] =
        (datasetParameter){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:29+01:00
           id = 1
           modId = "simple/root"
           modTime = 2020-02-05 16:49:29+01:00
           numericValue = 7.3
           type =
              (parameterType){
                 createId = "simple/root"
                 createTime = 2020-02-05 16:49:24+01:00
                 id = 5
                 modId = "simple/root"
                 modTime = 2020-02-05 16:49:24+01:00
                 applicableToDataCollection = False
                 applicableToDatafile = False
                 applicableToDataset = True
                 applicableToInvestigation = False
                 applicableToSample = False
                 enforced = False
                 name = "Magnetic field"
                 units = "T"
                 unitsFullName = "Tesla"
                 valueType = "NUMERIC"
                 verified = False
              }
        },
        (datasetParameter){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:29+01:00
           id = 2
           modId = "simple/root"
           modTime = 2020-02-05 16:49:29+01:00
           numericValue = 5.0
           type =
              (parameterType){
                 createId = "simple/root"
                 createTime = 2020-02-05 16:49:24+01:00
                 id = 7
                 modId = "simple/root"
                 modTime = 2020-02-05 16:49:24+01:00
                 applicableToDataCollection = False
                 applicableToDatafile = False
                 applicableToDataset = True
                 applicableToInvestigation = False
                 applicableToSample = False
                 enforced = False
                 name = "Reactor power"
                 units = "MW"
                 unitsFullName = "Megawatt"
                 valueType = "NUMERIC"
                 verified = False
              }
        },
     startDate = 2010-09-30 12:27:24+02:00
   }]

We may incrementally add conditions to a query.  This is particularly
useful if the presence of some of the conditions depend on the logic
of your Python program.  Consider::

  >>> def get_investigation(client, name, visitId=None):
  ...     query = Query(client, "Investigation")
  ...     query.addConditions({"name": "= '%s'" % name})
  ...     if visitId is not None:
  ...         query.addConditions({"visitId": "= '%s'" % visitId})
  ...     print(query)
  ...     return client.assertedSearch(query)[0]
  ...
  >>> get_investigation(client, "08100122-EF")
  SELECT o FROM Investigation o WHERE o.name = '08100122-EF'
  (investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:27+01:00
     id = 1
     modId = "simple/root"
     modTime = 2020-02-05 16:49:27+01:00
     name = "08100122-EF"
     startDate = 2008-03-13 11:39:42+01:00
     title = "Durol single crystal"
     visitId = "1.1-P"
   }
  >>> get_investigation(client, "12100409-ST", "1.1-P")
  SELECT o FROM Investigation o WHERE o.name = '12100409-ST' AND o.visitId = '1.1-P'
  (investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:33+01:00
     id = 3
     modId = "simple/root"
     modTime = 2020-02-05 16:49:33+01:00
     endDate = 2012-08-06 03:10:08+02:00
     name = "12100409-ST"
     startDate = 2012-07-26 17:44:24+02:00
     title = "NiO SC OF1 JUH HHL"
     visitId = "1.1-P"
   }

This `get_investigation()` function will search for investigations,
either by `name` alone or by `name` and `visitId`, depending on the
arguments.

It is also possible to put more then one conditions on a single
attribute: setting the corresponding value in the `conditions`
argument to a list of strings will result in combining the conditions
on that attribute.  Search for all datafiles created in 2012::

  >>> conditions = {
  ...     "datafileCreateTime": [">= '2012-01-01'", "< '2013-01-01'"]
  ... }
  >>> query = Query(client, "Datafile", conditions=conditions)
  >>> print(query)
  SELECT o FROM Datafile o WHERE o.datafileCreateTime >= '2012-01-01' AND o.datafileCreateTime < '2013-01-01'
  >>> client.search(query)
  [(datafile){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:34+01:00
     id = 7
     modId = "simple/root"
     modTime = 2020-02-05 16:49:34+01:00
     datafileCreateTime = 2012-07-16 16:30:17+02:00
     datafileModTime = 2012-07-16 16:30:17+02:00
     fileSize = 28937
     name = "e208945-2.nxs"
   }, (datafile){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:34+01:00
     id = 8
     modId = "simple/root"
     modTime = 2020-02-05 16:49:34+01:00
     checksum = "bd55affa"
     datafileCreateTime = 2012-07-30 03:10:08+02:00
     datafileModTime = 2012-07-30 03:10:08+02:00
     fileSize = 459
     name = "e208945.dat"
   }, (datafile){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:34+01:00
     id = 10
     modId = "simple/root"
     modTime = 2020-02-05 16:49:34+01:00
     datafileCreateTime = 2012-07-16 16:30:17+02:00
     datafileModTime = 2012-07-16 16:30:17+02:00
     fileSize = 14965
     name = "e208947.nxs"
   }]

Of course, that last example also works when adding the conditions
incrementally::

  >>> query = Query(client, "Datafile")
  >>> query.addConditions({"datafileCreateTime": ">= '2012-01-01'"})
  >>> query.addConditions({"datafileCreateTime": "< '2013-01-01'"})
  >>> print(query)
  SELECT o FROM Datafile o WHERE o.datafileCreateTime >= '2012-01-01' AND o.datafileCreateTime < '2013-01-01'

Instead of returning a list of the matching objects, we may also
request single attributes.  The result will be a list of the attribute
values of the matching objects.  Listing the names of all datasets::

  >>> query = Query(client, "Dataset", attributes="name")
  >>> print(query)
  SELECT o.name FROM Dataset o
  >>> client.search(query)
  [e201215, e201216, e208339, e208341, e208342, e208945, e208946, e208947]

As the name of that keyword argument suggests, we may also search for
multiple attributes at once.  The result will be a list of attribute
values rather then a single value for each object found in the query.
This requires an ICAT server version 4.11 or newer though::

  >>> query = Query(client, "Dataset", attributes=["investigation.name", "name", "complete", "type.name"])
  >>> print(query)
  SELECT i.name, o.name, o.complete, t.name FROM Dataset o JOIN o.investigation AS i JOIN o.type AS t
  >>> client.search(query)
  [[08100122-EF, e201215, False, raw], [08100122-EF, e201216, False, raw], [10100601-ST, e208339, False, raw], [10100601-ST, e208341, False, raw], [10100601-ST, e208342, False, raw], [12100409-ST, e208945, False, raw], [12100409-ST, e208946, False, raw], [12100409-ST, e208947, True, analyzed]]

There are also some aggregate functions that may be applied to search
results.  Let's count all datasets::

  >>> query = Query(client, "Dataset", aggregate="COUNT")
  >>> print(query)
  SELECT COUNT(o) FROM Dataset o
  >>> client.search(query)
  [8]

Using such aggregate functions in a query may result in a huge
performance gain, because the counting is done directly in the
database backend of ICAT, instead of compiling a list of all datasets,
transferring them to the client, and counting them at client side.

Let's check for a given investigation, the minimum, maximum, and
average magnetic field applied in the measurements::

  >>> conditions = {
  ...     "dataset.investigation.name": "= '10100601-ST'",
  ...     "type.name": "= 'Magnetic field'",
  ...     "type.units": "= 'T'",
  ... }
  >>> query = Query(client, "DatasetParameter", conditions=conditions, attributes="numericValue")
  >>> print(query)
  SELECT o.numericValue FROM DatasetParameter o JOIN o.dataset AS ds JOIN ds.investigation AS i JOIN o.type AS t WHERE i.name = '10100601-ST' AND t.name = 'Magnetic field' AND t.units = 'T'
  >>> client.search(query)
  [7.3, 2.7]
  >>> query.setAggregate("MIN")
  >>> print(query)
  SELECT MIN(o.numericValue) FROM DatasetParameter o JOIN o.dataset AS ds JOIN ds.investigation AS i JOIN o.type AS t WHERE i.name = '10100601-ST' AND t.name = 'Magnetic field' AND t.units = 'T'
  >>> client.search(query)
  [2.7]
  >>> query.setAggregate("MAX")
  >>> print(query)
  SELECT MAX(o.numericValue) FROM DatasetParameter o JOIN o.dataset AS ds JOIN ds.investigation AS i JOIN o.type AS t WHERE i.name = '10100601-ST' AND t.name = 'Magnetic field' AND t.units = 'T'
  >>> client.search(query)
  [7.3]
  >>> query.setAggregate("AVG")
  >>> print(query)
  SELECT AVG(o.numericValue) FROM DatasetParameter o JOIN o.dataset AS ds JOIN ds.investigation AS i JOIN o.type AS t WHERE i.name = '10100601-ST' AND t.name = 'Magnetic field' AND t.units = 'T'
  >>> client.search(query)
  [5.0]

For another example, let's search for all investigations, having any
dataset with a magnetic field parameter set::

  >>> conditions = {
  ...     "datasets.parameters.type.name": "= 'Magnetic field'",
  ...     "datasets.parameters.type.units": "= 'T'",
  ... }
  >>> query = Query(client, "Investigation", conditions=conditions)
  >>> print(query)
  SELECT o FROM Investigation o JOIN o.datasets AS s1 JOIN s1.parameters AS s2 JOIN s2.type AS s3 WHERE s3.name = 'Magnetic field' AND s3.units = 'T'
  >>> client.search(query)
  [(investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:28+01:00
     id = 2
     modId = "simple/root"
     modTime = 2020-02-05 16:49:28+01:00
     endDate = 2010-10-12 17:00:00+02:00
     name = "10100601-ST"
     startDate = 2010-09-30 12:27:24+02:00
     title = "Ni-Mn-Ga flat cone"
     visitId = "1.1-N"
   }, (investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:28+01:00
     id = 2
     modId = "simple/root"
     modTime = 2020-02-05 16:49:28+01:00
     endDate = 2010-10-12 17:00:00+02:00
     name = "10100601-ST"
     startDate = 2010-09-30 12:27:24+02:00
     title = "Ni-Mn-Ga flat cone"
     visitId = "1.1-N"
   }]

We get the same investigation twice!  The reason is that this
investigation has two datasets, both having a magnetic field parameter
respectively.  We may fix that by applying `DISTINCT`::

  >>> query.setAggregate("DISTINCT")
  >>> print(query)
  SELECT DISTINCT(o) FROM Investigation o JOIN o.datasets AS s1 JOIN s1.parameters AS s2 JOIN s2.type AS s3 WHERE s3.name = 'Magnetic field' AND s3.units = 'T'
  >>> client.search(query)
  [(investigation){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:28+01:00
     id = 2
     modId = "simple/root"
     modTime = 2020-02-05 16:49:28+01:00
     endDate = 2010-10-12 17:00:00+02:00
     name = "10100601-ST"
     startDate = 2010-09-30 12:27:24+02:00
     title = "Ni-Mn-Ga flat cone"
     visitId = "1.1-N"
   }]

`DISTINCT` may be combined with `COUNT`, `AVG`, and `SUM` in order to
make sure not to count the same object more then once::

  >>> conditions = {
  ...     "datasets.parameters.type.name": "= 'Magnetic field'",
  ...     "datasets.parameters.type.units": "= 'T'",
  ... }
  >>> query = Query(client, "Investigation", conditions=conditions, aggregate="COUNT")
  >>> print(query)
  SELECT COUNT(o) FROM Investigation o JOIN o.datasets AS s1 JOIN s1.parameters AS s2 JOIN s2.type AS s3 WHERE s3.name = 'Magnetic field' AND s3.units = 'T'
  >>> client.search(query)
  [2]
  >>> query.setAggregate("COUNT:DISTINCT")
  >>> print(query)
  SELECT COUNT(DISTINCT(o)) FROM Investigation o JOIN o.datasets AS s1 JOIN s1.parameters AS s2 JOIN s2.type AS s3 WHERE s3.name = 'Magnetic field' AND s3.units = 'T'
  >>> client.search(query)
  [1]

The JPQL queries support sorting of the results.  Search for all
dataset parameter, ordered by parameter type name (ascending), units
(ascending), and value (descending)::

  >>> order = ["type.name", "type.units", ("numericValue", "DESC")]
  >>> query = Query(client, "DatasetParameter", includes=["type"], order=order)
  >>> print(query)
  SELECT o FROM DatasetParameter o JOIN o.type AS t ORDER BY t.name, t.units, o.numericValue DESC INCLUDE o.type
  >>> client.search(query)
  [(datasetParameter){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:29+01:00
     id = 1
     modId = "simple/root"
     modTime = 2020-02-05 16:49:29+01:00
     numericValue = 7.3
     type =
        (parameterType){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:24+01:00
           id = 5
           modId = "simple/root"
           modTime = 2020-02-05 16:49:24+01:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Magnetic field"
           units = "T"
           unitsFullName = "Tesla"
           valueType = "NUMERIC"
           verified = False
        }
   }, (datasetParameter){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:32+01:00
     id = 4
     modId = "simple/root"
     modTime = 2020-02-05 16:49:32+01:00
     numericValue = 2.7
     type =
        (parameterType){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:24+01:00
           id = 5
           modId = "simple/root"
           modTime = 2020-02-05 16:49:24+01:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Magnetic field"
           units = "T"
           unitsFullName = "Tesla"
           valueType = "NUMERIC"
           verified = False
        }
   }, (datasetParameter){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:32+01:00
     id = 3
     modId = "simple/root"
     modTime = 2020-02-05 16:49:32+01:00
     numericValue = 5.0
     type =
        (parameterType){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:24+01:00
           id = 7
           modId = "simple/root"
           modTime = 2020-02-05 16:49:24+01:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Reactor power"
           units = "MW"
           unitsFullName = "Megawatt"
           valueType = "NUMERIC"
           verified = False
        }
   }, (datasetParameter){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:29+01:00
     id = 2
     modId = "simple/root"
     modTime = 2020-02-05 16:49:29+01:00
     numericValue = 5.0
     type =
        (parameterType){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:24+01:00
           id = 7
           modId = "simple/root"
           modTime = 2020-02-05 16:49:24+01:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Reactor power"
           units = "MW"
           unitsFullName = "Megawatt"
           valueType = "NUMERIC"
           verified = False
        }
   }, (datasetParameter){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:34+01:00
     id = 5
     modId = "simple/root"
     modTime = 2020-02-05 16:49:34+01:00
     numericValue = 3.92
     type =
        (parameterType){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:25+01:00
           id = 9
           modId = "simple/root"
           modTime = 2020-02-05 16:49:25+01:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Sample temperature"
           units = "C"
           unitsFullName = "Celsius"
           valueType = "NUMERIC"
           verified = False
        }
   }, (datasetParameter){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:34+01:00
     id = 6
     modId = "simple/root"
     modTime = 2020-02-05 16:49:34+01:00
     numericValue = 277.07
     type =
        (parameterType){
           createId = "simple/root"
           createTime = 2020-02-05 16:49:25+01:00
           id = 10
           modId = "simple/root"
           modTime = 2020-02-05 16:49:25+01:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Sample temperature"
           units = "K"
           unitsFullName = "Kelvin"
           valueType = "NUMERIC"
           verified = False
        }
   }]

We may limit the number of returned items.  Search for the second to
last dataset to have been finished::

  >>> query = Query(client, "Dataset", order=[("endDate", "DESC")], limit=(1, 1))
  >>> print(query)
  SELECT o FROM Dataset o ORDER BY o.endDate DESC LIMIT 1, 1
  >>> client.search(query)
  [(dataset){
     createId = "simple/root"
     createTime = 2020-02-05 16:49:34+01:00
     id = 6
     modId = "simple/root"
     modTime = 2020-02-05 16:49:34+01:00
     complete = False
     endDate = 2012-07-30 03:10:08+02:00
     name = "e208945"
     startDate = 2012-07-26 17:44:24+02:00
   }]

Useful search methods
---------------------

Additionally to the generic :meth:`~icat.client.Client.search` method
defined in the ICAT API, python-icat provides a few custom search
methods that are useful in particular situations.

assertedSearch
..............

The generic search returns a list of matching objects.  Often, the
number of objects to expect in the result is known from the context.
In the most common case, you would expect exactly one object in the
result and would raise an error if this is not the case.  This is what
:meth:`~icat.client.Client.assertedSearch` does.  Example: in many
production ICAT installations there is one and only one facility
object and you often need to fetch that in your scripts in order to
create a new investigation or a new parameter type.  Using the generic
search method you would write the following boiler plate code over and
over::

  res = client.search(Query(client, "Facility"))
  if not res:
      raise RuntimeError("Facility not found")
  elif len(res) > 1:
      raise RuntimeError("Facility not unique")
  facility = res[0]

(Note that you cannot safely subscript the result unless you know it's
not empty.)  Using :meth:`~icat.client.Client.assertedSearch`, you can
write the same as::

  facility = client.assertedSearch(Query(client, "Facility"))[0]

searchChunked
.............

A production ICAT has many datasets and datafiles.  You cannot search
for all of them at once, because the result might not fit in your
client's memory.  Furthermore, ICAT has a configured limit for the
maximum of objects to return in one search call, so you might hit that
wall if you are not careful.  The
:meth:`~icat.client.Client.searchChunked` method comes handy if you
need to iterate over a potentially large set of results.  It can be
used as a drop in replacement for the generic search method most of
the times, see the reference documentation for some subtle
differences.  You can safely do things like::

  for ds in client.searchChunked(Query(client, "Dataset")):
      # do something useful with the dataset ds ...
      print(ds.name)


searchMatching
..............

Given an object having all the attributes and related objects set that
form the uniqueness constraint for the object type, the
:meth:`~icat.client.Client.searchMatching` method searches this very
object from the ICAT server.  While this may not sound very useful at
first glance, it has a particular use case::

  def get_dataset(client, inv_name, ds_name, ds_type="raw"):
      """Get a dataset in an investigation.
      If it already exists, search and return it, create it, if not.
      """
      try:
          dataset = client.new("dataset")
          query = Query(client, "Investigation", conditions={
              "name": "= '%s'" % inv_name
          })
          dataset.investigation = client.assertedSearch(query)[0]
          query = Query(client, "DatasetType", conditions={
              "name": "= '%s'" % ds_type
          })
          dataset.type = client.assertedSearch(query)[0]
          dataset.complete = False
          dataset.name = ds_name
          dataset.create()
      except icat.ICATObjectExistsError:
          dataset = client.searchMatching(dataset)
      return dataset
