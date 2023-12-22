# Tutorial / Working with objects in the ICAT server
# interactive code blocks

client.search("SELECT f FROM Facility f INCLUDE f.parameterTypes LIMIT 1,1")

# Building advanced queries

from icat.query import Query

# --------------------

query = Query(client, "Investigation")
print(query)
client.search(query)

# --------------------

query = Query(client, "Investigation",
              conditions={"name": "= '10100601-ST'"})
print(query)
client.search(query)

# --------------------

query = Query(client, "Investigation",
              conditions={"name": "= '10100601-ST'"},
              includes=["datasets"])
print(query)
client.search(query)

# --------------------

query = Query(client, "Investigation",
              conditions={"LENGTH(title)": "= 18"})
print(query)
client.search(query)

# --------------------

conditions = {
    "investigation.name": "= '10100601-ST'",
    "parameters.type.name": "= 'Magnetic field'",
    "parameters.type.units": "= 'T'",
    "parameters.numericValue": "> 5.0",
}
query = Query(client, "Dataset",
              conditions=conditions, includes=["parameters.type"])
print(query)
client.search(query)

# --------------------

def get_investigation(client, name, visitId=None):
    query = Query(client, "Investigation")
    query.addConditions({"name": "= '%s'" % name})
    if visitId is not None:
        query.addConditions({"visitId": "= '%s'" % visitId})
    print(query)
    return client.assertedSearch(query)[0]

get_investigation(client, "08100122-EF")
get_investigation(client, "12100409-ST", "1.1-P")

# --------------------

conditions = {
    "datafileCreateTime": [">= '2012-01-01'", "< '2013-01-01'"]
}
query = Query(client, "Datafile", conditions=conditions)
print(query)
client.search(query)

# --------------------

query = Query(client, "Datafile")
query.addConditions({"datafileCreateTime": ">= '2012-01-01'"})
query.addConditions({"datafileCreateTime": "< '2013-01-01'"})
print(query)

# --------------------

query = Query(client, "Dataset", attributes="name")
print(query)
client.search(query)

# --------------------

query = Query(client, "Dataset", attributes=[
    "investigation.name", "name", "complete", "type.name"
])
print(query)
client.search(query)

# --------------------

query = Query(client, "Dataset", aggregate="COUNT")
print(query)
client.search(query)

# --------------------

conditions = {
    "dataset.investigation.name": "= '10100601-ST'",
    "type.name": "= 'Magnetic field'",
    "type.units": "= 'T'",
}
query = Query(client, "DatasetParameter",
              conditions=conditions, attributes="numericValue")
print(query)
client.search(query)
query.setAggregate("MIN")
print(query)
client.search(query)
query.setAggregate("MAX")
print(query)
client.search(query)
query.setAggregate("AVG")
print(query)
client.search(query)

# --------------------

conditions = {
    "datasets.parameters.type.name": "= 'Magnetic field'",
    "datasets.parameters.type.units": "= 'T'",
}
query = Query(client, "Investigation", conditions=conditions)
print(query)
client.search(query)

# --------------------

query.setAggregate("DISTINCT")
print(query)
client.search(query)

# --------------------

conditions = {
    "datasets.parameters.type.name": "= 'Magnetic field'",
    "datasets.parameters.type.units": "= 'T'",
}
query = Query(client, "Investigation",
              conditions=conditions, aggregate="COUNT")
print(query)
client.search(query)
query.setAggregate("COUNT:DISTINCT")
print(query)
client.search(query)

# --------------------

order = ["type.name", "type.units", ("numericValue", "DESC")]
query = Query(client, "DatasetParameter", includes=["type"], order=order)
print(query)
client.search(query)

# --------------------

query = Query(client, "User", conditions={
    "fullName": "IS NOT NULL"
}, order=[("LENGTH(fullName)", "DESC")])
print(query)
for user in client.search(query):
    print("%d: %s" % (len(user.fullName), user.fullName))

# --------------------

query = Query(client, "Dataset",
              order=[("endDate", "DESC")], limit=(2, 1))
print(query)
client.search(query)

# Useful search methods

res = client.search(Query(client, "Facility"))
if not res:
    raise RuntimeError("Facility not found")
elif len(res) > 1:
    raise RuntimeError("Facility not unique")

facility = res[0]
facility = client.assertedSearch(Query(client, "Facility"))[0]

# --------------------

for ds in client.searchChunked(Query(client, "Dataset")):
    # do something useful with the dataset ds ...
    print(ds.name)

# --------------------

def get_dataset(client, inv_name, ds_name, ds_type="raw"):
    """Get a dataset in an investigation.
    If it already exists, search and return it, create it, if not.
    """
    try:
        dataset = client.new("Dataset")
        query = Query(client, "Investigation", conditions={
            "name": "= '%s'" % inv_name
        })
        dataset.investigation = client.assertedSearch(query)[0]
        query = Query(client, "DatasetType", conditions={
            "name": "= '%s'" % ds_type
        })
        dataset.type = client.assertedSearch(query)[0]
        dataset.complete = False
        dataset.name = ds_name
        dataset.create()
    except icat.ICATObjectExistsError:
        dataset = client.searchMatching(dataset)
    return dataset
