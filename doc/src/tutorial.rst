Tutorial
========

This tutorial provides a step by step introduction to the usage of
python-icat.  It intents to give an overview of python-icat's most
noteworthy features.  You need to have python-icat installed to run
the examples.  You also need a running ICAT server and IDS server to
connect to.  Some examples in the tutorial assume to have root access
and modify data, therefore it is not advisable to use a production
ICAT.  Rather setup a dedicated test ICAT to run the tutorial.

During the tutorial you will create some simple Python scripts and
other files in your local file system.  It is advisable to create a
new empty folder for that purpose and change into that::

  $ mkdir python-icat-tutorial
  $ cd python-icat-tutorial

Some of the more advanced tutorial sections will require some example
content in the ICAT server.  You'll need the file `icatdump-5.0.yaml`
to set it up.  This file can be found in the `doc/examples` directory
in the python-icat source distribution.

The tutorial assumes some basic knowledge in programming with Python
as well as some basic understanding of ICAT.  The tutorial contains
the following sections:

.. toctree::
   :maxdepth: 2

   tutorial-hello
   tutorial-config
   tutorial-login
   tutorial-create
   tutorial-edit
   tutorial-search
   tutorial-ids
   tutorial-config-advanced

.. note::
   Throughout this tutorial, we assume the name of the Python
   executable to be just ``python`` and the full path used in the
   interpreter line of scripts to be ``/usr/bin/python``.  It is
   likely that this assumption does not hold in your environment.
   Quite often, a version number is appended to the executable name as
   in ``python3`` or ``python3.11`` and the Python executable might
   reside in another directory in your system.  You may need to adapt
   accordingly.
