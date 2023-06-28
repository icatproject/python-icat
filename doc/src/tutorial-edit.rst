Working with objects in the ICAT server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the previous section of this tutorial, we created two ``Facility``
objects::

  $ python -i login.py -s myicat_root
  Login to https://icat.example.com:8181 was successful.
  User: simple/root
  >>> client.search("SELECT f FROM Facility f")
  [(facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:39:26+02:00
     id = 1
     modId = "simple/root"
     modTime = 2023-06-28 10:39:26+02:00
     fullName = "Facility 1"
     name = "Fac1"
   }, (facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:41:08+02:00
     id = 2
     modId = "simple/root"
     modTime = 2023-06-28 10:41:08+02:00
     fullName = "Facility 2"
     name = "Fac2"
   }]

Let's see what we can do with these objects.

Editing the attributes of objects
---------------------------------

We can edit the attributes of existing objects by assigning values to
the corresponding :class:`~icat.entity.Entity` object.  To write these
changes back into ICAT, we can either call the
:meth:`icat.client.Client.update()` method, or simply invoke the
object's own :meth:`~icat.entity.Entity.update()` method instead.

Let's loop over our ``Facility`` objects to add some new attributes
and to edit existing ones::

  >>> for facility in client.search("SELECT f FROM Facility f"):
  ...     facility.description = "An example facility"
  ...     facility.daysUntilRelease = 1826
  ...     facility.fullName = "%s Facility" % facility.name
  ...     client.update(facility)
  ...

We can verify the changes by performing another search::

  >>> client.search("SELECT f FROM Facility f")
  [(facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:39:26+02:00
     id = 1
     modId = "simple/root"
     modTime = 2023-06-28 11:25:27+02:00
     daysUntilRelease = 1826
     description = "An example facility"
     fullName = "Fac1 Facility"
     name = "Fac1"
   }, (facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:41:08+02:00
     id = 2
     modId = "simple/root"
     modTime = 2023-06-28 11:25:27+02:00
     daysUntilRelease = 1826
     description = "An example facility"
     fullName = "Fac2 Facility"
     name = "Fac2"
   }]

To remove a particular attribute value, we usually just have to assign
:const:`None` to it::

  >>> for facility in client.search("SELECT f FROM Facility f"):
  ...     facility.description = None
  ...     facility.update()
  ...

If we search again now, the descriptions are gone::

  >>> client.search("SELECT f FROM Facility f")
  [(facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:39:26+02:00
     id = 1
     modId = "simple/root"
     modTime = 2023-06-28 11:26:31+02:00
     daysUntilRelease = 1826
     fullName = "Fac1 Facility"
     name = "Fac1"
   }, (facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:41:08+02:00
     id = 2
     modId = "simple/root"
     modTime = 2023-06-28 11:26:31+02:00
     daysUntilRelease = 1826
     fullName = "Fac2 Facility"
     name = "Fac2"
   }]

Copying objects
---------------

By calling the :meth:`~icat.entity.Entity.copy` method on an existing
object, we can create a new object that has all attributes set to a
copy of the corresponding values of the original object.  The
relations are copied by reference, i.e. the original and the copy
refer to the same related object.

To demonstrate this, we use one of the ``Facility`` objects we created
earlier, including its referenced ``ParameterType`` objects::

  >>> fac = client.get("Facility f INCLUDE f.parameterTypes", 1)
  >>> print(fac)
  (facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:39:26+02:00
     id = 1
     modId = "simple/root"
     modTime = 2023-06-28 11:26:31+02:00
     daysUntilRelease = 1826
     fullName = "Fac1 Facility"
     name = "Fac1"
     parameterTypes[] =
        (parameterType){
           createId = "simple/root"
           createTime = 2023-06-28 10:43:06+02:00
           id = 1
           modId = "simple/root"
           modTime = 2023-06-28 10:43:06+02:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Test parameter type 1"
           units = "pct"
           valueType = "NUMERIC"
           verified = False
        },
        (parameterType){
           createId = "simple/root"
           createTime = 2023-06-28 10:44:28+02:00
           id = 2
           modId = "simple/root"
           modTime = 2023-06-28 10:44:28+02:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Test parameter type 2"
           units = "N/A"
           valueType = "STRING"
           verified = False
        },
   }

Now we create a copy of this object and modify its attributes.  The
attributes of the original object remain unchanged.  However, any
changes to the referenced ``ParameterType`` objects are reflected in
both the copy and the original::

  >>> facc = fac.copy()
  >>> print(facc.name)
  Fac1
  >>> print(facc.parameterTypes[0].name)
  Test parameter type 1
  >>> facc.name = "Fac0"
  >>> facc.parameterTypes[0].name = "Test parameter type 0"
  >>> print(fac.name)
  Fac1
  >>> print(fac.parameterTypes[0].name)
  Test parameter type 0

When working with objects from ICAT, it can be a bit cumbersome to
keep the (possibly large) tree of related objects in local memory.  If
you only need to keep the object's attributes, you can use the
:meth:`~icat.entity.Entity.truncateRelations` method to delete all
references to other objects from this object.  Note that this is a
local operation on the object in the client only.  It does neither
affect the corresponding object at the ICAT server, nor any copies of
the object::

  >>> fac.truncateRelations()
  >>> print(fac)
  (facility){
     createId = "simple/root"
     createTime = 2023-06-28 10:39:26+02:00
     id = 1
     modId = "simple/root"
     modTime = 2023-06-28 11:26:31+02:00
     daysUntilRelease = 1826
     fullName = "Fac1 Facility"
     name = "Fac1"
   }
  >>> print(facc)
  (facility){
     createId = None
     createTime = None
     id = 1
     modId = None
     modTime = None
     daysUntilRelease = 1826
     description = None
     fullName = "Fac1 Facility"
     name = "Fac0"
     parameterTypes[] =
        (parameterType){
           createId = "simple/root"
           createTime = 2023-06-28 10:43:06+02:00
           id = 1
           modId = "simple/root"
           modTime = 2023-06-28 10:43:06+02:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Test parameter type 0"
           units = "pct"
           valueType = "NUMERIC"
           verified = False
        },
        (parameterType){
           createId = "simple/root"
           createTime = 2023-06-28 10:44:28+02:00
           id = 2
           modId = "simple/root"
           modTime = 2023-06-28 10:44:28+02:00
           applicableToDataCollection = False
           applicableToDatafile = False
           applicableToDataset = True
           applicableToInvestigation = False
           applicableToSample = False
           enforced = False
           name = "Test parameter type 2"
           units = "N/A"
           valueType = "STRING"
           verified = False
        },
     url = None
   }
