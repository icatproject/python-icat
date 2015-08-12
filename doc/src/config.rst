:mod:`icat.config` --- Manage configuration
===========================================

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
    line arguments to switch the value on and off respectively.

.. autoclass:: icat.config.Configuration
    :members:
    :show-inheritance:

.. autoclass:: icat.config.Config
    :members:
    :show-inheritance:
