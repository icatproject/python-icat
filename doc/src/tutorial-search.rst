Searching for objects in the ICAT Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are many ways to search for objects in ICAT using python-icat.
Until now, we have seen how we can manually write JPQL query strings
and pass them to the :meth:`~icat.client.Client.search` method::

  $ python -i login.py -s myicat_root
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
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

Preparing some example data
---------------------------

Before we can query the ICAT Server, we need to create some more
objects.  We start by adding an ``Investigation`` object::

  >>> t1 = client.new("investigationType", name="Test Investigation")
  >>> t1.facility = client.get("Facility", 1)
  >>> t1.create()
  >>> i1 = client.new("investigation", name="Inv", visitId="1-1", title="Test")
  >>> i1.facility = client.get("Facility", 1)
  >>> i1.type = t1
  >>> i1.create()

Next, we add two ``Dataset`` objects below the investigation::

  >>> t2 = client.new("datasetType", name="Test Dataset")
  >>> t2.facility = client.get("Facility", 1)
  >>> t2.create()
  >>> ds1 = client.new("dataset", name="D1", complete=False, investigation=i1)
  >>> ds1.type = t2
  >>> ds1.create()
  >>> ds2 = client.new("dataset", name="D2", complete=False, investigation=i1)
  >>> ds2.type = t2
  >>> ds2.create()

Lastly, we make some ``DatasetParameter`` objects::

  >>> dp1 = client.new("datasetParameter", numericValue=10)
  >>> dp1.type = client.get("ParameterType", 1)
  >>> dp1.dataset = ds1
  >>> dp2 = client.new("datasetParameter", stringValue="buono")
  >>> dp2.type = client.get("ParameterType", 2)
  >>> dp2.dataset = ds1
  >>> dp3 = client.new("datasetParameter", numericValue=22)
  >>> dp3.type = client.get("ParameterType", 1)
  >>> dp3.dataset = ds2
  >>> dp4 = client.new("datasetParameter", stringValue="brutto")
  >>> dp4.type = client.get("ParameterType", 2)
  >>> dp4.dataset = ds2
  >>> client.createMany([dp1, dp2, dp3, dp4])

Now let's see how we can query ICAT to find the objects we just added.
Given a local object (such as ``dp1`` above), one simple way to
retrieve a matching object from ICAT is using the
:meth:`~icat.client.Client.searchMatching` method::

  >>> client.searchMatching(dp1)
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 10.0
   }

However, usually we do not have the objects we're looking for in local
memory, so we have to search for them using queries.  The
:class:`icat.query.Query` class can help us with that.

Building advanced queries
-------------------------

In order to use the :class:`~icat.query.Query` class, we have to
import it first::

  >>> from icat.query import Query

Now let's have a look at some examples.  We start with a simple query
that lists all investigations::

  >>> query = Query(client, "Investigation")
  >>> print(query)
  SELECT o FROM Investigation o
  >>> client.search(query)
  [(investigation){
     createId = "simple/root"
     createTime = 2019-12-02 13:30:30+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:30:30+01:00
     name = "Inv"
     title = "Test"
     visitId = "1-1"
   }]

Extending the above query to include the datasets::

  >>> query.addIncludes(["datasets"])
  >>> print(query)
  SELECT o FROM Investigation o INCLUDE o.datasets
  >>> client.search(query)
  [(investigation){
     createId = "simple/root"
     createTime = 2019-12-02 13:30:30+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:30:30+01:00
     datasets[] =
        (dataset){
           createId = "simple/root"
           createTime = 2019-12-02 13:30:45+01:00
           id = 1
           modId = "simple/root"
           modTime = 2019-12-02 13:30:45+01:00
           complete = False
           name = "D1"
        },
        (dataset){
           createId = "simple/root"
           createTime = 2019-12-02 13:30:52+01:00
           id = 2
           modId = "simple/root"
           modTime = 2019-12-02 13:30:52+01:00
           complete = False
           name = "D2"
        },
     name = "Inv"
     title = "Test"
     visitId = "1-1"
   }]

Listing the names of all datasets::

  >>> query = Query(client, "Dataset", attribute="name")
  >>> print(query)
  SELECT o.name FROM Dataset o
  >>> client.search(query)
  [D1, D2]

Counting the total number of datasets::

  >>> query = Query(client, "Dataset", aggregate="COUNT")
  >>> print(query)
  SELECT COUNT(o) FROM Dataset o
  >>> client.search(query)
  [2L]

Finding the average of all numeric dataset parameter values::

  >>> query = Query(client, "DatasetParameter")
  >>> query.addConditions({"type.id": "=1"})
  >>> query.setAttribute("numericValue")
  >>> query.setAggregate("AVG")
  >>> print(query)
  SELECT AVG(o.numericValue) FROM DatasetParameter o JOIN o.type AS t WHERE t.id =1
  >>> client.search(query)
  [16.0]

Listing all numeric dataset parameters ordered by createTime and
value::

  >>> query = Query(client, "DatasetParameter")
  >>> query.addConditions({"type.id": "=1"})
  >>> query.setOrder(["createTime", ("numericValue", "DESC")])
  >>> print(query)
  SELECT o FROM DatasetParameter o JOIN o.type AS t WHERE t.id =1 ORDER BY o.createTime, o.numericValue DESC
  >>> client.search(query)
  [(datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 3
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 22.0
   }, (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 10.0
   }]

Limiting the number of returned items using a LIMIT clause.  In the
example below, skip 1 item and return only 2 of the remaining
items::

  >>> query = Query(client, "DatasetParameter")
  >>> query.setLimit((1,2))
  >>> query.setOrder(["id"])
  >>> print(query)
  SELECT o FROM DatasetParameter o ORDER BY o.id LIMIT 1, 2
  >>> client.search(query)
  [(datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 2
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     stringValue = "buono"
   }, (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 3
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 22.0
   }]

Useful search methods
---------------------

If you are looking for one `specific` object and know its unique
identifier (`id`), you can simply retrieve it using the
:meth:`~icat.client.Client.get` method::

  >>> client.get("DatasetParameter", 3)
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 3
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 22.0
   }

Another way to generate a unique key for an object is by calling the
:meth:`icat.entity.Entity.getUniqueKey` method.  Once you have the
unique key, you can use it to search for the object by calling the
:meth:`icat.client.Client.searchUniqueKey` method::

  >>> obj = client.get("Investigation i INCLUDE i.facility", 1)
  >>> key = obj.getUniqueKey()
  >>> print(key)
  Investigation_facility-(name-Fac1)_name-Inv_visitId-1=2D1
  >>> client.searchUniqueKey(key)
  (investigation){
     createId = "simple/root"
     createTime = 2019-12-02 13:30:30+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:30:30+01:00
     name = "Inv"
     title = "Test"
     visitId = "1-1"
   }

If you expect to find a certain number of objects, you can use the
:meth:`~icat.client.Client.assertedSearch` method.  This will raise an
error if the number of items found doesn't lie within the specified
bound.

To find `exactly one` object, call the method like this::

  >>> client.assertedSearch("SELECT i FROM Investigation i WHERE i.name='Inv'")
  [(investigation){
     createId = "simple/root"
     createTime = 2019-12-02 13:30:30+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:30:30+01:00
     name = "Inv"
     title = "Test"
     visitId = "1-1"
   }]

To make sure that you get `at least` 2 objects, for example, specify
the additional parameters `assertmin` and `assertmax`::

  >>> client.assertedSearch("Dataset", assertmin=2, assertmax=None)
  [(dataset){
     createId = "simple/root"
     createTime = 2019-12-02 13:30:45+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:30:45+01:00
     complete = False
     name = "D1"
   }, (dataset){
     createId = "simple/root"
     createTime = 2019-12-02 13:30:52+01:00
     id = 2
     modId = "simple/root"
     modTime = 2019-12-02 13:30:52+01:00
     complete = False
     name = "D2"
   }]

To limit the number of items retrieved `per call`, you can use the
:meth:`~icat.client.Client.searchChunked` method.  This method
repeatedly calls the regular :meth:`~icat.client.Client.search` method
as often as needed to retrieve the whole search result.  Thus, it
avoids the error if the number of items in the result exceeds the
limit imposed by the ICAT server.  By default, the chunksize is set to
100, but you can adjust it to fit your needs.

In the example below, we perform a chunked search to retrieve all four
dataset parameters, using chunks of size 2 each.  Instead of a list,
the method returns an iterator over the items in the search result.
This doesn't need as much memory when performing large queries::

  >>> for p in client.searchChunked("DatasetParameter", chunksize=2):
  ...     print(p)
  ...
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 10.0
   }
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 2
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     stringValue = "buono"
   }
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 3
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 22.0
   }
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 4
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     stringValue = "brutto"
   }

Beware that due to the way this method works, the result may be
defective (omissions, duplicates) if the content in the ICAT server
changes between individual search calls in a way that would affect the
result.  Hence, make sure you don't have code with side effects on the
search result in the body of the loop (i.e. editing objects) when
looping over the returned items.

Using the `skip` and `count` parameters, the method also allows you to
skip a certain number of items and to set an upper limit on the number
of items you want to fetch.  This is equivalent to having a LIMIT
clause in the query.  Because of this, the query string itself must
not contain a LIMIT clause.  Consider the following example where we
skip 1 item and return only 2 of the remaining items::

  >>> for p in client.searchChunked("DatasetParameter", skip=1, count=2):
  ...     print(p)
  ...
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 2
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     stringValue = "buono"
   }
  (datasetParameter){
     createId = "simple/root"
     createTime = 2019-12-02 13:31:24+01:00
     id = 3
     modId = "simple/root"
     modTime = 2019-12-02 13:31:24+01:00
     numericValue = 22.0
   }

