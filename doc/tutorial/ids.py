# Tutorial / Upload and download files to and from IDS
# interactive code blocks

client.ids.isReadOnly()

# Upload files

users = [("jdoe", "John"), ("nbour", "Nicolas"), ("rbeck", "Rudolph")]
for user, name in users:
    with open("greet-%s.txt" % user, "wt") as f:
        print("Hello %s!" % name, file=f)

# --------------------

from icat.query import Query
query = Query(client, "Investigation", conditions={"name": "= '12100409-ST'"})
investigation = client.assertedSearch(query)[0]
dataset = client.new("Dataset")
dataset.investigation = investigation
query = Query(client, "DatasetType", conditions={"name": "= 'other'"})
dataset.type = client.assertedSearch(query)[0]
dataset.name = "greetings"
dataset.complete = False
dataset.create()

# --------------------

query = Query(client, "DatafileFormat", conditions={"name": "= 'Text'"})
df_format = client.assertedSearch(query)[0]
for fname in ("greet-jdoe.txt", "greet-nbour.txt", "greet-rbeck.txt"):
    datafile = client.new("Datafile",
                          name=fname,
                          dataset=dataset,
                          datafileFormat=df_format)
    client.putData(fname, datafile)

# Download files

query = Query(client, "Datafile", conditions={
    "name": "= 'greet-jdoe.txt'",
    "dataset.name": "= 'greetings'"
})
df = client.assertedSearch(query)[0]
data = client.getData([df])
type(data)
data.read().decode('utf8')

# --------------------

from io import BytesIO
from zipfile import ZipFile
query = Query(client, "Dataset", conditions={"name": "= 'greetings'"})
ds = client.assertedSearch(query)[0]
data = client.getData([ds])
buffer = BytesIO(data.read())
with ZipFile(buffer) as zipfile:
    for f in zipfile.namelist():
        print("file name: %s" % f)
        print("content: %r" % zipfile.open(f).read().decode('utf8'))

# --------------------

from icat.ids import DataSelection
selection = DataSelection([ds])
client.ids.archive(selection)

# --------------------

client.ids.getStatus(selection)

# --------------------

data = client.getData([ds])

# --------------------

client.ids.getStatus(selection)
data = client.getData([ds])
len(data.read())

# --------------------

preparedId = client.prepareData(selection)
preparedId

# --------------------

client.isDataPrepared(preparedId)
data = client.getData(preparedId)
buffer = BytesIO(data.read())
with ZipFile(buffer) as zipfile:
    zipfile.namelist()
