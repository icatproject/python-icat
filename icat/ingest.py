"""Ingest metadata into ICAT.

.. note::
   The status of this module in the current version is still
   experimental.  There may be incompatible changes in the future
   even in minor releases of python-icat.

.. versionadded:: 1.1.0
"""

from pathlib import Path
from lxml import etree
import icat.dumpfile_xml
from icat.exception import InvalidIngestFileError


class IngestReader(icat.dumpfile_xml.XMLDumpFileReader):
    """Read metadata from XML ingest files into ICAT.

    The input file may contain one or more datasets and related
    objects that must all belong to a single investigation.  The file
    is first validated against an XML Schema Definition (XSD) and then
    transformed on-the-fly into generic ICAT data file format using an
    XSL Transformation (XSLT).  The result of that transformation is
    fed into the parent class
    :class:`~icat.dumpfile_xml.XMLDumpFileReader`.

    :param client: a client object configured to connect to the ICAT
        server that the objects should be created in.
    :type client: :class:`icat.client.Client`
    :param metadata: the input file.  Either the path to the file or a
        file object opened for reading binary data.
    :type metadata: :class:`~pathlib.Path` or file object
    :param investigation: the investigation object that the input data
        should belong to.
    :type investigation: :class:`icat.entity.Entity`
    :raise icat.exception.InvalidIngestFileError: if the input in
        metadata is not valid.
    """

    SchemaDir = Path("/usr/share/icat")
    """Path to a directory to read XSD and XSLT files from.
    """
    XSD_Map = {
        ('icatingest', '1.0'): "ingest-10.xsd",
        ('icatingest', '1.1'): "ingest-11.xsd",
    }
    """A mapping to select the XSD file to use.  Keys are pairs of root
    element name and version attribute, the values are the
    corresponding name of the XSD file.
    """
    XSLT_Map = {
        'icatingest': "ingest.xslt",
    }
    """A mapping to select the XSLT file to use.  Keys are the root
    element name, the values are the corresponding name of the XSLT
    file.

    .. versionadded:: 1.3.0
    """

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
        """Get the XSD file.

        Inspect the root element in the input data and lookup the
        tuple of element name and version attribute in
        :attr:`~icat.ingest.IngestReader.XSD_Map`.  The value is taken
        as a file name relative to
        :attr:`~icat.ingest.IngestReader.SchemaDir` and this path is
        returned.

        Subclasses may override this method to customize the XSD file
        to use.  These derived versions may inspect the input data to
        select the appropriate file.  Derived versions should raise
        :exc:`~icat.exception.InvalidIngestFileError` if they decide
        to reject the input data.

        :param ingest_data: input data
        :type ingest_data: :class:`lxml.etree._ElementTree`
        :return: path to the XSD file.
        :rtype: :class:`~pathlib.Path`
        :raise icat.exception.InvalidIngestFileError: if the pair of
            root element name and version attribute could not be found
            in :attr:`~icat.ingest.IngestReader.XSD_Map`.
        """
        root = ingest_data.getroot()
        try:
            xsd = self.XSD_Map[root.tag, root.get("version")]
        except KeyError:
            raise InvalidIngestFileError("unknown format")
        return self.SchemaDir / xsd

    def get_xslt(self, ingest_data):
        """Get the XSLT file.

        Inspect the root element in the input data and lookup the
        element name in :attr:`~icat.ingest.IngestReader.XSLT_Map`.
        The value is taken as a file name relative to
        :attr:`~icat.ingest.IngestReader.SchemaDir` and this path is
        returned.

        Subclasses may override this method to customize the XSLT file
        to use.  These derived versions may inspect the input data to
        select the appropriate file.  Derived versions should raise
        :exc:`~icat.exception.InvalidIngestFileError` if they decide
        to reject the input data.

        :param ingest_data: input data
        :type ingest_data: :class:`lxml.etree._ElementTree`
        :return: path to the XSLT file.
        :rtype: :class:`~pathlib.Path`
        :raise icat.exception.InvalidIngestFileError: if the root
            element name could not be found in
            :attr:`~icat.ingest.IngestReader.XSLT_Map`.

        .. versionchanged:: 1.3.0
            lookup the root element name in
            :attr:`~icat.ingest.IngestReader.XSLT_Map` rather than
            using a static file name.
        """
        root = ingest_data.getroot()
        try:
            xslt = self.XSLT_Map[root.tag]
        except KeyError:
            raise InvalidIngestFileError("unknown format")
        return self.SchemaDir / xslt

    def getobjs(self):
        """Iterate over the objects in the ingest file.
        """
        objindex = {"_Investigation": self.investigation}
        return super().getobjs(objindex=objindex)

    def ingest(self, datasets, dry_run=False, update_ds=False):
        """Ingest metadata from an ingest file.

        Read the metadata provided as argument to the constructor.
        The acceptable set of objects in the input is restricted: only
        ``Dataset`` and related ``DatasetInstrument``,
        ``DatasetTechnique``, and ``DatasetParameter`` objects are
        allowed.  The ``Dataset`` objects must be in the list provided
        as argument.

        If `dry_run` is :const:`False`, the related objects will be
        created in ICAT.  In this case, the `datasets` in the argument
        must already have been created in ICAT beforehand (e.g. the
        `id` attribute must be set).  If `dry_run` is :const:`True`,
        the `datasets` don't need to be created beforehand.

        if `update_ds` is :const:`True`, the objects in the `datasets`
        argument will be updated: the attributes and the relations to
        other objects will be set to the values read from the input.

        :param datasets: list of allowed datasets in the input.
        :type datasets: iterable of :class:`icat.entity.Entity`
        :param dry_run: flag whether not to create related objects.
        :type dry_run: :class:`bool`
        :param update_ds: flag whether to update the `datasets` in the
            argument.
        :type update_ds: :class:`bool`
        :raise icat.exception.InvalidIngestFileError: if any unallowed
            object is read from the input.
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
