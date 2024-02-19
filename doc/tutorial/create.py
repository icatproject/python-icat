# Tutorial / Creating stuff in the ICAT server
# interactive code blocks

# Creating simple objects

f1 = client.new("Facility")
f1.name = "Fac1"
f1.fullName = "Facility 1"
f1.id = client.create(f1)
client.search("SELECT f FROM Facility f")

# --------------------

f2 = client.new("Facility", name="Fac2", fullName="Facility 2")
f2.create()
client.search("SELECT f FROM Facility f")

# Relationships to other objects

f1 = client.get("Facility", 1)

# --------------------

pt1 = client.new("ParameterType")
pt1.name = "Test parameter type 1"
pt1.units = "pct"
pt1.applicableToDataset = True
pt1.valueType = "NUMERIC"
pt1.facility = f1
pt1.create()

# --------------------

pt2 = client.new("ParameterType")
pt2.name = "Test parameter type 2"
pt2.units = "N/A"
pt2.applicableToDataset = True
pt2.valueType = "STRING"
pt2.facility = f1
for v in ["buono", "brutto", "cattivo"]:
    psv = client.new("PermissibleStringValue", value=v)
    pt2.permissibleStringValues.append(psv)

pt2.create()

# --------------------

query = ("SELECT pt FROM ParameterType pt "
         "INCLUDE pt.facility, pt.permissibleStringValues")
client.search(query)

# Access rules

publicTables = [ "Application", "DatafileFormat", "DatasetType",
                 "Facility", "FacilityCycle", "Instrument",
                 "InvestigationType", "ParameterType",
                 "PermissibleStringValue", "SampleType", ]
queries = [ "SELECT o FROM %s o" % t for t in publicTables ]
client.createRules("R", queries)
