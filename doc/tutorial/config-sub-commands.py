#! /usr/bin/python

from __future__ import print_function
import icat
import icat.config
from icat.query import Query

config = icat.config.Config(ids="optional")

# add a global configuration variable 'entity' common for all sub-commands
config.add_variable("entity", ("-e", "--entity"),
                    dict(help="an entity from the ICAT schema",
                         choices=["User", "Study"]))

# make this program use sub-commands
subcmds = config.add_subcommands("mode")

# register three possible sub-commands {list,create,delete}
subconfig_list = subcmds.add_subconfig("list",
                                       dict(help="list existing ICAT objects"))
subconfig_create = subcmds.add_subconfig("create",
                                         dict(help="create a new ICAT object"))
subconfig_delete = subcmds.add_subconfig("delete",
                                         dict(help="delete an ICAT object"))

# add two additional configuration variables 'name' and 'id', but this
# time make them only available for the respective sub-command
subconfig_create.add_variable("name", ("-n", "--name"),
                              dict(help="name for the new ICAT object"))
subconfig_delete.add_variable("id", ("-i", "--id"),
                              dict(help="id of the ICAT object"))

client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

# check which sub-command (mode) was called
if conf.mode.name == "list":
    print("listing existing %s objects..." % conf.entity)
    print(client.search(conf.entity))
elif conf.mode.name == "create":
    print("creating a new %s object named %s..." % (conf.entity, conf.name))
    obj = client.new(conf.entity.lower(), name=conf.name)
    obj.create()
elif conf.mode.name == "delete":
    print("deleting the %s object with id %s..." % (conf.entity, conf.id))
    query = Query(client, conf.entity, conditions={"id": "=%s" % conf.id})
    client.deleteMany(client.assertedSearch(query))

print("done")
