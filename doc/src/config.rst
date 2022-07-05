:mod:`icat.config` --- Manage configuration
===========================================

.. py:module:: icat.config

This module reads configuration variables from different sources, such
as command line arguments, environment variables, and configuration
files.  A set of configuration variables that any ICAT client program
typically needs is predefined.  Custom configuration variables may be
added.  The main class that client programs interact with is
:class:`icat.config.Config`.

.. data:: icat.config.cfgdirs

    Search path for the configuration file.  The value depends on the
    operating system.

.. autodata:: icat.config.cfgfile

.. autodata:: icat.config.defaultsection

.. autofunction:: icat.config.boolean

.. data:: icat.config.flag

    Variant of :func:`icat.config.boolean` that defines two command
    line arguments to switch the value on and off respectively.  May
    be passed as type to :meth:`icat.config.BaseConfig.add_variable`.

.. autofunction:: icat.config.cfgpath

.. autoclass:: icat.config.ConfigVariable
    :members:
    :show-inheritance:

.. autoclass:: icat.config.ConfigSubCmds
    :members:
    :show-inheritance:

.. autoclass:: icat.config.Configuration
    :members:
    :show-inheritance:

.. autoclass:: icat.config.BaseConfig
    :show-inheritance:

    Class attributes (read only):

    .. attribute:: ReservedVariables = ['credentials']

        Reserved names of configuration variables.

    Instance methods:

    .. automethod:: icat.config.BaseConfig.add_variable

    .. automethod:: icat.config.BaseConfig.add_subcommands

.. autoclass:: icat.config.Config
    :show-inheritance:

    Instance attributes (read only):

    .. attribute:: client

        The :class:`icat.client.Client` object initialized according to
	the configuration.  This is also the first element in the
	return value from :meth:`getconfig`.

    .. attribute:: client_kwargs

        The keyword arguments that have been passed to the constructor
        of :attr:`client`.

    Instance methods:

    .. automethod:: icat.config.Config.getconfig

.. autoclass:: icat.config.SubConfig
    :members:
    :show-inheritance:


.. _standard-config-vars:

Predefined configuration variables
----------------------------------

The constructor of :class:`icat.config.Config` sets up the following
set of configuration variables that an ICAT client typically needs:

  `configFile`
    Paths of the configuration files to read.  The default is a list
    of standard paths that depends on the operating system.  If a
    value is provided, it must be a single path.  The value that is
    set in this variable after configuration is a list of
    :class:`~pathlib.Path` objects of the files that have successfully
    been read.

  `configSection`
    Name of the section in the configuration file to apply.  If
    not set, no values will be read from the configuration file.

  `url`
    URL of the web service description of the ICAT server.

  `idsurl`
    URL of the ICAT Data Service.

  `checkCert`
    Verify the server certificate for HTTPS connections.

  `http_proxy`
    Proxy to use for HTTP requests.

  `https_proxy`
    Proxy to use for HTTPS requests.

  `no_proxy`
    Comma separated list of domain extensions proxy should not be
    used for.

  `auth`
    Name of the authentication plugin to use for login.

  `username`
    The ICAT user name.

  `password`
    The user's password.  Will prompt for the password if not set.

  `promptPass`
    Prompt for the password.

A few derived variables are also set in
:meth:`icat.config.Config.getconfig`:

  `credentials`
    contains the credentials needed for the indicated authenticator
    (username and password if authenticator information is not
    available) suitable to be passed to :meth:`icat.client.Client.login`.

The command line arguments, environment variables, and default values
for the configuration variables are as follows:

+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| Name            | Command line                | Environment           | Default        | Mandatory | Notes        |
+=================+=============================+=======================+================+===========+==============+
| `configFile`    | ``-c``, ``--configfile``    | ``ICAT_CFG``          | depends        | no        | \(1)         |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `configSection` | ``-s``, ``--configsection`` | ``ICAT_CFG_SECTION``  | :const:`None`  | no        |              |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `url`           | ``-w``, ``--url``           | ``ICAT_SERVICE``      |                | yes       |              |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `idsurl`        | ``--idsurl``                | ``ICAT_DATA_SERVICE`` | :const:`None`  | depends   | \(2)         |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `checkCert`     | ``--check-certificate``,    |                       | :const:`True`  | no        |              |
|                 | ``--no-check-certificate``  |                       |                |           |              |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `http_proxy`    | ``--http-proxy``            | ``http_proxy``        | :const:`None`  | no        |              |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `https_proxy`   | ``--https-proxy``           | ``https_proxy``       | :const:`None`  | no        |              |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `no_proxy`      | ``--no-proxy``              | ``no_proxy``          | :const:`None`  | no        |              |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `auth`          | ``-a``, ``--auth``          | ``ICAT_AUTH``         |                | yes       | \(3)         |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `username`      | ``-u``, ``--user``          | ``ICAT_USER``         |                | yes       | \(3),(4)     |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `password`      | ``-p``, ``--pass``          |                       | interactive    | yes       | \(3),(4),(5) |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+
| `promptPass`    | ``-P``, ``--prompt-pass``   |                       | :const:`False` | no        | \(3),(4),(5) |
+-----------------+-----------------------------+-----------------------+----------------+-----------+--------------+

Mandatory means that an error will be raised in
:meth:`icat.config.Config.getconfig` if no value is found for the
configuration variable in question.

Notes:

1. The default value for `configFile` depends on the operating system.

2. The configuration variable `idsurl` will not be set up at all, or
   be set up as a mandatory, or as an optional variable, if the `ids`
   argument to the constructor of :class:`icat.config.Config` is set
   to :const:`False`, to "mandatory", or to "optional" respectively.

3. If the argument `needlogin` to the constructor of
   :class:`icat.config.Config` is set to :const:`False`, the
   configuration variables `auth`, `username`, `password`,
   `promptPass`, and `credentials` will be left out.

4. If the ICAT server supports the
   :meth:`icat.client.Client.getAuthenticatorInfo` API call
   (icat.server 4.9.0 and newer), the server will be queried about the
   credentials required for the authenticator indicated by the value
   of `auth`.  The corresponding variables will be setup in the place
   of `username` and `password`.  The variable `promptPass` will be
   setup only if any of the credentials is marked as hidden in the
   authenticator information.

5. The user will be prompted for the password if `promptPass` is
   :const:`True`, if no `password` is provided in the command line or
   the configuration file, or if the `username`, but not the
   `password` has been provided by command line arguments.  This
   applies accordingly to credentials marked as hidden if
   authenticator information is available from the server.

If the argument `defaultvars` to the constructor of
:class:`icat.config.Config` is set to :const:`False`, no default
configuration variables other then `configFile` and `configSection`
will be defined.  The configuration mechanism is still intact.  In
particular, custom configuration variables may be defined and reading
the configuration file still works.
