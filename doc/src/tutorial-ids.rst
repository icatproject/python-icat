Working with IDS
~~~~~~~~~~~~~~~~

You can use python-icat not only as a client for ICAT, but also for
IDS.  In this tutorial section, we look at some basic examples of
this.  The examples below assume to have a running IDS server that is
ready to accept our requests.

If you set the `idsurl` configuration variable before calling
:meth:`~icat.config.Config.getconfig` at the beginning of your
program, python-icat will automatically provide an IDS client for you
(see :doc:`tutorial-config` for details).  You can then access IDS
specific methods via the :attr:`~icat.client.Client.ids` attribute as
part of your :class:`~icat.client.Client` object, i.e. by writing
`client.ids`::

  $ python -i login.py -s myicat_root
  Login to https://localhost:8181/ICATService/ICAT?wsdl was successful.
  User: simple/root
  >>> client.ids.isReadOnly()
  False

Additionally, some IDS methods can also be accessed directly from the
:class:`~icat.client.Client` object, e.g.
:meth:`~icat.client.Client.putData`.  These convenience methods are
automatically mapped to the corresponding method in the
:class:`~icat.ids.IDSClient` class.

Creating a datafile
-------------------

To upload a datafile to ICAT, you first have to create a local
``Datafile`` object with the corresponding attributes and references.
In the example below, we will add a new datafile to one of the
existing ``Dataset`` objects from the previous tutorial section::

  >>> f1 = client.new("datafileFormat", name="Test Format 1", version="1.0")
  >>> df1 = client.new("datafile")
  >>> df1.dataset = client.get("Dataset", 1)
  >>> df1.datafileFormat = f1
  >>> df1.name = "DF1"
  >>> df1.description = "Datafile 1"

Note that the object hasn't been created in ICAT yet.  So far, it
exists only in local memory.  Now, we can call the
:meth:`~icat.client.Client.putData` convenience method to upload our
datafile to IDS.  Here, we assume to have a file 'test.dat' located in
the current working directory::

  >>> client.putData("test.dat", df1)
  (datafile){
     createId = "simple/root"
     createTime = 2019-12-09 11:18:42+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-12-09 11:18:42+01:00
     checksum = "487ec51f"
     datafileCreateTime = 2019-12-09 11:04:55+01:00
     datafileModTime = 2019-12-09 11:04:55+01:00
     description = "Datafile 1"
     fileSize = 60
     location = "1/1/7f5c2064-d4b6-4392-bf35-5b74201564cb"
     name = "DF1"
   }

In the above output, we can see the new object and its attributes.
Things like the `fileSize` and a `checksum` were set automatically.

Working with data objects in IDS
--------------------------------

There are multiple ways to select data in IDS.  The easiest way is to
directly ask for a particular set of data objects using the
:meth:`~icat.client.Client.getData` method.  Since we still have the
datafile object ``df1`` in local memory, we can specify the data
objects we want to select by passing a list of
:class:`~icat.entity.Entity` objects::

  >>> data = client.getData([df1])
  >>> for line in data:
  ...     print(line.strip())
  ...
  Datafile test content
  Very important

Alternatively, we could have specified a dictionary with lists of
IDs::

  >>> data = client.getData({"datafileIds": [1]})
  >>> for line in data:
  ...     print(line.strip())
  ...
  Datafile test content
  Very important

We can also select an entire dataset.  In this case, the response is a
zip file which we may process as follows::

  >>> from StringIO import StringIO
  >>> from zipfile import ZipFile
  >>> data = client.getData({"datasetIds": [1]})
  >>> zipdata = StringIO()
  >>> zipdata.write(data.read())
  >>> zipfile = ZipFile(zipdata)
  >>> for f in zipfile.namelist():
  ...     print("FILENAME: %s" % f)
  ...     print(zipfile.open(f).read())
  ...
  FILENAME: ids/Fac1/Inv/1-1/D1/DF1
  Datafile test content
  Very important

When downloading large sets of data objects from IDS, it may be
necessary to prepare the data first.  Here, we use the
:class:`~icat.ids.DataSelection` class to specify the data object we
want to select::

  >>> from icat.ids import DataSelection
  >>> selection = DataSelection({"datasetIds": [1, 2]})

Now we can instruct IDS to prepare the data by calling the
:meth:`~icat.client.Client.prepareData` method.  In response, we get a
`preparedId` which we can use to retrieve the data via the
:meth:`~icat.client.Client.getPreparedData` method once it's ready::

  >>> preparedId = client.prepareData(selection)
  >>> print(preparedId)
  744a83ae-a09d-4d29-93f2-7a90b56ea7ad
  >>> client.isDataPrepared(preparedId)
  True
  >>> data = client.getPreparedData(preparedId)

We can process the response the same as before::

  >>> zipdata = StringIO()
  >>> zipdata.write(data.read())
  >>> zipfile = ZipFile(zipdata)
  >>> for f in zipfile.namelist():
  ...     print("FILENAME: %s" % f)
  ...     print(zipfile.open(f).read())
  ...
  FILENAME: ids/Fac1/Inv/1-1/D1/DF1
  Datafile test content
  Very important

Because we created a :class:`~icat.ids.DataSelection` object earlier,
we can now use several additional methods from the
:class:`~icat.ids.IDSClient` class which take the `selection` as an
argument.

For example, :meth:`~icat.ids.IDSClient.getStatus` lets us check the
status of our selection::

  >>> client.ids.getStatus(selection)
  u'ONLINE'

With :meth:`~icat.ids.IDSClient.getSize` we can get the total size of
our selection in bytes::

  >>> client.ids.getSize(selection)
  37L

The :meth:`~icat.ids.IDSClient.getDatafileIds` method returns a list
with IDs of all datafiles which are part of the selection.  Among
other things, we can use the IDs to obtain hard links to particular
datafiles by calling the :meth:`~icat.ids.IDSClient.getLink` method::

  >>> client.ids.getDatafileIds(selection)
  [1]
  >>> client.ids.getLink(1)
  u'/home/icat/ids/cache/link/aa8dc56f-ee10-4da5-8fb8-debf9d6aaf66'

Finally, we can delete one or more data objects from IDS by calling
:meth:`~icat.client.Client.deleteData`.  This will also remove the
corresponding entries from the ICAT catalogue::

  >>> client.deleteData(selection)
  >>> client.search("Datafile")
  []

