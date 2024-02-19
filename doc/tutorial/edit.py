# Tutorial / Working with objects in the ICAT server
# interactive code blocks

client.search("SELECT f FROM Facility f")

# Editing the attributes of objects

for facility in client.search("SELECT f FROM Facility f"):
    facility.description = "An example facility"
    facility.daysUntilRelease = 1826
    facility.fullName = "%s Facility" % facility.name
    client.update(facility)

client.search("SELECT f FROM Facility f")

# --------------------

for facility in client.search("SELECT f FROM Facility f"):
    facility.description = None
    facility.update()

client.search("SELECT f FROM Facility f")

# Copying objects

fac = client.get("Facility f INCLUDE f.parameterTypes", 1)
print(fac)

# --------------------

facc = fac.copy()
print(facc.name)
print(facc.parameterTypes[0].name)
facc.name = "Fac0"
facc.parameterTypes[0].name = "Test parameter type 0"
print(fac.name)
print(fac.parameterTypes[0].name)

# --------------------

fac.truncateRelations()
print(fac)
print(facc)
