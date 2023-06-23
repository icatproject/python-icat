"""Test ingest metadata using the icat.ingest module.
"""

from collections import namedtuple
import datetime
import io
import pytest
pytest.importorskip("lxml")
import icat
import icat.config
from icat.ingest import IngestReader
from icat.query import Query
from conftest import getConfig, icat_version, testdatadir


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(confSection="ingest", ids=False)
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="function")
def investigation(client):
    query = Query(client, "Investigation", conditions={
        "name": "= '12100409-ST'",
    })
    inv = client.assertedSearch(query)[0]
    yield inv
    rootclient, rootconf = getConfig(confSection="root", ids=False)
    rootclient.login(rootconf.auth, rootconf.credentials)
    query = Query(rootclient, "Dataset", conditions={
        "investigation.id": "= %d" % inv.id,
        "name": "LIKE 'testingest_%'",
    })
    rootclient.deleteMany(client.search(query))

@pytest.fixture(scope="function")
def schemadir(monkeypatch):
    monkeypatch.setattr(IngestReader, "SchemaDir", testdatadir)

cet = datetime.timezone(datetime.timedelta(hours=1))
cest = datetime.timezone(datetime.timedelta(hours=2))

Case = namedtuple('Case', ['name', 'data', 'metadata', 'checks', 'marks'])

# Try out different variants for the metadata input file
cases = [
    Case(
        name = "inl",
        data = ["testingest_inl_1", "testingest_inl_2"],
        metadata = b"""<?xml version='1.0' encoding='UTF-8'?>
        <icatingest version="1.0">
          <head>
            <date>2023-06-16T11:01:15+02:00</date>
            <generator>python-icat 1.1.0</generator>
          </head>
          <data>
            <dataset id="Dataset_1">
              <name>testingest_inl_1</name>
              <description>Dy01Cp02 at 2.7 K</description>
              <startDate>2022-02-03T15:40:12+01:00</startDate>
              <endDate>2022-02-03T17:04:22+01:00</endDate>
              <parameters>
                <stringValue>neutron</stringValue>
                <type name="Probe"/>
              </parameters>
              <parameters>
                <numericValue>5.3</numericValue>
                <type name="Reactor power" units="MW"/>
              </parameters>
              <parameters>
                <numericValue>2.74103</numericValue>
                <rangeBottom>2.7408</rangeBottom>
                <rangeTop>2.7414</rangeTop>
                <type name="Sample temperature" units="K"/>
              </parameters>
              <parameters>
                <numericValue>4.1357</numericValue>
                <rangeBottom>4.0573</rangeBottom>
                <rangeTop>4.1567</rangeTop>
                <type name="Magnetic field" units="T"/>
              </parameters>
              <parameters>
                <stringValue>Dy01Cp02</stringValue>
                <type name="Comment"/>
              </parameters>
            </dataset>
            <dataset id="Dataset_2">
              <name>testingest_inl_2</name>
              <description>Dy01Cp02 at 5.1 K</description>
              <startDate>2022-02-03T17:13:10+01:00</startDate>
              <endDate>2022-02-03T18:45:27+01:00</endDate>
              <parameters>
                <stringValue>neutron</stringValue>
                <type name="Probe"/>
              </parameters>
              <parameters>
                <numericValue>5.3</numericValue>
                <type name="Reactor power" units="MW"/>
              </parameters>
              <parameters>
                <numericValue>5.1239</numericValue>
                <rangeBottom>5.1045</rangeBottom>
                <rangeTop>5.1823</rangeTop>
                <type name="Sample temperature" units="K"/>
              </parameters>
              <parameters>
                <numericValue>3.9345</numericValue>
                <rangeBottom>3.7253</rangeBottom>
                <rangeTop>4.0365</rangeTop>
                <type name="Magnetic field" units="T"/>
              </parameters>
              <parameters>
                <stringValue>Dy01Cp02</stringValue>
                <type name="Comment"/>
              </parameters>
            </dataset>
          </data>
        </icatingest>
        """,
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
        name = "inl5",
        data = ["testingest_inl5_1", "testingest_inl5_2"],
        metadata = b"""<?xml version='1.0' encoding='UTF-8'?>
        <icatingest version="1.0">
          <head>
            <date>2023-06-16T11:01:15+02:00</date>
            <generator>python-icat 1.1.0</generator>
          </head>
          <data>
            <dataset id="Dataset_1">
              <name>testingest_inl5_1</name>
              <description>Dy01Cp02 at 2.7 K</description>
              <startDate>2022-02-03T15:40:12+01:00</startDate>
              <endDate>2022-02-03T17:04:22+01:00</endDate>
              <datasetInstruments>
                <instrument pid="DOI:00.0815/inst-00001"/>
              </datasetInstruments>
              <datasetTechniques>
                <technique pid="PaNET:PaNET01217"/>
              </datasetTechniques>
              <parameters>
                <stringValue>neutron</stringValue>
                <type name="Probe"/>
              </parameters>
              <parameters>
                <numericValue>5.3</numericValue>
                <type name="Reactor power" units="MW"/>
              </parameters>
              <parameters>
                <numericValue>2.74103</numericValue>
                <rangeBottom>2.7408</rangeBottom>
                <rangeTop>2.7414</rangeTop>
                <type name="Sample temperature" units="K"/>
              </parameters>
              <parameters>
                <numericValue>4.1357</numericValue>
                <rangeBottom>4.0573</rangeBottom>
                <rangeTop>4.1567</rangeTop>
                <type name="Magnetic field" units="T"/>
              </parameters>
              <parameters>
                <stringValue>Dy01Cp02</stringValue>
                <type name="Comment"/>
              </parameters>
            </dataset>
            <dataset id="Dataset_2">
              <name>testingest_inl5_2</name>
              <description>Dy01Cp02 at 5.1 K</description>
              <startDate>2022-02-03T17:13:10+01:00</startDate>
              <endDate>2022-02-03T18:45:27+01:00</endDate>
              <datasetInstruments>
                <instrument pid="DOI:00.0815/inst-00001"/>
              </datasetInstruments>
              <datasetTechniques>
                <technique pid="PaNET:PaNET01217"/>
              </datasetTechniques>
              <parameters>
                <stringValue>neutron</stringValue>
                <type name="Probe"/>
              </parameters>
              <parameters>
                <numericValue>5.3</numericValue>
                <type name="Reactor power" units="MW"/>
              </parameters>
              <parameters>
                <numericValue>5.1239</numericValue>
                <rangeBottom>5.1045</rangeBottom>
                <rangeTop>5.1823</rangeTop>
                <type name="Sample temperature" units="K"/>
              </parameters>
              <parameters>
                <numericValue>3.9345</numericValue>
                <rangeBottom>3.7253</rangeBottom>
                <rangeTop>4.0365</rangeTop>
                <type name="Magnetic field" units="T"/>
              </parameters>
              <parameters>
                <stringValue>Dy01Cp02</stringValue>
                <type name="Comment"/>
              </parameters>
            </dataset>
          </data>
        </icatingest>
        """,
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
        name = "sep",
        data = ["testingest_sep_1", "testingest_sep_2"],
        metadata = b"""<?xml version='1.0' encoding='UTF-8'?>
        <icatingest version="1.0">
          <head>
            <date>2023-06-16T11:01:15+02:00</date>
            <generator>python-icat 1.1.0</generator>
          </head>
          <data>
            <dataset id="Dataset_1">
              <name>testingest_sep_1</name>
              <description>Dy01Cp02 at 2.7 K</description>
              <startDate>2022-02-03T15:40:12+01:00</startDate>
              <endDate>2022-02-03T17:04:22+01:00</endDate>
            </dataset>
            <dataset id="Dataset_2">
              <name>testingest_sep_2</name>
              <description>Dy01Cp02 at 5.1 K</description>
              <startDate>2022-02-03T17:13:10+01:00</startDate>
              <endDate>2022-02-03T18:45:27+01:00</endDate>
            </dataset>
            <datasetParameter>
              <stringValue>neutron</stringValue>
              <dataset ref="Dataset_1"/>
              <type name="Probe"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>5.3</numericValue>
              <dataset ref="Dataset_1"/>
              <type name="Reactor power" units="MW"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>2.74103</numericValue>
              <rangeBottom>2.7408</rangeBottom>
              <rangeTop>2.7414</rangeTop>
              <dataset ref="Dataset_1"/>
              <type name="Sample temperature" units="K"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>4.1357</numericValue>
              <rangeBottom>4.0573</rangeBottom>
              <rangeTop>4.1567</rangeTop>
              <dataset ref="Dataset_1"/>
              <type name="Magnetic field" units="T"/>
            </datasetParameter>
            <datasetParameter>
              <stringValue>Dy01Cp02</stringValue>
              <dataset ref="Dataset_1"/>
              <type name="Comment"/>
            </datasetParameter>
            <datasetParameter>
              <stringValue>neutron</stringValue>
              <dataset ref="Dataset_2"/>
              <type name="Probe"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>5.3</numericValue>
              <dataset ref="Dataset_2"/>
              <type name="Reactor power" units="MW"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>5.1239</numericValue>
              <rangeBottom>5.1045</rangeBottom>
              <rangeTop>5.1823</rangeTop>
              <dataset ref="Dataset_2"/>
              <type name="Sample temperature" units="K"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>3.9345</numericValue>
              <rangeBottom>3.7253</rangeBottom>
              <rangeTop>4.0365</rangeTop>
              <dataset ref="Dataset_2"/>
              <type name="Magnetic field" units="T"/>
            </datasetParameter>
            <datasetParameter>
              <stringValue>Dy01Cp02</stringValue>
              <dataset ref="Dataset_2"/>
              <type name="Comment"/>
            </datasetParameter>
          </data>
        </icatingest>
        """,
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
        name = "sep5",
        data = ["testingest_sep5_1", "testingest_sep5_2"],
        metadata = b"""<?xml version='1.0' encoding='UTF-8'?>
        <icatingest version="1.0">
          <head>
            <date>2023-06-16T11:01:15+02:00</date>
            <generator>python-icat 1.1.0</generator>
          </head>
          <data>
            <dataset id="Dataset_1">
              <name>testingest_sep5_1</name>
              <description>Dy01Cp02 at 2.7 K</description>
              <startDate>2022-02-03T15:40:12+01:00</startDate>
              <endDate>2022-02-03T17:04:22+01:00</endDate>
            </dataset>
            <dataset id="Dataset_2">
              <name>testingest_sep5_2</name>
              <description>Dy01Cp02 at 5.1 K</description>
              <startDate>2022-02-03T17:13:10+01:00</startDate>
              <endDate>2022-02-03T18:45:27+01:00</endDate>
            </dataset>
            <datasetInstrument>
              <dataset ref="Dataset_1"/>
              <instrument pid="DOI:00.0815/inst-00001"/>
            </datasetInstrument>
            <datasetInstrument>
              <dataset ref="Dataset_2"/>
              <instrument pid="DOI:00.0815/inst-00001"/>
            </datasetInstrument>
            <datasetTechnique>
              <dataset ref="Dataset_1"/>
              <technique pid="PaNET:PaNET01217"/>
            </datasetTechnique>
            <datasetTechnique>
              <dataset ref="Dataset_2"/>
              <technique pid="PaNET:PaNET01217"/>
            </datasetTechnique>
            <datasetParameter>
              <stringValue>neutron</stringValue>
              <dataset ref="Dataset_1"/>
              <type name="Probe"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>5.3</numericValue>
              <dataset ref="Dataset_1"/>
              <type name="Reactor power" units="MW"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>2.74103</numericValue>
              <rangeBottom>2.7408</rangeBottom>
              <rangeTop>2.7414</rangeTop>
              <dataset ref="Dataset_1"/>
              <type name="Sample temperature" units="K"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>4.1357</numericValue>
              <rangeBottom>4.0573</rangeBottom>
              <rangeTop>4.1567</rangeTop>
              <dataset ref="Dataset_1"/>
              <type name="Magnetic field" units="T"/>
            </datasetParameter>
            <datasetParameter>
              <stringValue>Dy01Cp02</stringValue>
              <dataset ref="Dataset_1"/>
              <type name="Comment"/>
            </datasetParameter>
            <datasetParameter>
              <stringValue>neutron</stringValue>
              <dataset ref="Dataset_2"/>
              <type name="Probe"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>5.3</numericValue>
              <dataset ref="Dataset_2"/>
              <type name="Reactor power" units="MW"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>5.1239</numericValue>
              <rangeBottom>5.1045</rangeBottom>
              <rangeTop>5.1823</rangeTop>
              <dataset ref="Dataset_2"/>
              <type name="Sample temperature" units="K"/>
            </datasetParameter>
            <datasetParameter>
              <numericValue>3.9345</numericValue>
              <rangeBottom>3.7253</rangeBottom>
              <rangeTop>4.0365</rangeTop>
              <dataset ref="Dataset_2"/>
              <type name="Magnetic field" units="T"/>
            </datasetParameter>
            <datasetParameter>
              <stringValue>Dy01Cp02</stringValue>
              <dataset ref="Dataset_2"/>
              <type name="Comment"/>
            </datasetParameter>
          </data>
        </icatingest>
        """,
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
    pytest.param(c, id=c.name, marks=c.marks) for c in cases
])
def test_ingest(client, investigation, schemadir, case):
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    reader = IngestReader(client, io.BytesIO(case.metadata), investigation)
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
        name = "sep5",
        data = ["e208339"],
        metadata = b"""<?xml version='1.0' encoding='UTF-8'?>
        <icatingest version="1.0">
          <head>
            <date>2023-06-16T11:01:15+02:00</date>
            <generator>python-icat 1.1.0</generator>
          </head>
          <data>
            <dataset id="Dataset_1">
              <name>e208339</name>
            </dataset>
            <datasetInstrument>
              <dataset ref="Dataset_investigation-(name-10100601=2DST)_name-e208339"/>
              <instrument pid="DOI:00.0815/inst-00048"/>
            </datasetInstrument>
            <datasetTechnique>
              <dataset ref="Dataset_investigation-(name-10100601=2DST)_name-e208339"/>
              <technique pid="PaNET:PaNET01089"/>
            </datasetTechnique>
            <datasetParameter>
              <stringValue>very evil</stringValue>
              <dataset ref="Dataset_investigation-(name-10100601=2DST)_name-e208339"/>
              <type name="Probe"/>
            </datasetParameter>
          </data>
        </icatingest>
        """,
        checks = {},
        marks = (
            pytest.mark.skipif(icat_version < "5.0",
                               reason="Need ICAT schema 5.0 or newer"),
        ),
    ),
]
@pytest.mark.parametrize("case", [
    pytest.param(c, id=c.name, marks=c.marks) for c in badcases
])
def test_badref_ingest(client, investigation, schemadir, case):
    datasets = []
    for name in case.data:
        datasets.append(client.new("Dataset", name=name))
    reader = IngestReader(client, io.BytesIO(case.metadata), investigation)
    with pytest.raises(icat.InvalidIngestFileError):
        reader.ingest(datasets, dry_run=True, update_ds=True)
