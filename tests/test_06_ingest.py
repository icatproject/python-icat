"""Test ingest metadata using the icat.ingest module.
"""

from collections import namedtuple
import datetime
import pytest
pytest.importorskip("lxml")
from lxml import etree
import icat
import icat.config
from icat.ingest import IngestReader
from icat.query import Query
from conftest import getConfig, gettestdata, icat_version, testdatadir


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(confSection="ingest", ids=False)
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="function")
def investigation(client, cleanup_objs):
    query = Query(client, "Investigation", conditions={
        "name": "= '12100409-ST'",
    })
    inv = client.assertedSearch(query)[0]
    yield inv
    query = Query(client, "Dataset", conditions={
        "investigation.id": "= %d" % inv.id,
        "name": "LIKE 'testingest_%'",
    })
    cleanup_objs.extend(client.search(query))

@pytest.fixture(scope="function")
def schemadir(monkeypatch):
    monkeypatch.setattr(IngestReader, "SchemaDir", testdatadir)

cet = datetime.timezone(datetime.timedelta(hours=1))
cest = datetime.timezone(datetime.timedelta(hours=2))

Case = namedtuple('Case', ['data', 'metadata', 'schema', 'checks', 'marks'])

# Try out different variants for the metadata input file
cases = [
    Case(
        data = ["testingest_inl_1", "testingest_inl_2"],
        metadata = gettestdata("metadata-4.4-inl.xml"),
        schema = gettestdata("icatdata-4.4.xsd"),
        checks = {
            "testingest_inl_1": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 15, 40, 12, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 4, 22, tzinfo=cet)),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 2.74103),
            ],
            "testingest_inl_2": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 5.1 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 13, 10, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 18, 45, 27, tzinfo=cet)),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 5.1239),
            ],
        },
        marks = (),
    ),
    Case(
        data = ["testingest_inl5_1", "testingest_inl5_2"],
        metadata = gettestdata("metadata-5.0-inl.xml"),
        schema = gettestdata("icatdata-5.0.xsd"),
        checks = {
            "testingest_inl5_1": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 15, 40, 12, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 4, 22, tzinfo=cet)),
                (("SELECT inst.name FROM Instrument inst "
                  "JOIN inst.datasetInstruments AS dsi JOIN dsi.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "E2"),
                (("SELECT t.name FROM Technique t "
                  "JOIN t.datasetTechniques AS dst JOIN dst.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "Neutron Diffraction"),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 2.74103),
            ],
            "testingest_inl5_2": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 5.1 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 13, 10, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 18, 45, 27, tzinfo=cet)),
                (("SELECT inst.name FROM Instrument inst "
                  "JOIN inst.datasetInstruments AS dsi JOIN dsi.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "E2"),
                (("SELECT t.name FROM Technique t "
                  "JOIN t.datasetTechniques AS dst JOIN dst.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "Neutron Diffraction"),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 5.1239),
            ],
        },
        marks = (
            pytest.mark.skipif(icat_version < "5.0",
                               reason="Need ICAT schema 5.0 or newer"),
        ),
    ),
    Case(
        data = ["testingest_sep_1", "testingest_sep_2"],
        metadata = gettestdata("metadata-4.4-sep.xml"),
        schema = gettestdata("icatdata-4.4.xsd"),
        checks = {
            "testingest_sep_1": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 15, 40, 12, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 4, 22, tzinfo=cet)),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 2.74103),
            ],
            "testingest_sep_2": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 5.1 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 13, 10, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 18, 45, 27, tzinfo=cet)),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 5.1239),
            ],
        },
        marks = (),
    ),
    Case(
        data = ["testingest_sep5_1", "testingest_sep5_2"],
        metadata = gettestdata("metadata-5.0-sep.xml"),
        schema = gettestdata("icatdata-5.0.xsd"),
        checks = {
            "testingest_sep5_1": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 15, 40, 12, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 4, 22, tzinfo=cet)),
                (("SELECT inst.name FROM Instrument inst "
                  "JOIN inst.datasetInstruments AS dsi JOIN dsi.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "E2"),
                (("SELECT t.name FROM Technique t "
                  "JOIN t.datasetTechniques AS dst JOIN dst.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "Neutron Diffraction"),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 2.74103),
            ],
            "testingest_sep5_2": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 5.1 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 13, 10, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 18, 45, 27, tzinfo=cet)),
                (("SELECT inst.name FROM Instrument inst "
                  "JOIN inst.datasetInstruments AS dsi JOIN dsi.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "E2"),
                (("SELECT t.name FROM Technique t "
                  "JOIN t.datasetTechniques AS dst JOIN dst.dataset AS ds "
                  "WHERE ds.id = %d"),
                 "Neutron Diffraction"),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
                (("SELECT p.numericValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Sample temperature'"),
                 5.1239),
            ],
        },
        marks = (
            pytest.mark.skipif(icat_version < "5.0",
                               reason="Need ICAT schema 5.0 or newer"),
        ),
    ),
]

@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in cases
])
def test_ingest_schema(client, investigation, schemadir, case):
    """Check that the ingest data after transformation is valid according
    to icatdata schema.
    """
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    reader = IngestReader(client, case.metadata, investigation)
    with case.schema.open("rb") as f:
        schema = etree.XMLSchema(etree.parse(f))
    assert schema.validate(reader.infile)

@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in cases
])
def test_ingest(client, investigation, schemadir, case):
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    reader = IngestReader(client, case.metadata, investigation)
    reader.ingest(datasets, dry_run=True, update_ds=True)
    for ds in datasets:
        ds.create()
    reader.ingest(datasets)
    for name in case.checks.keys():
        query = Query(client, "Dataset", conditions={
            "name": "= '%s'" % name,
            "investigation.id": "= %d" % investigation.id,
        })
        ds = client.assertedSearch(query)[0]
        for query, res in case.checks[name]:
            assert client.assertedSearch(query % ds.id)[0] == res


badcases = [
    Case(
        data = ["e208339"],
        metadata = gettestdata("metadata-5.0-badref.xml"),
        schema = gettestdata("icatdata-5.0.xsd"),
        checks = {},
        marks = (
            pytest.mark.skipif(icat_version < "5.0",
                               reason="Need ICAT schema 5.0 or newer"),
        ),
    ),
]
@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in badcases
])
def test_badref_ingest(client, investigation, schemadir, case):
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    with pytest.raises(icat.InvalidIngestFileError):
        reader = IngestReader(client, case.metadata, investigation)
        reader.ingest(datasets, dry_run=True, update_ds=True)
