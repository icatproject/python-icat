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

  optional arguments:
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
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/jdoe

If we add the option on the command line, it has the expected effect::

  $ python config-custom.py -s myicat_jdoe -o out.txt
  $ cat out.txt
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/jdoe

Alternatively, we may also specify the option in the configuration
file as follows::

  [myicat_jdoe]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  idsurl = https://icat.example.com:8181/ids
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
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/jdoe

But if we pass the flag parameter, it produces a different output::

  $ python config-flag.py -s myicat_jdoe --hide-user-name
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.

Defining sub-commands
---------------------

For some use cases, defining simple configuration variables may not be
flexible enough.  For example, a program might perform several
different functions which each require different kinds of arguments.
In cases like this, programs can split up their functionality into
sub-commands which each take their own set of configuration variables.

To make sub-commands available in your program, simply call the
:meth:`~icat.config.BaseConfig.add_subcommands` method.  Please note
that after calling this method, adding any more subsequent
configuration variables or subcommand variables is not allowed, so
make sure to set up all 'global' configuration variables first before
invoking this method.

Once the sub-commands have been made available, you can call the
:meth:`~icat.config.ConfigSubCmds.add_subconfig` method to register a
new sub-command for your program.  You can then define
sub-command-specific configuration variables using the familiar
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

  optional arguments:
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
  []
  done

Alright, looks like there are no ``User`` objects yet, so let's add a
new one.  We will use the `create` sub-command to do this.  Earlier,
we defined a configuration variable `name` (``-n NAME``) that is
specific to the `create` sub-command.  We can check this by calling::

  $ python config-sub-commands.py create -h
  usage: config-sub-commands.py create [-h] [-n NAME]

  optional arguments:
    -h, --help            show this help message and exit
    -n NAME, --name NAME  name for the new ICAT object

Let's create a new ``User`` object named "Alice".  Note that we must
provide the 'global' configuration variables (`section` and `entity`)
before the sub-command, and the sub-command-specific option (`name`)
after it::

  $ python config-sub-commands.py -s myicat_root -e User create -n Alice
  creating a new User object named Alice...
  done

If we now list the ``User`` objects again, we can see a new object
with name "Alice"::

  $ python config-sub-commands.py -s myicat_root -e User list
  listing existing User objects...
  [(user){
     createId = "simple/root"
     createTime = 2019-11-26 13:00:46+01:00
     id = 1
     modId = "simple/root"
     modTime = 2019-11-26 13:00:46+01:00
     name = "Alice"
   }]
  done

Finally, let's delete this new object using the `delete` sub-command.
To do this, we must specify the sub-command-specific configuration
variable `id` (``-i ID``).  In the above output, we can see that the
object's ID is 1, so we write::

  $ python config-sub-commands.py -s myicat_root -e User delete -i 1
  deleting the User object with ID 1...
  done

