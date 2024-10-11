#! /usr/bin/python3
"""Ingest metadata into ICAT.

This scripts demonstrates how to use class IngestReader from the
icat.ingest module to read metadata from a file and add that to ICAT.
The script intents to model the use case of ingesting raw datasets
from the experiment.

The script expects an input directory containing one metadata input
file and one or more subdirectories for each dataset respectively,
e.g. something like::

  input_dir
   ├── metadata.xml
   ├── dataset_1
   │    ├── datafile_a.dat
   │    ├── datafile_b.dat
   │    └── datafile_c.dat
   └── dataset_2
        ├── datafile_d.dat
        ├── datafile_e.dat
        └── datafile_f.dat

The script takes the name of an investigation as argument.  The
investigation MUST exist in ICAT beforehand and all datasets in the
input directory MUST belong to this investigation.  The script will
create the datasets in ICAT, e.g. they MUST NOT exist in ICAT
beforehand.  The metadata input file may contain attributes and
related objects (datasetInstrument, datasetTechnique,
datasetParameter) for the datasets provided in the input directory.
The metadata input is restricted in that sense, e.g. this script
enforces that the metadata does not contain any other input.

The XML Schema Definition and XSL Transformation files (ingest.xsd and
ingest.xslt) provided by python-icat (or customized versions thereof)
need to be installed so that class IngestReader will find them
(e.g. in the IngestReader.SchemaDir directory).

There are some limitations to keep things simple:

* the script creates the dataset and datafile objects in ICAT, but
  does not upload the file content to IDS.  In a real production
  workflow, you'd probably have a separate step that copies the files
  to the storage managed by IDS while creating the dataset and
  datafile objects in ICAT at the same time.

* the script does not care to add a datafileFormat or any descriptive
  attributes (fileSize, checksum, datafileModTime) to the datafiles it
  creates.

* it is assumed that the investigation can be unambiguously found by
  its name.

* a real production workflow would probably apply much stricter
  conformance checks on the input (e.g. restrictions on allowed
  dataset or datafile names, make sure not to follow any symlinks from
  the input directory) and have a more elaborated error handling.

"""

import logging
from pathlib import Path
import icat
import icat.config
from icat.ingest import IngestReader
from icat.query import Query


logging.basicConfig(level=logging.DEBUG)
# Silence some rather chatty modules.
logging.getLogger('suds.client').setLevel(logging.CRITICAL)
logging.getLogger('suds').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


config = icat.config.Config(ids=False)
config.add_variable('investigation', ("investigation",),
                    dict(help="name of the investigation"))
config.add_variable('inputdir', ("inputdir",),
                    dict(help="path to the input directory"),
                    type=Path)
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

query = Query(client, "Investigation", conditions={
    "name": "= '%s'" % conf.investigation
})
investigation = client.assertedSearch(query)[0]


class ContentError(RuntimeError):
    """Some invalid content in the input directory.
    """
    def __init__(self, base, p, msg):
        p = p.relative_to(base)
        super().__init__("%s: %s" % (p, msg))


def check(client, path, investigation):
    """Verify the content of the input directory.

    The idea is to check the input directory for conformance as much
    as possible and to fail early if anything is not as required,
    before having committed anything to ICAT.

    Returns a tuple with two items: a list of datasets and an
    IngestReader.
    """
    datasets = []
    metadata_path = path / "metadata.xml"
    for p0 in path.iterdir():
        if p0.name.startswith('.') or p0 == metadata_path:
            continue
        elif p0.is_dir():
            is_empty = True
            dataset = client.new("dataset")
            dataset.name = p0.name
            dataset.complete = False
            for p1 in p0.iterdir():
                if p1.is_file():
                    is_empty = False
                    datafile = client.new("datafile")
                    datafile.name = p1.name
                    dataset.datafiles.append(datafile)
                else:
                    raise ContentError(path, p1, 'unexpected item')
            if is_empty:
                raise ContentError(path, p0, 'empty dataset directory')
            datasets.append(dataset)
        else:
            raise ContentError(path, p0, 'unexpected item')
    try:
        reader = IngestReader(client, metadata_path, investigation)
        reader.ingest(datasets, dry_run=True, update_ds=True)
    except (icat.InvalidIngestFileError, icat.SearchResultError) as e:
        raise ContentError(path, metadata_path,
                           "%s: %s" % (type(e).__name__, e))
    return (datasets, reader)

logger.info("ingesting from directory %s into investigation %s",
            conf.inputdir, investigation.name)
datasets, reader = check(client, conf.inputdir, investigation)
logger.debug("input directory checked, found %d datasets", len(datasets))
for ds in datasets:
    ds.create()
    ds.truncateRelations(keepInstRel=True)
    logger.debug("created dataset %s", ds.name)
reader.ingest(datasets)
for ds in datasets:
    ds.complete = True
    ds.update()
logger.debug("ingest done")
