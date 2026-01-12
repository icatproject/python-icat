Upload and download files to and from IDS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ICAT Data Service (IDS) is the component that manages the storage
in ICAT.  It implements file upload and download.  You can use
python-icat not only as a client for ICAT, but also for IDS.  In this
tutorial section, we look at some basic examples of this.  The
examples below assume to have a running IDS that is ready to accept
our requests.

If the `idsurl` configuration variable is set (see
:doc:`tutorial-config` for details), python-icat will provide an IDS
client in the :attr:`~icat.client.Client.ids` attribute of the
:class:`~icat.client.Client` class.  This :class:`~icat.ids.IDSClient`
provides methods for the IDS API calls::

  $ python -i login.py -s myicat_nbour
  Login to https://icat.example.com:8181 was successful.
  User: db/nbour
  >>> client.ids.isReadOnly()
  False

Additionally, the :class:`~icat.client.Client` class directly provides
methods for some of the mosten often needed IDS calls.  These custom
IDS methods are based on the low level IDS client methods but are
somewhat more convenient to use and integrate better in the
python-icat data structures.

This tutorial section uses the same example content in ICAT as the
previous section.  This content can be set up with the following
commands at the command line::

  $ wipeicat -s myicat_root
  $ icatingest -s myicat_root -i icatdump-6.2.yaml

If you already did that for the previous section, you don't need to
repeat it.  Take notice of the hint on the content of the
`icatdump-6.2.yaml` file and ICAT server versions from the previous
section.

Upload files
------------

Obviously, we would need some local files first, if we want to upload
them.  Let's create a few::

  >>> users = [("jdoe", "John"), ("nbour", "Nicolas"), ("rbeck", "Rudolph")]
  >>> for user, name in users:
  ...     with open("greet-%s.txt" % user, "wt") as f:
  ...         print("Hello %s!" % name, file=f)
  ...

We need a dataset in ICAT that the uploaded files should be put into,
so let's create one::

  >>> from icat.query import Query
  >>> query = Query(client, "Investigation", conditions={"name": "= '12100409-ST'"})
  >>> investigation = client.assertedSearch(query)[0]
  >>> dataset = client.new("Dataset")
  >>> dataset.investigation = investigation
  >>> query = Query(client, "DatasetType", conditions={"name": "= 'other'"})
  >>> dataset.type = client.assertedSearch(query)[0]
  >>> dataset.name = "greetings"
  >>> dataset.complete = False
  >>> dataset.create()

For each of the files, we create a new datafile object and call the
:meth:`~icat.client.Client.putData` method to upload it::

  >>> query = Query(client, "DatafileFormat", conditions={"name": "= 'Text'"})
  >>> df_format = client.assertedSearch(query)[0]
  >>> for fname in ("greet-jdoe.txt", "greet-nbour.txt", "greet-rbeck.txt"):
  ...     datafile = client.new("Datafile",
  ...                           name=fname,
  ...                           dataset=dataset,
  ...                           datafileFormat=df_format)
  ...     client.putData(fname, datafile)
  ...
  (datafile){
     createId = "db/nbour"
     createTime = 2025-12-01 16:15:46+01:00
     id = 12
     modId = "db/nbour"
     modTime = 2025-12-01 16:15:46+01:00
     checksum = "bef32c73"
     datafileCreateTime = 2025-12-01 16:14:58+01:00
     datafileModTime = 2025-12-01 16:14:58+01:00
     fileSize = 12
     location = "3/10/811120a0-2d11-4628-b0b4-3d630871d4a7"
     name = "greet-jdoe.txt"
   }
  (datafile){
     createId = "db/nbour"
     createTime = 2025-12-01 16:15:46+01:00
     id = 13
     modId = "db/nbour"
     modTime = 2025-12-01 16:15:46+01:00
     checksum = "9012de77"
     datafileCreateTime = 2025-12-01 16:14:58+01:00
     datafileModTime = 2025-12-01 16:14:58+01:00
     fileSize = 15
     location = "3/10/7ea664ec-ddae-48d5-b73b-631082f9107a"
     name = "greet-nbour.txt"
   }
  (datafile){
     createId = "db/nbour"
     createTime = 2025-12-01 16:15:46+01:00
     id = 14
     modId = "db/nbour"
     modTime = 2025-12-01 16:15:46+01:00
     checksum = "cc830993"
     datafileCreateTime = 2025-12-01 16:14:58+01:00
     datafileModTime = 2025-12-01 16:14:58+01:00
     fileSize = 15
     location = "3/10/5a48d180-723d-4d71-bb74-b11607284578"
     name = "greet-rbeck.txt"
   }

Note that we did not create these datafiles in ICAT.  IDS did this for
us in response to the :meth:`~icat.client.Client.putData` call.  IDS
also calculated the checksum and set the file size.  The location
attribute is also set by IDS and is mostly only relevant internally in
IDS.  The value depends on the IDS storage plugin and may be
different.  The datafileCreateTime and the datafileModTime has been
determined by fstat'ing the local files in
:meth:`~icat.client.Client.putData`.

Download files
--------------

We can request a download of a set of data using the
:meth:`~icat.client.Client.getData` method::

  >>> query = Query(client, "Datafile", conditions={
  ...     "name": "= 'greet-jdoe.txt'",
  ...     "dataset.name": "= 'greetings'"
  ... })
  >>> df = client.assertedSearch(query)[0]
  >>> data = client.getData([df])
  >>> type(data)
  <class 'http.client.HTTPResponse'>
  >>> data.read().decode('utf8')
  'Hello John!\n'

This method takes a list of investigation, dataset, or datafile
objects as argument.  It returns a :class:`~http.client.HTTPResponse`
object, which is a file like object that we can read the body of the
HTTP response from.  If we requested only one single file, this
response will contain the file content.  If more then a single file is
requested, either by passing multiple files in the argument or by
requesting a dataset having multiple files, IDS will send a zip file
with the requested files::

  >>> from io import BytesIO
  >>> from zipfile import ZipFile
  >>> query = Query(client, "Dataset", conditions={"name": "= 'greetings'"})
  >>> ds = client.assertedSearch(query)[0]
  >>> data = client.getData([ds])
  >>> buffer = BytesIO(data.read())
  >>> with ZipFile(buffer) as zipfile:
  ...     for f in zipfile.namelist():
  ...         print("file name: %s" % f)
  ...         print("content: %r" % zipfile.open(f).read().decode('utf8'))
  ...
  file name: ids/ESNF/12100409-ST/1.1-P/greetings/greet-jdoe.txt
  content: 'Hello John!\n'
  file name: ids/ESNF/12100409-ST/1.1-P/greetings/greet-nbour.txt
  content: 'Hello Nicolas!\n'
  file name: ids/ESNF/12100409-ST/1.1-P/greetings/greet-rbeck.txt
  content: 'Hello Rudolph!\n'

The internal file names in the zip file depend on the IDS storage
plugin and may be different.

Note that it may happen that the files we request are not readily
available because they are archived to tape.  We create this condition
by explicitely requesting IDS to archive our dataset::

  >>> from icat.ids import DataSelection
  >>> selection = DataSelection([ds])
  >>> client.ids.archive(selection)

Note that we needed to resort to a low level call from the IDS client
for that.  This method requires the selected data to be wrapped in a
:class:`~icat.ids.DataSelection` object.  We may also check that
status::

  >>> client.ids.getStatus(selection)
  'ARCHIVED'

If we request the data now, we will get an error from IDS::

  >>> data = client.getData([ds])
  Traceback (most recent call last):
    ...
  icat.exception.IDSDataNotOnlineError: Before putting, getting or deleting a datafile, its dataset has to be restored, restoration requested automatically

As the error message hints, a restoration of the data has been
requested automatically.  So we can just repeat the request again
after a short while::

  >>> client.ids.getStatus(selection)
  'ONLINE'
  >>> data = client.getData([ds])
  >>> len(data.read())
  665

We can ask IDS with the :meth:`~icat.client.Client.prepareData` call
to store a selection of data objects internally for later referral::

  >>> preparedId = client.prepareData(selection)
  >>> preparedId
  'eb0dd942-7ce9-4ea9-b342-ea326edd4dfe'

The return value is a random id.  We can use that preparedId to query
the status or to download the data::

  >>> client.isDataPrepared(preparedId)
  True
  >>> data = client.getData(preparedId)
  >>> buffer = BytesIO(data.read())
  >>> with ZipFile(buffer) as zipfile:
  ...     zipfile.namelist()
  ...
  ['ids/ESNF/12100409-ST/1.1-P/greetings/greet-jdoe.txt', 'ids/ESNF/12100409-ST/1.1-P/greetings/greet-nbour.txt', 'ids/ESNF/12100409-ST/1.1-P/greetings/greet-rbeck.txt']
