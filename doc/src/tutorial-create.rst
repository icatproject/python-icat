Creating Stuff in the ICAT Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ICAT server is pretty useless if it is void of content.  So lets
start creating some objects.

We could do it by writing and running a small Python script each time
as in the last sections.  But python-icat may also be used
interactively at the Python prompt, so lets try this out::

  $ python -i login.py -s myicat_root
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/root
  >>> client.search("SELECT f FROM Facility f")
  []

The ``-i`` command line option tells Python to enter interactive mode
after executing the ``login.py`` script from last section.

Creating simple objects
-----------------------

The :meth:`~icat.client.Client.search` result shows that there is no
``Facility`` object in ICAT.  Let's create one.  In the same session
type::

  >>> f1 = client.new("facility")
  >>> f1.name = "Test1"
  >>> f1.fullName = "Facility 1"
  >>> f1.id = client.create(f1)

The :meth:`~icat.client.Client.new` method instantiates a new
``Facility`` object locally in the client.  We set some of the
attributes of this new object.  Finally, we call
:meth:`~icat.client.Client.create` to create it in the ICAT server.
The return value is the id of the new ``Facility`` object in ICAT.
The result can be verified by repeating the search from above::

  >>> client.search("SELECT f FROM Facility f")
  [(facility){
     createId = "simple/root"
     createTime = 2016-11-07 14:34:08+00:00
     id = 1
     modId = "simple/root"
     modTime = 2016-11-07 14:34:08+00:00
     fullName = "Facility 1"
     name = "Test1"
   }]

The same result could also have been obtained slightly differently:
the :meth:`~icat.client.Client.new` method optionally accepts keyword
arguments to set the attributes of the new entity object.
Furthermore, the entity object itself also has a
:meth:`~icat.entity.Entity.create` method to create this object in the
ICAT server.  We thus could achieve the same as above like this::

  >>> f2 = client.new("facility", name="Test2", fullName="Facility 2")
  >>> f2.create()

To verify the result, we check again::

  >>> client.search("SELECT f FROM Facility f")
  [(facility){
     createId = "simple/root"
     createTime = 2016-11-07 14:34:08+00:00
     id = 1
     modId = "simple/root"
     modTime = 2016-11-07 14:34:08+00:00
     fullName = "Facility 1"
     name = "Test1"
   }, (facility){
     createId = "simple/root"
     createTime = 2016-11-07 14:34:26+00:00
     id = 2
     modId = "simple/root"
     modTime = 2016-11-07 14:34:26+00:00
     fullName = "Facility 2"
     name = "Test2"
   }]

Relationships to other objects
------------------------------

Most objects in the ICAT are related to other objects.  Consider the
following example::

  >>> pt1 = client.new("parameterType")
  >>> pt1.name = "Test parameter type 1"
  >>> pt1.units = "pct"
  >>> pt1.valueType = "NUMERIC"
  >>> pt1.facility = f1
  >>> pt1.create()

The ``ParameterType`` has a many to one relationship to a
``Facility``.  This relationship is established by setting the
corresponding attribute in the ``ParameterType`` object before
creating it in the ICAT.  The ``Facility`` must already exist at this
point.  In this example we assumed to be still in the same session
from above so that the variable ``f1`` still contains the facility
created before.

On the other hand, there is also a one to many relationship between
``ParameterType`` and ``PermissibleStringValue`` in the ICAT schema.
Let's create a ``ParameterType`` with string values::

  >>> pt2 = client.new("parameterType")
  >>> pt2.name = "Test parameter type 2"
  >>> pt2.units = "N/A"
  >>> pt2.valueType = "STRING"
  >>> pt2.facility = f1
  >>> for v in ["buono", "brutto", "cattivo"]:
  ...     psv = client.new("permissibleStringValue", value=v)
  ...     pt2.permissibleStringValues.append(psv)
  ...
  >>> pt2.create()

The ``permissibleStringValues`` attribute of ``ParameterType`` is a
list.  We may add new ``PermissibleStringValue`` instances to this
list before creating the object.  The ``PermissibleStringValue``
instances should not yet exist in ICAT at this point, they will be
created together with the ``ParameterType`` object.

We can verify this by searching for the newly created objects::

  >>> query = "SELECT pt FROM ParameterType pt INCLUDE pt.facility, pt.permissibleStringValues"
  >>> client.search(query)
  [(parameterType){
     createId = "simple/root"
     createTime = 2016-11-07 15:50:44+00:00
     id = 1
     modId = "simple/root"
     modTime = 2016-11-07 15:50:44+00:00
     applicableToDataCollection = False
     applicableToDatafile = False
     applicableToDataset = False
     applicableToInvestigation = False
     applicableToSample = False
     enforced = False
     facility =
        (facility){
           createId = "simple/root"
           createTime = 2016-11-07 14:34:08+00:00
           id = 1
           modId = "simple/root"
           modTime = 2016-11-07 14:34:08+00:00
           fullName = "Facility 1"
           name = "Test1"
        }
     name = "Test parameter type 1"
     units = "pct"
     valueType = "NUMERIC"
     verified = False
   }, (parameterType){
     createId = "simple/root"
     createTime = 2016-11-07 16:00:21+00:00
     id = 2
     modId = "simple/root"
     modTime = 2016-11-07 16:00:21+00:00
     applicableToDataCollection = False
     applicableToDatafile = False
     applicableToDataset = False
     applicableToInvestigation = False
     applicableToSample = False
     enforced = False
     facility =
        (facility){
           createId = "simple/root"
           createTime = 2016-11-07 14:34:08+00:00
           id = 1
           modId = "simple/root"
           modTime = 2016-11-07 14:34:08+00:00
           fullName = "Facility 1"
           name = "Test1"
        }
     name = "Test parameter type 2"
     permissibleStringValues[] =
        (permissibleStringValue){
           createId = "simple/root"
           createTime = 2016-11-07 16:00:21+00:00
           id = 1
           modId = "simple/root"
           modTime = 2016-11-07 16:00:21+00:00
           value = "brutto"
        },
        (permissibleStringValue){
           createId = "simple/root"
           createTime = 2016-11-07 16:00:21+00:00
           id = 2
           modId = "simple/root"
           modTime = 2016-11-07 16:00:21+00:00
           value = "cattivo"
        },
        (permissibleStringValue){
           createId = "simple/root"
           createTime = 2016-11-07 16:00:21+00:00
           id = 3
           modId = "simple/root"
           modTime = 2016-11-07 16:00:21+00:00
           value = "buono"
        },
     units = "N/A"
     valueType = "STRING"
     verified = False
   }]

As expected, we get a list of two ``ParameterType`` objects as result,
one of them related to a couple of ``PermissibleStringValue`` objects
that have been created at the same time as the related
``ParameterType`` object.

Access rules
------------

Until now, we connected the ICAT server as the ``root`` user.  Let's
try what happens if we choose another user::

  $ python -i login.py -s myicat_jdoe
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/jdoe
  >>> client.search("SELECT pt FROM ParameterType pt INCLUDE pt.facility")
  []

We can't get any of the objects created above from ICAT.  The reason
is that we don't have the permission to access these objects.  ICAT
has a default deny access policy: only the ``root`` user has read and
write access to everything, all other users get only access, if there
is a rule that explicitely allows it.

Let's add some rules to allow public read access to some object
types.  Connect again as ``root`` and enter::

  $ python -i login.py -s myicat_root
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/root
  >>> publicTables = [ "Application", "DatafileFormat", "DatasetType",
  ...                  "Facility", "FacilityCycle", "Instrument",
  ...                  "InvestigationType", "ParameterType",
  ...                  "PermissibleStringValue", "SampleType", ]
  >>> queries = [ "SELECT o FROM %s o" % t for t in publicTables ]
  >>> client.createRules("R", queries)
  [1L, 2L, 3L, 4L, 5L, 6L, 7L, 8L, 9L, 10L]

The :meth:`~icat.client.Client.createRules` takes an access mode and a
list of search queries (and optionally a group) as arguments.  It will
add rules the allow access to all objects that are yield by a search
for any of the queries.  The access mode is ``"R"`` for read access in
this example.  :meth:`~icat.client.Client.createRules` is a
convenience method in python-icat roughly equivalent to::

  >>> rules = []
  >>> for w in queries:
  ...     r = client.new("rule", crudFlags="R", what=w)
  ...     rules.append(r)
  ...
  >>> client.createMany(rules)

If we now try again to search for the objects as normal user, we get::

  $ python -i login.py -s myicat_jdoe
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/jdoe
  >>> client.search("SELECT pt FROM ParameterType pt INCLUDE pt.facility")
  [(parameterType){
     createId = "simple/root"
     createTime = 2016-11-07 15:50:44+00:00
     id = 1
     modId = "simple/root"
     modTime = 2016-11-07 15:50:44+00:00
     applicableToDataCollection = False
     applicableToDatafile = False
     applicableToDataset = False
     applicableToInvestigation = False
     applicableToSample = False
     enforced = False
     facility =
        (facility){
           createId = "simple/root"
           createTime = 2016-11-07 14:34:08+00:00
           id = 1
           modId = "simple/root"
           modTime = 2016-11-07 14:34:08+00:00
           fullName = "Facility 1"
           name = "Test1"
        }
     name = "Test parameter type 1"
     units = "pct"
     valueType = "NUMERIC"
     verified = False
   }, (parameterType){
     createId = "simple/root"
     createTime = 2016-11-07 16:00:21+00:00
     id = 2
     modId = "simple/root"
     modTime = 2016-11-07 16:00:21+00:00
     applicableToDataCollection = False
     applicableToDatafile = False
     applicableToDataset = False
     applicableToInvestigation = False
     applicableToSample = False
     enforced = False
     facility =
        (facility){
           createId = "simple/root"
           createTime = 2016-11-07 14:34:08+00:00
           id = 1
           modId = "simple/root"
           modTime = 2016-11-07 14:34:08+00:00
           fullName = "Facility 1"
           name = "Test1"
        }
     name = "Test parameter type 2"
     units = "N/A"
     valueType = "STRING"
     verified = False
   }]
