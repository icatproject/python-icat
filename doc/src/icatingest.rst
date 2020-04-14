.. _icatingest:

icatingest
==========


Synopsis
~~~~~~~~

**icatingest** [*standard options*] [-i FILE] [-f FORMAT] [--upload-datafiles] [--datafile-dir DATADIR] [--duplicate OPTION]


Description
~~~~~~~~~~~

.. program:: icatingest

This script reads an ICAT data file and creates all objects found in
an ICAT server.  The format of that file depends on the backend that
can be selected with the :option:`--format` option.


Options
~~~~~~~

.. program:: icatingest

The configuration options may be set in the command line or in a
configuration file (besides :option:`--configfile` and
:option:`--configsection`).  Some options may also be set in the
environment.


Specific Options
................

The following options are specific to icatingest:

.. program:: icatingest

.. option:: -i FILE, --inputfile FILE

    Set the input file name.  If the value `-` is used, the input will
    be read from standard input.  This is also the default.

.. option:: -f FORMAT, --format FORMAT

    Select the backend to use and thus the input file format.  XML
    and YAML backends are available.

.. option:: --upload-datafiles

    If that flag is set, Datafile objects will not be created in the
    ICAT server directly, but a corresponding file will be uploaded to
    IDS instead.

.. option:: --datafile-dir DATADIR

    Directory to search for the files to be uploaded to IDS.  This is
    only relevant if :option:`--upload-datafiles` is set.  The default
    is the current working directory.

.. option:: --duplicate OPTION

    Set the behavior in the case that any object read from the input
    already exists in the ICAT server.  Valid options are:

    **THROW**
        Throw an error.  This is the default.

    **IGNORE**
        Skip the object read from the input.

    **CHECK**
        Compare all attributes from the input object with the already
	existing object in ICAT.  Throw an error of any attribute
	differs.

    **OVERWRITE**
        Overwrite the existing object in ICAT, e.g. update it with all
	attributes set to the values found in the input object.

    If :option:`--upload-datafiles` is set, this option will be
    ignored for Datafile objects which will then always raise an error
    if they already exist.


Standard Options
................

The following options needed to connect the ICAT service are common
for most python-icat scripts:

.. program:: icatingest

.. option:: -h, --help

    Display a help message and exit.

.. option:: -c CONFIGFILE, --configfile CONFIGFILE

    Name of a configuration file.

.. option:: -s SECTION, --configsection SECTION

    Name of a section in the configuration file.  If set, the values
    in this configuration section will be applied to define other
    options.

.. option:: -w URL, --url URL

    URL of the ICAT server.  This should point to the web service
    descriptions.  If the URL has no path component, a default path
    will be added.

.. option:: --idsurl URL

    URL of the IDS server.  This is only relevant if
    :option:`--upload-datafiles` is set.  If the URL has no path
    component, a default path will be added.

.. option:: --no-check-certificate

    Do not verify the ICAT server's TLS certificate.  This is only
    relevant if the URL set with :option:`--url` or :option:`--idsurl`
    uses HTTPS.  It is mostly only useful for connecting a test server
    that does not have a trusted certificate.

.. option:: --http-proxy HTTP_PROXY

    Proxy to use for http requests.

.. option:: --https-proxy HTTPS_PROXY

    Proxy to use for https requests.

.. option:: --no-proxy NO_PROXY

    Comma separated list of exclusions for proxy use.

.. option:: -a AUTH, --auth AUTH

    Name of the authentication plugin to use for login to the ICAT
    server.

.. option:: -u USERNAME, --user USERNAME

    The ICAT user name.

.. option:: -p PASSWORD, --pass PASSWORD

    The user's password.  Will prompt for the password if not set.

.. option:: -P, --prompt-pass

    Prompt for the password.  This is mostly useful to override a
    password set in the configuration file.


Known Issues and Limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The user running this script need to have create permission for all
  objects in the dump file.  In the generic case of restoring the
  entire content on an empty ICAT server, the script must be run by
  the ICAT root user.

* A dump and restore of an ICAT will not preserve the attributes
  :attr:`~icat.entity.Entity.id`,
  :attr:`~icat.entity.Entity.createId`,
  :attr:`~icat.entity.Entity.createTime`,
  :attr:`~icat.entity.Entity.modId`, and
  :attr:`~icat.entity.Entity.modTime` of any object.  As a
  consequence, access rules that are based on the values of these
  attributes will not work after a restore.

* Dealing with duplicates, see :option:`--duplicate`, is only
  supported for single objects.  If the object contains embedded
  related objects in one to many relationships that are to be created
  at once, the only allowed option to deal with duplicates is THROW.


Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. describe:: ICAT_CFG

    Name of a configuration file, see :option:`--configfile`.

.. describe:: ICAT_CFG_SECTION

    Name of a section in the configuration file, see
    :option:`--configsection`.

.. describe:: ICAT_SERVICE

    URL of the ICAT server, see :option:`--url`.

.. describe:: ICAT_DATA_SERVICE

    URL of the IDS server, see :option:`--idsurl`.

.. describe:: http_proxy

    Proxy to use for http requests, see :option:`--http-proxy`.

.. describe:: https_proxy

    Proxy to use for https requests, see :option:`--https-proxy`.

.. describe:: no_proxy

    Exclusions for proxy use, see :option:`--no-proxy`.

.. describe:: ICAT_AUTH

    Name of the authentication plugin, see :option:`--auth`.

.. describe:: ICAT_USER

    ICAT user name, see :option:`--user`.


See also
~~~~~~~~

* Section :ref:`ICAT-data-files` on the structure of the dump files.
* Section :ref:`standard-config-vars` on the standard options.
* The :ref:`icatdump` script.
