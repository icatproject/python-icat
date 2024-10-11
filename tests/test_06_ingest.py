"""Test ingest metadata using the icat.ingest module.
"""

from collections import namedtuple
import datetime
import io
import logging
import pytest
pytest.importorskip("lxml")
from lxml import etree
import icat
import icat.config
from icat.ingest import IngestReader
from icat.query import Query
from conftest import (getConfig, gettestdata, icat_version,
                      get_icatdata_schema, testdatadir)

logger = logging.getLogger(__name__)

# There seem to be a bug in older icat.server versions when searching
# for a single boolean attribute in a query.
skip_single_boolean = icat_version < "4.11.0"

def print_xml(root):
    print('\n', etree.tostring(root, pretty_print=True).decode(), sep='')

def get_test_investigation(client):
    query = Query(client, "Investigation", conditions={
        "name": "= '12100409-ST'",
    })
    return client.assertedSearch(query)[0]

class NamedBytesIO(io.BytesIO):
    def __init__(self, initial_bytes, name):
        super().__init__(initial_bytes)
        self.name = name

@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(confSection="ingest", ids=False)
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="module")
def samples(rootclient):
    """Create some samples that are referenced in some of the ingest files.
    """
    query = Query(rootclient, "SampleType", conditions={
        "name": "= 'Nickel(II) oxide SC'"
    })
    st = rootclient.assertedSearch(query)[0]
    inv = get_test_investigation(rootclient)
    samples = []
    for n in ("ab3465", "ab3466"):
        s = rootclient.new("Sample", name=n, type=st, investigation=inv)
        s.create()
        samples.append(s)
    yield samples
    rootclient.deleteMany(samples)

@pytest.fixture(scope="function")
def investigation(client, cleanup_objs):
    inv = get_test_investigation(client)
    yield inv
    query = Query(client, "Dataset", conditions={
        "investigation.id": "= %d" % inv.id,
        "name": "LIKE 'testingest_%'",
    })
    cleanup_objs.extend(client.search(query))

@pytest.fixture(scope="function")
def schemadir(monkeypatch):
    monkeypatch.setattr(IngestReader, "SchemaDir", testdatadir)


class EnvironmentIngestReader(IngestReader):
    """Modified version of IngestReader
    - Allow custom environment settings to be included.
    - Capture the ingest data after injection of the environment in an
      attribute.
    """
    _add_env = dict()
    def get_environment(self, client):
        env = super().get_environment(client)
        env.update(self._add_env)
        return env
    def add_environment(self, client, ingest_data):
        super().add_environment(client, ingest_data)
        self._ingest_data = ingest_data


class MyIngestReader(IngestReader):
    """Testing a customized IngestReader
    """
    XSD_Map = {
        ('icatingest', '1.0'): "ingest-10.xsd",
        ('icatingest', '1.1'): "ingest-11.xsd",
        ('myingest', '1.0'): "myingest.xsd",
    }
    XSLT_Map = {
        'icatingest': "ingest.xslt",
        'myingest': "myingest.xslt",
    }


cet = datetime.timezone(datetime.timedelta(hours=1))
cest = datetime.timezone(datetime.timedelta(hours=2))

Case = namedtuple('Case', ['data', 'metadata', 'checks', 'marks'])

# Try out different variants for the metadata input file
cases = [
    Case(
        data = ["testingest_inl_1", "testingest_inl_2"],
        metadata = gettestdata("metadata-4.4-inl.xml"),
        checks = {
            "testingest_inl_1": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
        checks = {
            "testingest_inl5_1": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
        checks = {
            "testingest_sep_1": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
        checks = {
            "testingest_sep5_1": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
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
        data = [ "testingest_sample_1", "testingest_sample_2",
                 "testingest_sample_3", "testingest_sample_4" ],
        metadata = gettestdata("metadata-sample.xml"),
        checks = {
            "testingest_sample_1": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "ab3465 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 9, 30, 18, 2, 17, tzinfo=cest)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 9, 30, 20, 18, 36, tzinfo=cest)),
                (("SELECT COUNT(s) FROM Sample s JOIN s.datasets AS ds "
                  "WHERE ds.id = %d"),
                 1),
                (("SELECT s.name FROM Sample s JOIN s.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "ab3465"),
            ],
            "testingest_sample_2": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "ab3465 at 5.1 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 9, 30, 20, 29, 19, tzinfo=cest)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 9, 30, 21, 23, 49, tzinfo=cest)),
                (("SELECT COUNT(s) FROM Sample s JOIN s.datasets AS ds "
                  "WHERE ds.id = %d"),
                 1),
                (("SELECT s.name FROM Sample s JOIN s.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "ab3465"),
            ],
            "testingest_sample_3": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "ab3466 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 9, 30, 21, 35, 16, tzinfo=cest)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 9, 30, 23, 4, 27, tzinfo=cest)),
                (("SELECT COUNT(s) FROM Sample s JOIN s.datasets AS ds "
                  "WHERE ds.id = %d"),
                 1),
                (("SELECT s.name FROM Sample s JOIN s.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "ab3466"),
            ],
            "testingest_sample_4": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 False),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "raw"),
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "reference"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 9, 30, 23, 4, 31, tzinfo=cest)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2020, 10, 1, 1, 26, 7, tzinfo=cest)),
                (("SELECT COUNT(s) FROM Sample s JOIN s.datasets AS ds "
                  "WHERE ds.id = %d"),
                 0),
            ],
        },
        marks = (),
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
    reader = EnvironmentIngestReader(client, case.metadata, investigation)
    print_xml(reader._ingest_data)
    print_xml(reader.infile)
    with get_icatdata_schema().open("rb") as f:
        schema = etree.XMLSchema(etree.parse(f))
    schema.assertValid(reader.infile)

@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in cases
])
def test_ingest(client, investigation, samples, schemadir, case):
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
            if skip_single_boolean and isinstance(res, bool):
                continue
            assert client.assertedSearch(query % ds.id)[0] == res

io_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="1.1">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data>
    <dataset id="Dataset_1">
      <name>testingest_io_1</name>
      <description>Dy01Cp02 at 10.2 K</description>
      <startDate>2022-02-03T15:40:12+01:00</startDate>
      <endDate>2022-02-03T17:04:22+01:00</endDate>
      <parameters>
        <stringValue>neutron</stringValue>
        <type name="Probe"/>
      </parameters>
    </dataset>
  </data>
</icatingest>
""".encode("utf8"), "io_metadata")
io_cases = [
    Case(
        data = ["testingest_io_1"],
        metadata = io_metadata,
        checks = {
            "testingest_io_1": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 10.2 K"),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "neutron"),
            ],
        },
        marks = (),
    ),
]

@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in io_cases
])
def test_ingest_fileobj(client, investigation, samples, schemadir, case):
    """Test ingest reading from a file object rather than a Path
    """
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
            if skip_single_boolean and isinstance(res, bool):
                continue
            assert client.assertedSearch(query % ds.id)[0] == res


invalid_root_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatinvalid version="1.0">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data/>
</icatinvalid>
""".encode("utf8"), "invalid_root")
invalid_ver_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="0.7">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data/>
</icatingest>
""".encode("utf8"), "invalid_version")
invalid_ref_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="1.0">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data>
    <dataset id="Dataset_1">
      <name>testingest_err_invalid_ref</name>
    </dataset>
    <datasetParameter>
      <stringValue>very evil</stringValue>
      <dataset ref="Dataset_investigation-(name-12100409=2DST)_name-testingest=5Ferr=5Finvalid=5Fref"/>
      <type name="Probe"/>
    </datasetParameter>
  </data>
</icatingest>
""".encode("utf8"), "invalid_ref")
invalid_dup_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="1.0">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data>
    <dataset id="Dataset_1">
      <name>testingest_err_invalid_dup</name>
    </dataset>
    <datasetParameter>
      <numericValue>10.0</numericValue>
      <dataset ref="Dataset_1"/>
      <type name="Reactor power" units="MW"/>
    </datasetParameter>
    <datasetParameter>
      <numericValue>17.0</numericValue>
      <dataset ref="Dataset_1"/>
      <type name="Reactor power" units="MW"/>
    </datasetParameter>
  </data>
</icatingest>
""".encode("utf8"), "invalid_dup")
invalid_dup_id_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="1.0">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data>
    <dataset id="Dataset_1">
      <name>testingest_err_invalid_dup_id_1</name>
    </dataset>
    <dataset id="Dataset_1">
      <name>testingest_err_invalid_dup_id_2</name>
    </dataset>
    <datasetParameter>
      <numericValue>10.0</numericValue>
      <dataset ref="Dataset_1"/>
      <type name="Reactor power" units="MW"/>
    </datasetParameter>
  </data>
</icatingest>
""".encode("utf8"), "invalid_dup_id")
invalid_cases = [
    Case(
        data = [],
        metadata = invalid_root_metadata,
        checks = {},
        marks = (),
    ),
    Case(
        data = [],
        metadata = invalid_ver_metadata,
        checks = {},
        marks = (),
    ),
    Case(
        data = ["testingest_err_invalid_ref"],
        metadata = invalid_ref_metadata,
        checks = {},
        marks = (),
    ),
    Case(
        data = ["testingest_err_invalid_dup"],
        metadata = invalid_dup_metadata,
        checks = {},
        marks = (),
    ),
    Case(
        data = ["testingest_err_invalid_dup_id_1",
                "testingest_err_invalid_dup_id_2"],
        metadata = invalid_dup_id_metadata,
        checks = {},
        marks = (),
    ),
]
@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in invalid_cases
])
def test_ingest_error_invalid(client, investigation, schemadir, case):
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    with pytest.raises(icat.InvalidIngestFileError) as exc:
        reader = IngestReader(client, case.metadata, investigation)
        reader.ingest(datasets, dry_run=True, update_ds=True)
    logger.info("Raised %s: %s", exc.type.__name__, exc.value)

searcherr_attr_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="1.0">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data>
    <dataset id="Dataset_1">
      <name>testingest_err_search_attr</name>
    </dataset>
    <datasetParameter>
      <numericValue>10.0</numericValue>
      <dataset ref="Dataset_1"/>
      <type name="not found"/>
    </datasetParameter>
  </data>
</icatingest>
""".encode("utf8"), "search_attr")
searcherr_ref_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="1.0">
  <head>
    <date>2023-06-16T11:01:15+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data>
    <dataset id="Dataset_1">
      <name>testingest_err_search_ref</name>
    </dataset>
    <datasetParameter>
      <numericValue>10.0</numericValue>
      <dataset ref="Dataset_notfound"/>
      <type name="Reactor power" units="MW"/>
    </datasetParameter>
  </data>
</icatingest>
""".encode("utf8"), "search_ref")
searcherr_cases = [
    Case(
        data = ["testingest_err_search_attr"],
        metadata = searcherr_attr_metadata,
        checks = {},
        marks = (),
    ),
    Case(
        data = ["testingest_err_search_ref"],
        metadata = searcherr_ref_metadata,
        checks = {},
        marks = (),
    ),
]
@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in searcherr_cases
])
def test_ingest_error_searcherr(client, investigation, schemadir, case):
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    with pytest.raises(icat.SearchResultError) as exc:
        reader = IngestReader(client, case.metadata, investigation)
        reader.ingest(datasets, dry_run=True, update_ds=True)
    logger.info("Raised %s: %s", exc.type.__name__, exc.value)


classattr_metadata = NamedBytesIO("""<?xml version='1.0' encoding='UTF-8'?>
<icatingest version="1.1">
  <head>
    <date>2024-10-11T10:51:26+02:00</date>
    <generator>metadata-writer 0.27a</generator>
  </head>
  <data>
    <dataset id="Dataset_1">
      <name>testingest_classattr_1</name>
      <description>Auxiliary data</description>
      <startDate>2022-02-03T15:40:12+01:00</startDate>
      <endDate>2022-02-03T17:04:22+01:00</endDate>
    </dataset>
  </data>
</icatingest>
""".encode("utf8"), "classattr_metadata")
classattr_cases = [
    Case(
        data = ["testingest_classattr_1"],
        metadata = classattr_metadata,
        checks = {
            "testingest_classattr_1": [
                ("SELECT ds.complete FROM Dataset ds WHERE ds.id = %d",
                 True),
                (("SELECT t.name FROM DatasetType t JOIN t.datasets AS ds "
                  "WHERE ds.id = %d"),
                 "other"),
            ],
        },
        marks = (),
    ),
]
@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in classattr_cases
])
@pytest.mark.skipif(skip_single_boolean, reason="Bug in icat.server")
def test_ingest_classattr(monkeypatch, client, investigation, schemadir, case):
    """Test overriding prescribed values set in IngestReader class attributes.
    """
    monkeypatch.setattr(IngestReader, "Dataset_complete", "true")
    monkeypatch.setattr(IngestReader, "DatasetType_name", "other")
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


customcases = [
    Case(
        data = ["testingest_custom_icatingest_1"],
        metadata = gettestdata("metadata-custom-icatingest.xml"),
        checks = {
            "testingest_custom_icatingest_1": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "Dy01Cp02 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 15, 40, 12, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 4, 22, tzinfo=cet)),
                (("SELECT COUNT(p) FROM DatasetParameter p "
                  "JOIN p.dataset AS ds "
                  "WHERE ds.id = %d"),
                 0),
            ],
        },
        marks = (),
    ),
    Case(
        data = ["testingest_custom_myingest_1"],
        metadata = gettestdata("metadata-custom-myingest.xml"),
        checks = {
            "testingest_custom_myingest_1": [
                ("SELECT ds.description FROM Dataset ds WHERE ds.id = %d",
                 "My Ingest: Dy01Cp02 at 2.7 K"),
                ("SELECT ds.startDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 15, 40, 12, tzinfo=cet)),
                ("SELECT ds.endDate FROM Dataset ds WHERE ds.id = %d",
                 datetime.datetime(2022, 2, 3, 17, 4, 22, tzinfo=cet)),
                (("SELECT COUNT(p) FROM DatasetParameter p "
                  "JOIN p.dataset AS ds "
                  "WHERE ds.id = %d"),
                 1),
                (("SELECT p.stringValue FROM DatasetParameter p "
                  "JOIN p.dataset AS ds JOIN p.type AS t "
                  "WHERE ds.id = %d AND t.name = 'Probe'"),
                 "x-ray"),
            ],
        },
        marks = (),
    ),
]
@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in customcases
])
def test_custom_ingest(client, investigation, samples, schemadir, case):
    """Test a custom ingest reader MyIngestReader, defined above.

    MyIngestReader defines a custom ingest format by defining it's own
    set of XSD and XSLT file.  But it still supports the vanilla
    icatingest format.  In the test, we define two cases, having
    identical input data: the first one using icatdata format, the
    second one the customized myingest format.  Otherwise the input is
    identical.  But note that the transformation for the myingest case
    alters the input on the fly, so we get different results.
    """
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    reader = MyIngestReader(client, case.metadata, investigation)
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
            if skip_single_boolean and isinstance(res, bool):
                continue
            assert client.assertedSearch(query % ds.id)[0] == res


env_cases = [
    Case(
        data = ["testingest_inl_1", "testingest_inl_2"],
        metadata = gettestdata("metadata-4.4-inl.xml"),
        checks = {},
        marks = (),
    ),
]
@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.metadata.name, marks=c.marks) for c in env_cases
])
def test_ingest_env(monkeypatch, client, investigation, schemadir, case):
    """Test using the _environment element.

    Add a custom attribute to the _environment that is injected by
    IngestReader into the input data.  Apply a custom XSLT that
    extracts attributes from the _environment element and puts the
    values into the head element of the transformed input.  This is to
    test that adding the _environment element works and it is in
    principle possible to make use of the values in the XSLT.
    """
    generator = "test_ingest_env (python-icat %s)" % icat.__version__
    monkeypatch.setattr(EnvironmentIngestReader,
                        "_add_env", dict(generator=generator))
    monkeypatch.setattr(EnvironmentIngestReader,
                        "XSLT_Map", dict(icatingest="ingest-env.xslt"))
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    reader = EnvironmentIngestReader(client, case.metadata, investigation)
    print_xml(reader._ingest_data)
    print_xml(reader.infile)
    with get_icatdata_schema().open("rb") as f:
        schema = etree.XMLSchema(etree.parse(f))
    schema.assertValid(reader.infile)
    version_elem = reader.infile.xpath("/icatdata/head/apiversion")
    assert version_elem
    assert version_elem[0].text == str(client.apiversion)
    generator_elem = reader.infile.xpath("/icatdata/head/generator")
    assert generator_elem
    assert generator_elem[0].text == generator
