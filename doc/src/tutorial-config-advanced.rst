Advanced configuration
~~~~~~~~~~~~~~~~~~~~~~

So far, we have relied on the :mod:`icat.config` module to provide
configuration variables for us (such as `url` or `idsurl`).  However,
programs may also define their own custom configuration variables.

Custom configuration variables
------------------------------

Let's add the option to redirect the output of our example program to
a file.  The output file path shall be passed via the command line as
a configuration variable.  To set this up, we can use the
:meth:`~icat.config.BaseConfig.add_variable` method:

.. literalinclude:: ../tutorial/config-custom.py

This adds a new configuration variable `outfile`.  It can be specified
on the command line as ``-o OUTFILE`` or ``--outputfile OUTFILE`` and
it defaults to the string ``-`` if not specified.  We can check this
on the list of available command line options::

  $ python config-custom.py -h
  usage: config-custom.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL]
                          [--idsurl IDSURL] [--no-check-certificate]
                          [--http-proxy HTTP_PROXY] [--https-proxy HTTPS_PROXY]
                          [--no-proxy NO_PROXY] [-a AUTH] [-u USERNAME] [-P]
                          [-p PASSWORD] [-o OUTFILE]

  options:
    -h, --help            show this help message and exit
    -c CONFIGFILE, --configfile CONFIGFILE
                          config file
    -s SECTION, --configsection SECTION
                          section in the config file
    -w URL, --url URL     URL to the web service description
    --idsurl IDSURL       URL to the ICAT Data Service
    --no-check-certificate
                          don't verify the server certificate
    --http-proxy HTTP_PROXY
                          proxy to use for http requests
    --https-proxy HTTPS_PROXY
                          proxy to use for https requests
    --no-proxy NO_PROXY   list of exclusions for proxy use
    -a AUTH, --auth AUTH  authentication plugin
    -u USERNAME, --user USERNAME
                          username
    -P, --prompt-pass     prompt for the password
    -p PASSWORD, --pass PASSWORD
                          password
    -o OUTFILE, --outputfile OUTFILE
                          output file name or '-' for stdout

This new option is optional, so the program can be used as before::

  $ python config-custom.py -s myicat_jdoe
  Login to https://icat.example.com:8181 was successful.
  User: db/jdoe

If we add the option on the command line, it has the expected effect::

  $ python config-custom.py -s myicat_jdoe -o out.txt
  $ cat out.txt
  Login to https://icat.example.com:8181 was successful.
  User: db/jdoe

Alternatively, we may also specify the option in the configuration
file as follows::

  [myicat_jdoe]
  url = https://icat.example.com:8181
  auth = db
  username = jdoe
  password = secret
  idsurl = https://icat.example.com:8181
  #checkCert = No
  outfile = out.txt

Flag configuration variables
----------------------------

Instead of passing a string value to our program, we can also define
different variable types using the `type` parameter.  Among other
things, this allows us to pass boolean/flag parameters.  Let's add
another configuration variable to our example program that lets us
control the output via a flag:

.. literalinclude:: ../tutorial/config-flag.py

If we call our program normally, we get the same output as before::

  $ python config-flag.py -s myicat_jdoe
  Login to https://icat.example.com:8181 was successful.
  User: db/jdoe

But if we pass the flag parameter, it produces a different output::

  $ python config-flag.py -s myicat_jdoe --hide-user-name
  Login to https://icat.example.com:8181 was successful.

A flag type configuration variable also adds a negated form of the
command line flag::

  $ python config-flag.py -s myicat_jdoe --no-hide-user-name
  Login to https://icat.example.com:8181 was successful.
  User: db/jdoe

This may look somewhat pointless at first glance as it only affirms
the default.  It becomes useful if we set this flag in the
configuration file as in::

  [myicat_jdoe]
  url = https://icat.example.com:8181
  auth = db
  username = jdoe
  password = secret
  idsurl = https://icat.example.com:8181
  #checkCert = No
  hide = true

In that case we can override this setting on the command line with
``--no-hide-user-name``.

Defining sub-commands
---------------------

Many programs split up their functionality into sub-commands.  For
instance, the ``git`` program can be called as ``git clone``, ``git
checkout``, ``git commit``, and so on.  In general, each sub-command
will take their own set of configuration variables.

You can create programs like this and manage the configuration of each
sub-command with :mod:`icat.config` using the
:meth:`~icat.config.BaseConfig.add_subcommands` method.  It adds a
special :class:`~icat.config.ConfigSubCmds` configuration variable
representing the sub-command.  This object provides the
:meth:`~icat.config.ConfigSubCmds.add_subconfig` method to register a
new sub-command value.  On the sub-config object in turn you can then
define specific configuration variables using the familiar
:meth:`~icat.config.BaseConfig.add_variable` method.

To put it all together, consider the following example program:

.. literalinclude:: ../tutorial/config-sub-commands.py

If we check the available commands for the above program, our three
sub-commands should be listed::

  $ python config-sub-commands.py -h
  usage: config-sub-commands.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL]
                                [--idsurl IDSURL] [--no-check-certificate]
                                [--http-proxy HTTP_PROXY]
                                [--https-proxy HTTPS_PROXY]
                                [--no-proxy NO_PROXY] [-a AUTH] [-u USERNAME]
                                [-P] [-p PASSWORD] [-e {User,Study}]
                                {list,create,delete} ...

  options:
    -h, --help            show this help message and exit
    -c CONFIGFILE, --configfile CONFIGFILE
                          config file
    -s SECTION, --configsection SECTION
                          section in the config file
    -w URL, --url URL     URL to the web service description
    --idsurl IDSURL       URL to the ICAT Data Service
    --no-check-certificate
                          don't verify the server certificate
    --http-proxy HTTP_PROXY
                          proxy to use for http requests
    --https-proxy HTTPS_PROXY
                          proxy to use for https requests
    --no-proxy NO_PROXY   list of exclusions for proxy use
    -a AUTH, --auth AUTH  authentication plugin
    -u USERNAME, --user USERNAME
                          username
    -P, --prompt-pass     prompt for the password
    -p PASSWORD, --pass PASSWORD
                          password
    -e {User,Study}, --entity {User,Study}
                          an entity from the ICAT schema

  subcommands:
    {list,create,delete}
      list                list existing ICAT objects
      create              create a new ICAT object
      delete              delete an ICAT object

This looks good.  Let's try calling our program with the `list`
sub-command.  Of course we must also provide a `section` from our
config file (``-s SECTION``) as well as the `entity` variable (``-e
{User,Study}``) we defined earlier::

  $ python config-sub-commands.py -s myicat_root -e User list
  listing existing User objects...
  [(user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 1
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "University of Ravenna, Institute of Modern History"
     email = "acord@example.org"
     familyName = "Cordus"
     fullName = "Aelius Cordus"
     givenName = "Aelius"
     name = "db/acord"
     orcidId = "0000-0002-3262"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 2
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "Goethe University Frankfurt, Faculty of Philosophy and History"
     email = "ahau@example.org"
     familyName = "Hau"
     fullName = "Arnold Hau"
     givenName = "Arnold"
     name = "db/ahau"
     orcidId = "0000-0002-3263"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 3
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "Université Paul-Valéry Montpellier 3"
     email = "jbotu@example.org"
     familyName = "Botul"
     fullName = "Jean-Baptiste Botul"
     givenName = "Jean-Baptiste"
     name = "db/jbotu"
     orcidId = "0000-0002-3264"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 4
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     email = "jdoe@example.org"
     familyName = "Doe"
     fullName = "John Doe"
     givenName = "John"
     name = "db/jdoe"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 5
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "University of Nancago"
     email = "nbour@example.org"
     familyName = "Bourbaki"
     fullName = "Nicolas Bourbaki"
     givenName = "Nicolas"
     name = "db/nbour"
     orcidId = "0000-0002-3266"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 6
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "Kaiser-Wilhelms-Akademie für das militärärztliche Bildungswesen"
     email = "rbeck@example.org"
     familyName = "Beck-Dülmen"
     fullName = "Rudolph Beck-Dülmen"
     givenName = "Rudolph"
     name = "db/rbeck"
     orcidId = "0000-0002-3267"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 7
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "Data Ingester"
     name = "simple/dataingest"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 8
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "IDS reader"
     name = "simple/idsreader"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 9
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "Pub reader"
     name = "simple/pubreader"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 10
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "Root"
     name = "simple/root"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 11
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "User Office"
     name = "simple/useroffice"
   }]
  done

We see the users defined in the example content created in the
previous tutorial sections.  Let's add a new user.  We will use the
`create` sub-command to do this.  Earlier, we defined a configuration
variable `name` (``-n NAME``) that is specific to the `create`
sub-command.  We can check this by calling::

  $ python config-sub-commands.py create -h
  usage: config-sub-commands.py create [-h] [-n NAME]

  options:
    -h, --help            show this help message and exit
    -n NAME, --name NAME  name for the new ICAT object

Let's create a new ``User`` object named "db/alice".  Note that we must
provide the 'global' configuration variables (`section` and `entity`)
before the sub-command, and the sub-command-specific option (`name`)
after it::

  $ python config-sub-commands.py -s myicat_root -e User create -n db/alice
  creating a new User object named db/alice...
  done

If we now list the ``User`` objects again, we can see a new object
with name "db/alice"::

  $ python config-sub-commands.py -s myicat_root -e User list
  listing existing User objects...
  [(user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 1
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "University of Ravenna, Institute of Modern History"
     email = "acord@example.org"
     familyName = "Cordus"
     fullName = "Aelius Cordus"
     givenName = "Aelius"
     name = "db/acord"
     orcidId = "0000-0002-3262"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 2
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "Goethe University Frankfurt, Faculty of Philosophy and History"
     email = "ahau@example.org"
     familyName = "Hau"
     fullName = "Arnold Hau"
     givenName = "Arnold"
     name = "db/ahau"
     orcidId = "0000-0002-3263"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 3
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "Université Paul-Valéry Montpellier 3"
     email = "jbotu@example.org"
     familyName = "Botul"
     fullName = "Jean-Baptiste Botul"
     givenName = "Jean-Baptiste"
     name = "db/jbotu"
     orcidId = "0000-0002-3264"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 4
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     email = "jdoe@example.org"
     familyName = "Doe"
     fullName = "John Doe"
     givenName = "John"
     name = "db/jdoe"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 5
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "University of Nancago"
     email = "nbour@example.org"
     familyName = "Bourbaki"
     fullName = "Nicolas Bourbaki"
     givenName = "Nicolas"
     name = "db/nbour"
     orcidId = "0000-0002-3266"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 6
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     affiliation = "Kaiser-Wilhelms-Akademie für das militärärztliche Bildungswesen"
     email = "rbeck@example.org"
     familyName = "Beck-Dülmen"
     fullName = "Rudolph Beck-Dülmen"
     givenName = "Rudolph"
     name = "db/rbeck"
     orcidId = "0000-0002-3267"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 7
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "Data Ingester"
     name = "simple/dataingest"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 8
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "IDS reader"
     name = "simple/idsreader"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 9
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "Pub reader"
     name = "simple/pubreader"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 10
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "Root"
     name = "simple/root"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 15:32:07+01:00
     id = 11
     modId = "simple/root"
     modTime = 2025-12-01 15:32:07+01:00
     fullName = "User Office"
     name = "simple/useroffice"
   }, (user){
     createId = "simple/root"
     createTime = 2025-12-01 16:35:16+01:00
     id = 12
     modId = "simple/root"
     modTime = 2025-12-01 16:35:16+01:00
     name = "db/alice"
   }]
  done

Finally, let's delete this new object using the `delete` sub-command.
To do this, we must specify the sub-command-specific configuration
variable `id` (``-i ID``).  In the above output, we can see that the
object's ID is 12, so we write::

  $ python config-sub-commands.py -s myicat_root -e User delete -i 12
  deleting the User object with ID 12...
  done

Preset configuration values in the program
------------------------------------------

It is possible to preset the value for configuration variables in the
program, using the `preset` keyword argument to
:class:`~icat.config.Config`.  Consider the following example program:

.. literalinclude:: ../tutorial/config-preset.py

You can call this as follows::

  $ python config-preset.py
  Login to https://icat.example.com:8181 was successful.
  User: simple/root

Note that we did not specify the configuration section on the command
line, yet the program picked the configuration values from the
`myicat_root` section in the configuration file.  Setting values using
the `preset` keyword argument has a similar effect as setting a
default for the respective configuration variable.  But it also allows
to override the default for configuration variables that are
predefined by :mod:`icat.config`.

We can still override the preset configuration variable in the command
line::

  $ python config-preset.py -s myicat_nbour
  Login to https://icat.example.com:8181 was successful.
  User: db/nbour
