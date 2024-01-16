.. _ICAT-data-files:

ICAT data files
===============

ICAT data files provide a way to serialize ICAT content to a flat
file.  These files are read by the :ref:`icatingest` and written by
the :ref:`icatdump` command line scripts respectively.  The program
logic for reading and writing the files is provided by the
:mod:`icat.dumpfile` module.

The actual file format depends on the version of the ICAT schema and
on the backend: python-icat provides backends using XML and YAML.

Logical structure of ICAT data files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a one-to-one correspondence of the objects in the data
file and the corresponding object in ICAT according to the ICAT
schema, including all attributes and relations to other objects.

Data files are partitioned in chunks.  This is done to avoid having
the whole file, e.g. the complete inventory of the ICAT, at once in
memory.  The problem is that objects contain references to other
objects, e.g. Datafiles refer to Datasets, the latter refer to
Investigations, and so forth.  We keep an index of the objects as
cache in order to resolve these references.  But there is a memory
versus time tradeoff: in order to avoid the index to grow beyond
bounds, objects need to be discarded from the index from time to time.
References to objects that can not be resolved from the index need to
be searched from the ICAT server, which of course is expensive.  So
the strategy is as follows: keep all objects from the current chunk in
the index and discard the complete index each time a chunk has been
processed. [#dc]_ This will work fine if objects are mostly
referencing other objects from the same chunk and only a few
references go across chunk boundaries.

Therefore, we want these chunks to be small enough to fit into memory,
but at the same time large enough to keep as many relations between
objects as possible local in a chunk.  It is in the responsibility of
the writer of the data file to create the chunks in this manner.

The objects that get written to the data file and how this file is
organized is controlled by lists of ICAT search expressions or entity
objects, see :meth:`icat.dumpfile.DumpFileWriter.writeobjs`.  There is
some degree of flexibility: an object may include related objects in
an one-to-many relation.  In this case, these related objects should
not be added on their own again.  For instance, you may write User,
Grouping, and UserGroup as separate objects into the file.  In this
case, the UserGroup entries must properly reference related User and
Grouping.  Alternatively you may include the UserGroups in the
corresponding Grouping objects.  In this case, you must not add the
UserGroups again on their own.

Objects related in a many-to-one relation must always be included in
the search expression.  This is also true if the object is
indirectly related to one of the included objects.  In this case,
only a reference to the related object will be included in the data
file.  The related object must have its own entry.

References to ICAT objects and unique keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

References to related objects are encoded in ICAT data files by
reference keys.  There are two kinds of those keys: local keys and
unique keys.

When an ICAT object is defined in the file, it generally defines a
local key at the same time.  Local keys are stored in the object index
and may be used to reference this object from other obejcts in the
same data chunk.  Unique keys can be obtained from an object by
calling :meth:`icat.entity.Entity.getUniqueKey`.  An object can be
searched by its unique key from the ICAT server by calling
:meth:`icat.client.Client.searchUniqueKey`.  As a result, it is
possible to reference an object by its unique key even if the
reference is not in the object index.  All references that go across
chunk boundaries must use unique keys. [#dc]_

Reference keys should be considered as opaque ids.

ICAT data XML files
~~~~~~~~~~~~~~~~~~~

In this section we describe the ICAT data file format using the XML
backend.  Consider the following example:

.. literalinclude:: ../examples/icatdump-simple.xml
   :language: xml

The root element of ICAT data XML files is ``icatdata``.  It may
optionally have one ``head`` subelement and one or more ``data``
subelements.

The ``head`` element will be ignored by :ref:`icatingest`.  It serves
to provide some information on the context of the creation of the data
file, which may be useful for debugging in case of issues.

The content of each ``data`` element is one chunk according to the
logical structure explained above.  The present example contains two
chunks.  Each element within the ``data`` element corresponds to an
ICAT object according to the ICAT schema.  In the present example, the
first chunk contains four User objects and three Grouping objects.
The Groupings include related UserGroups.  The second chunk only
contains one Investigation, including related investigationGroups.

These object elements may have an ``id`` attribute that defines a
local key to reference the object later on.  The subelements of the
object elements correspond to the object's attributes and relations in
the ICAT schema.  All many-to-one relations must be provided and
reference already existing objects, e.g. they must either already have
existed before starting the ingestion or appear earlier in the ICAT
data file than the referencing object, so that they will be created
earlier.  The related object may either be referenced by reference key
using the ``ref`` attribute or by the related object's attribute
values, using XML attributes of the same name.  In the latter case,
the attribute values must uniquely define the related object.

In the present example, consider the first grouping:

.. code-block:: XML

  <grouping id="Grouping_name-investigation=5F10100601=2DST=5Fowner">
    <name>investigation_10100601-ST_owner</name>
    <userGroups>
      <user ref="User_name-db=2Fahau"/>
    </userGroups>
  </grouping>

It includes a related userGroup object that in turn references a
related User.  This User is referenced in the ``ref`` attribute using
a local key defined in the User's ``id`` attribute earlier in the
file.  Another example is how the Investigation references its
Facility:

.. code-block:: XML

  <investigation>
    <!--  ... -->
    <facility ref="Facility_name-ESNF"/>
    <!--  ... -->
  </investigation>

The Facility is not defined in the data file.  It is assumed to exist
in ICAT before ingesting the file.  In this case, it must be
referenced by its unique key.  Alternatively, the Facility could have
been referenced by attribute as in:

.. code-block:: XML

  <investigation>
    <!--  ... -->
    <facility name="ESNF"/>
    <!--  ... -->
  </investigation>

The object elements may include one-to-many relations.  In this case,
the related objects will be created along with the parent in one
single cascading call.  In the present example, the Grouping objects
include their related UserGroup objects.  Note that these UserGroups
include their relation to the User, but not their relation with
Grouping.  The latter relationship is implied by the parent relation
of the object in the file.

As an alternative, the Usergroups could have been added to the file as
separate objects as direct subelements of ``data`` as in:

.. code-block:: XML

  <data>
    <user id="User_name-db=2Fahau">
      <affiliation>Goethe University Frankfurt, Faculty of Philosophy and History</affiliation>
      <email>ahau@example.org</email>
      <familyName>Hau</familyName>
      <fullName>Arnold Hau</fullName>
      <givenName>Arnold</givenName>
      <name>db/ahau</name>
      <orcidId>0000-0002-3263</orcidId>
    </user>
    <grouping id="Grouping_name-investigation=5F10100601=2DST=5Fowner">
      <name>investigation_10100601-ST_owner</name>
    </grouping>
    <userGroup id="UserGroup_user-(name-db=2Fahau)_grouping-(name-investigation=5F10100601=2DST=5Fowner)">
      <grouping ref="Grouping_name-investigation=5F10100601=2DST=5Fowner"/>
      <user ref="User_name-db=2Fahau"/>
    </userGroup>
  </data>

The Investigation in the second chunk in the present example includes
related InvestigationGroups that will be created along with the
Investigation.  The InvestigationGroup objects include a reference to
the corresponding Grouping.  Note that these references go across
chunk boundaries.  Thus, unique keys for the Groupings need to be used
here.

Finally note that the file format also depends on the ICAT schema
version: the present example can only be ingested into ICAT server 5.0
or newer, because the attributes fileCount and fileSize have been
added to Investigation in this version.  With older ICAT versions, it
will fail because the attributes are not defined.

You will find more extensive examples in the source distribution of
python-icat.  The distribution also provides XML Schema Definition
files for the ICAT data XML file format corresponding to various ICAT
schema versions.  Note the these  XML Schema Definition
files are provided for reference only.  The :ref:`icatingest` script
does not validate its input.

ICAT data YAML files
~~~~~~~~~~~~~~~~~~~~

In this section we describe the ICAT data file format using the YAML
backend.  Consider the following example, it corresponds to the same
ICAT content as the XML example above:

.. literalinclude:: ../examples/icatdump-simple.yaml
   :language: yaml

ICAT data YAML files start with a head consisting of a few comment
lines, followed by one or more YAML documents.  YAML documents are
separated by a line containing only ``---``.  The comments in the head
provide some information on the context of the creation of the data
file, which may be useful for debugging in case of issues.

Each YAML document defines one chunk of data according to the logical
structure explained above.  It consists of a mapping having the name
of entity types in the ICAT schema as keys.  The values are in turn
mappings that map object ids as key to ICAT object definitions as
value.  These object ids define local keys that may be used to
reference the respective object later on.  In the present example, the
first chunk contains four User objects and three Grouping objects.
The Groupings include related UserGroups.  The second chunk only
contains one Investigation, including related investigationGroups.

Each of the ICAT object definitions corresponds to an object in the
ICAT schema.  It is again a mapping with the object's attribute and
relation names as keys and corresponding values.  All many-to-one
relations must be provided and reference existing objects, e.g. they
must either already have existed before starting the ingestion or
appear in the same or an earlier YAML document in the ICAT data file.
The values of many-to-one relations are reference keys, either local
keys defined in the same YAML document or unique keys.

The object definitions may include one-to-many relations.  In this
case, the value for the relation name is a list of object definitions
for the related objects.  These related objects will be created along
with the parent in one single cascading call.  In the present example,
the Grouping objects include their related UserGroup objects.  Note
that these UserGroups include their relation to the User, but not
their relation with Grouping.  The latter relationship is implied by
the parent relation of the object in the file.

As an alternative, in the present example, the Usergroups could have
been added to the file as separate objects as in:

.. code-block:: YAML

  ---
  grouping:
    Grouping_name-investigation=5F10100601=2DST=5Fowner:
      name: investigation_10100601-ST_owner
  user:
    User_name-db=2Fahau:
      affiliation: Goethe University Frankfurt, Faculty of Philosophy and History
      email: ahau@example.org
      familyName: Hau
      fullName: Arnold Hau
      givenName: Arnold
      name: db/ahau
      orcidId: 0000-0002-3263
  userGroup:
    UserGroup_user-(name-db=2Fahau)_grouping-(name-investigation=5F10100601=2DST=5Fowner):
      grouping: Grouping_name-investigation=5F10100601=2DST=5Fowner
      user: User_name-db=2Fahau
  ---

Note that the entries in the mappings have no inherent order.  The
:ref:`icatingest` script uses a predefined order to read the ICAT
entity types in order to make sure that referenced objects are created
before any object that may reference them.


.. [#dc] There is one exception: DataCollections don't have a
         uniqueness constraint and can't reliably be searched by
         attributes.  Therefore local keys for DataCollections are
         always kept in the object index and may be used to reference
         them across chunk boundaries.
