"""Ingest metadata into ICAT.

.. note::
   The status of this module is experimental.  There may be
   incompatible changes even in minor releases.

.. versionadded:: 1.1.0
"""

from pathlib import Path
from lxml import etree
import icat.dumpfile_xml
from icat.exception import InvalidIngestFileError


class IngestReader(icat.dumpfile_xml.XMLDumpFileReader):
    """Backend to read a data file in ingest format.

    The file is on-the-fly transformed to XML data and be passed to
    XMLDumpFileReader, the parent class, to read the objects.

    This class is suitable to be used as a context manager.
    """

    SchemaDir = Path("/usr/share/icat")

    def __init__(self, client, metadata, investigation):
        self.investigation = investigation
        try:
            if hasattr(metadata, "open"):
                with metadata.open("rb") as f:
                    ingest_data = etree.parse(f)
            else:
                ingest_data = etree.parse(metadata)
        except etree.XMLSyntaxError as e:
            raise InvalidIngestFileError(e)
        with self.get_xsd(ingest_data).open("rb") as f:
            schema = etree.XMLSchema(etree.parse(f))
        if not schema.validate(ingest_data):
            raise InvalidIngestFileError("validation failed")
        with self.get_xslt(ingest_data).open("rb") as f:
            xslt = etree.XSLT(etree.parse(f))
        super().__init__(client, xslt(ingest_data))

    def get_xsd(self, ingest_data):
        return self.SchemaDir / "ingest.xsd"

    def get_xslt(self, ingest_data):
        return self.SchemaDir / "ingest.xslt"

    def getobjs(self):
        """Iterate over the objects in the ingest file.
        """
        objindex = {"Investigation": self.investigation}
        return super().getobjs(objindex=objindex)

    def ingest(self, datasets, dry_run=False, update_ds=False):
        """Ingest metadata from an ingest file.

        The acceptable set of objects in the ingest file is somewhat
        reduced compared to the file format definition: only Datasets and
        related DatasetInstruments, DatasetParameter, and
        DatasetTechniques may be present in the file.  Each dataset must
        already exist in ICAT and be in the list of datasets given as
        argument to the function.

        If the optional keyword argument `dry_run` is True, no objects
        will be updated or created in ICAT.  In that case, the datasets
        don't need to exist beforehand.  This is useful to check the
        ingest file for validity without acutally committing anything.

        if the optional keyword argument `update_ds` is True, each
        dataset's attributes and relations will be updated from the data
        found in the file.
        """
        dataset_map = { ds.name: ds for ds in datasets }
        allowed_ds_related = {
            "DatasetInstrument", "DatasetTechnique", "DatasetParameter"
        }
        for obj in self.getobjs():
            if (obj.BeanName == "Dataset" and obj.name in dataset_map):
                dataset = dataset_map[obj.name]
                assert obj.investigation == self.investigation
                if update_ds:
                    for a in obj.InstAttr | obj.InstRel:
                        v = getattr(obj, a)
                        if v is not None:
                            setattr(dataset, a, v)
                    for a in obj.InstMRel:
                        rl = getattr(obj, a)
                        if rl:
                            getattr(dataset, a).extend(rl)
                if not dry_run:
                    obj.id = dataset.id
            elif (obj.BeanName in allowed_ds_related and
                  obj.dataset.name in dataset_map and
                  obj.dataset.investigation == self.investigation):
                if not dry_run:
                    obj.create()
            else:
                raise InvalidIngestFileError("Invalid %s object"
                                             % (obj.BeanName))
