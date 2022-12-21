#! /usr/bin/python

import icat
import icat.config

config = icat.config.Config(ids="optional")

# add a global configuration variable 'entity' common for all sub-commands
config.add_variable("entity", ("-e", "--entity"),
                    dict(help="an entity from the ICAT schema",
                         choices=["User", "Study"]))

# add the configuration variable representing the sub-commands
subcmds = config.add_subcommands("mode")

# register three possible values for the sub-commands {list,create,delete}
subconfig_list = subcmds.add_subconfig("list",
                                       dict(help="list existing ICAT objects"))
subconfig_create = subcmds.add_subconfig("create",
                                         dict(help="create a new ICAT object"))
subconfig_delete = subcmds.add_subconfig("delete",
                                         dict(help="delete an ICAT object"))

# add two additional configuration variables 'name' and 'id' that are
# specific to the 'create' and 'delete' sub-commands respectively.
subconfig_create.add_variable("name", ("-n", "--name"),
                              dict(help="name for the new ICAT object"))
subconfig_delete.add_variable("id", ("-i", "--id"),
                              dict(help="ID of the ICAT object"))

client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

# check which sub-command (mode) was called
if conf.mode.name == "list":
    print("listing existing %s objects..." % conf.entity)
    print(client.search(conf.entity))
elif conf.mode.name == "create":
    print("creating a new %s object named %s..." % (conf.entity, conf.name))
    obj = client.new(conf.entity, name=conf.name)
    obj.create()
elif conf.mode.name == "delete":
    print("deleting the %s object with ID %s..." % (conf.entity, conf.id))
    obj = client.get(conf.entity, conf.id)
    client.delete(obj)

print("done")
