"""Provide the classes corresponding to the entities in the ICAT schema.

Entity classes defined in this module are derived from the abstract
base class `Entity` from module `icat.entity`.  They override the
class variables ``BeanName``, ``InstAttr``, ``InstRel``, and
``InstMRel`` as appropriate.
"""

from icat.entity import Entity


class Parameter(Entity):
    """Abstract base class for ``DatafileParameter``,
    ``DatasetParameter``, ``InvestigationParameter``,
    ``SampleParameter``, and ``DataCollectionParameter``."""
    InstAttr = frozenset(['id', 'numericValue', 'dateTimeValue', 'stringValue', 
                          'rangeBottom', 'rangeTop', 'error'])
    InstRel = frozenset(['type'])


class Application(Entity):
    """Some piece of software."""
    BeanName = 'Application'
    Constraint = ('name', 'version')
    InstAttr = frozenset(['id', 'name', 'version'])
    InstMRel = frozenset(['jobs'])


class Application43(Application):
    """Some piece of software."""
    Constraint = ('facility', 'name', 'version')
    InstRel = frozenset(['facility'])


class DataCollection(Entity):
    """A set of Datafiles and Datasets which can span investigations
    and facilities.  Note that it has no constraint fields.  It is
    expected that a DataCollection would be identified by its
    DataCollectionParameters or its relationship to a Job."""
    BeanName = 'DataCollection'
    InstMRel = frozenset(['dataCollectionDatafiles', 'dataCollectionDatasets', 
                          'dataCollectionParameters', 'jobsAsInput', 
                          'jobsAsOutput'])
    AttrAlias = {'parameters':'dataCollectionParameters'}
    SortAttrs = ['dataCollectionDatasets', 'dataCollectionDatafiles']


class DataCollection431(DataCollection):
    """A set of Datafiles and Datasets which can span investigations
    and facilities.  Note that it has no constraint fields.  It is
    expected that a DataCollection would be identified by its
    parameters or its relationship to a Job."""
    InstMRel = frozenset(['dataCollectionDatafiles', 'dataCollectionDatasets', 
                          'parameters', 'jobsAsInput', 'jobsAsOutput'])
    AttrAlias = {'dataCollectionParameters':'parameters'}


class DataCollectionDatafile(Entity):
    """Represents a many-to-many relationship between a DataCollection
    and its Datafiles."""
    BeanName = 'DataCollectionDatafile'
    Constraint = ('dataCollection', 'datafile')
    InstRel = frozenset(['dataCollection', 'datafile'])


class DataCollectionDataset(Entity):
    """Represents a many-to-many relationship between a DataCollection
    and its datasets."""
    BeanName = 'DataCollectionDataset'
    Constraint = ('dataCollection', 'dataset')
    InstRel = frozenset(['dataCollection', 'dataset'])


class DataCollectionParameter(Parameter):
    """A parameter associated with a DataCollection."""
    BeanName = 'DataCollectionParameter'
    Constraint = ('dataCollection', 'type')
    InstRel = frozenset(['dataCollection', 'type'])


class Datafile(Entity):
    """A data file."""
    BeanName = 'Datafile'
    Constraint = ('name', 'location', 'dataset')
    InstAttr = frozenset(['id', 'name', 'description', 'location', 'fileSize', 
                          'checksum', 'datafileCreateTime', 'datafileModTime', 
                          'doi'])
    InstRel = frozenset(['datafileFormat', 'dataset'])
    InstMRel = frozenset(['parameters', 'inputDatafiles', 'outputDatafiles', 
                          'sourceDatafiles', 'destDatafiles'])


class Datafile43(Datafile):
    """A data file."""
    Constraint = ('dataset', 'name')
    InstMRel = frozenset(['parameters', 'dataCollectionDatafiles', 
                          'sourceDatafiles', 'destDatafiles'])


class DatafileFormat(Entity):
    """A data file format."""
    BeanName = 'DatafileFormat'
    Constraint = ('facility', 'name', 'version')
    InstAttr = frozenset(['id', 'name', 'description', 'version', 'type'])
    InstRel = frozenset(['facility'])
    InstMRel = frozenset(['datafiles'])


class DatafileParameter(Parameter):
    """A parameter associated with a data file."""
    BeanName = 'DatafileParameter'
    Constraint = ('datafile', 'type')
    InstRel = frozenset(['datafile', 'type'])


class Dataset(Entity):
    """A collection of data files and part of an investigation."""
    BeanName = 'Dataset'
    Constraint = ('sample', 'investigation', 'name', 'type')
    InstAttr = frozenset(['id', 'name', 'description', 'location', 
                          'startDate', 'endDate', 'complete', 'doi'])
    InstRel = frozenset(['type', 'sample', 'investigation'])
    InstMRel = frozenset(['parameters', 'datafiles', 
                          'inputDatasets', 'outputDatasets'])


class Dataset43(Dataset):
    """A collection of data files and part of an investigation."""
    Constraint = ('investigation', 'name')
    InstMRel = frozenset(['parameters', 'datafiles', 'dataCollectionDatasets'])


class DatasetParameter(Parameter):
    """A parameter associated with a data set."""
    BeanName = 'DatasetParameter'
    Constraint = ('dataset', 'type')
    InstRel = frozenset(['dataset', 'type'])


class DatasetType(Entity):
    """A type of data set."""
    BeanName = 'DatasetType'
    Constraint = ('facility', 'name')
    InstAttr = frozenset(['id', 'name', 'description'])
    InstRel = frozenset(['facility'])
    InstMRel = frozenset(['datasets'])


class Facility(Entity):
    """An experimental facility."""
    BeanName = 'Facility'
    Constraint = ('name',)
    InstAttr = frozenset(['id', 'name', 'fullName', 'description', 'url', 
                          'daysUntilRelease'])
    InstMRel = frozenset(['instruments', 'facilityCycles', 'investigations', 
                          'parameterTypes', 'datafileFormats', 'datasetTypes', 
                          'sampleTypes', 'investigationTypes'])


class Facility43(Facility):
    """An experimental facility."""
    InstMRel = frozenset(['instruments', 'facilityCycles', 'investigations', 
                          'parameterTypes', 'datafileFormats', 'datasetTypes', 
                          'sampleTypes', 'investigationTypes', 'applications'])


class FacilityCycle(Entity):
    """An operating cycle within a facility"""
    BeanName = 'FacilityCycle'
    Constraint = ('facility', 'name')
    InstAttr = frozenset(['id', 'name', 'description', 'startDate', 'endDate'])
    InstRel = frozenset(['facility'])
    InstMRel = frozenset(['investigations'])


class FacilityCycle43(FacilityCycle):
    """An operating cycle within a facility."""
    InstMRel = frozenset([])


class Group(Entity):
    """A group of users."""
    BeanName = 'Group'
    Constraint = ('name',)
    InstAttr = frozenset(['id', 'name'])
    InstMRel = frozenset(['userGroups', 'rules'])

    def addUsers(self, users):
        ugs = []
        uids = set()
        for u in users:
            if u.id in uids:
                continue
            ugs.append(self.client.new('userGroup', user=u, grouping=self))
            uids.add(u.id)
        if ugs:
            self.client.createMany(ugs)

    def getUsers(self, attribute=None):
        if attribute is not None:
            query = ("User.%s <-> UserGroup <-> %s [id=%d]" 
                     % (attribute, self.BeanName, self.id))
        else:
            query = ("User <-> UserGroup <-> %s [id=%d]" 
                     % (self.BeanName, self.id))
        return self.client.search(query)


class Group43(Group):
    """A group of users."""
    BeanName = 'Grouping'


class Group44(Group43):
    """A group of users."""
    InstMRel = frozenset(['userGroups', 'rules', 'investigationGroups'])


class InputDatafile(Entity):
    """Many to many relationship between data file as input and a job."""
    BeanName = 'InputDatafile'
    InstRel = frozenset(['job', 'datafile'])


class InputDataset(Entity):
    """Many to many relationship between data set as input and a job."""
    BeanName = 'InputDataset'
    InstRel = frozenset(['job', 'dataset'])


class Instrument(Entity):
    """Used by a user within an investigation."""
    BeanName = 'Instrument'
    Constraint = ('facility', 'name')
    InstAttr = frozenset(['id', 'name', 'fullName', 'description', 'type'])
    InstRel = frozenset(['facility'])
    InstMRel = frozenset(['instrumentScientists', 'investigations'])

    def addInstrumentScientists(self, users):
        iss = []
        for u in users:
            iss.append(self.client.new('instrumentScientist', 
                                       instrument=self, user=u))
        if iss:
            self.client.createMany(iss)

    def getInstrumentScientists(self, attribute=None):
        if attribute is not None:
            query = ("User.%s <-> InstrumentScientist <-> Instrument [id=%d]" 
                     % (attribute, self.id))
        else:
            query = ("User <-> InstrumentScientist <-> Instrument [id=%d]" 
                     % (self.id))
        return self.client.search(query)


class Instrument43(Instrument):
    """Used by a user within an investigation."""
    InstAttr = frozenset(['id', 'name', 'fullName', 'description', 'type', 
                          'url'])
    InstMRel = frozenset(['instrumentScientists', 'investigationInstruments'])


class InstrumentScientist(Entity):
    """Relationship between an ICAT user as an instrument scientist
    and the instrument."""
    BeanName = 'InstrumentScientist'
    Constraint = ('user', 'instrument')
    InstRel = frozenset(['user', 'instrument'])


class Investigation(Entity):
    """An investigation or experiment."""
    BeanName = 'Investigation'
    Constraint = ('name', 'visitId', 'facilityCycle', 'instrument')
    InstAttr = frozenset(['id', 'name', 'title', 'summary', 'doi', 'visitId', 
                          'startDate', 'endDate', 'releaseDate'])
    InstRel = frozenset(['type', 'facility', 'instrument', 'facilityCycle'])
    InstMRel = frozenset(['parameters', 'investigationUsers', 'keywords', 
                          'publications', 'samples', 'datasets', 'shifts', 
                          'studyInvestigations'])

    def addInstrument(self, instrument):
        self.get()
        self.instrument = instrument
        self.update()

    def addKeywords(self, keywords):
        kws = []
        for k in keywords:
            kws.append(self.client.new('keyword', name=k, investigation=self))
        if kws:
            self.client.createMany(kws)

    def addInvestigationUsers(self, users, role='Investigator'):
        ius = []
        for u in users:
            ius.append(self.client.new('investigationUser', 
                                       investigation=self, user=u, role=role))
        if ius:
            self.client.createMany(ius)


class Investigation43(Investigation):
    """An investigation or experiment."""
    Constraint = ('facility', 'name', 'visitId')
    InstRel = frozenset(['type', 'facility'])
    InstMRel = frozenset(['parameters', 'investigationInstruments', 
                          'investigationUsers', 'keywords', 
                          'publications', 'samples', 'datasets', 'shifts', 
                          'studyInvestigations'])

    def addInstrument(self, instrument):
        ii = self.client.new('investigationInstrument', 
                             investigation=self, instrument=instrument)
        ii.create()


class Investigation44(Investigation43):
    """An investigation or experiment."""
    InstMRel = frozenset(['parameters', 'investigationInstruments', 
                          'investigationUsers', 'keywords', 
                          'publications', 'samples', 'datasets', 'shifts', 
                          'studyInvestigations', 'investigationGroups'])


class InvestigationGroup(Entity):
    """Many to many relationship between investigation and group which might be used within authorization rules. Please see UserInvestigation"""
    BeanName = 'InvestigationGroup'
    Constraint = ('grouping', 'investigation')
    InstRel = frozenset(['investigation', 'grouping'])


class InvestigationInstrument(Entity):
    """Represents a many-to-many relationship between an investigation
    and the instruments assigned."""
    BeanName = 'InvestigationInstrument'
    Constraint = ('investigation', 'instrument')
    InstRel = frozenset(['investigation', 'instrument'])


class InvestigationParameter(Parameter):
    """A parameter associated with an investigation."""
    BeanName = 'InvestigationParameter'
    Constraint = ('investigation', 'type')
    InstRel = frozenset(['investigation', 'type'])


class InvestigationType(Entity):
    """A type of investigation."""
    BeanName = 'InvestigationType'
    Constraint = ('name', 'facility')
    InstAttr = frozenset(['id', 'name', 'description'])
    InstRel = frozenset(['facility'])
    InstMRel = frozenset(['investigations'])


class InvestigationUser(Entity):
    """Many to many relationship between investigation and user."""
    BeanName = 'InvestigationUser'
    Constraint = ('user', 'investigation')
    InstAttr = frozenset(['id', 'role'])
    InstRel = frozenset(['user', 'investigation'])


class Job(Entity):
    """A run of an application with its related inputs and outputs."""
    BeanName = 'Job'
    InstRel = frozenset(['application'])
    InstMRel = frozenset(['inputDatafiles', 'inputDatasets', 
                          'outputDatafiles', 'outputDatasets'])
    SortAttrs = ['application']


class Job43(Job):
    """A run of an application with its related inputs and outputs."""
    InstAttr = frozenset(['id', 'arguments'])
    InstRel = frozenset(['application', 'inputDataCollection', 
                         'outputDataCollection'])
    InstMRel = frozenset([])
    SortAttrs = ['application', 'arguments']


class Keyword(Entity):
    """A Keyword related to an investigation."""
    BeanName = 'Keyword'
    Constraint = ('name', 'investigation')
    InstAttr = frozenset(['id', 'name'])
    InstRel = frozenset(['investigation'])


class NotificationRequest(Entity):
    """Registers a request for a JMS notification to be sent out."""
    BeanName = 'NotificationRequest'
    Constraint = ('name',)
    InstAttr = frozenset(['id', 'name', 'what', 'crudFlags', 'datatypes', 
                          'destType', 'jmsOptions'])


class Log(Entity):
    """To store call logs if configured in icat.properties."""
    BeanName = 'Log'
    InstAttr = frozenset(['id', 'query', 'operation', 'entityId', 'entityName', 
                          'duration'])


class OutputDatafile(Entity):
    """Many to many relationship between data file as output and a job."""
    BeanName = 'OutputDatafile'
    InstRel = frozenset(['job', 'datafile'])


class OutputDataset(Entity):
    """Many to many relationship between data set as output and a job."""
    BeanName = 'OutputDataset'
    InstRel = frozenset(['job', 'dataset'])


class ParameterType(Entity):
    """A parameter type with unique name and units."""
    BeanName = 'ParameterType'
    Constraint = ('facility', 'name', 'units')
    InstAttr = frozenset(['id', 'name', 'description', 'valueType', 'units', 
                          'unitsFullName', 'minimumNumericValue', 
                          'maximumNumericValue', 'enforced', 'verified', 
                          'applicableToDatafile', 'applicableToDataset', 
                          'applicableToSample', 'applicableToInvestigation'])
    InstRel = frozenset(['facility'])
    InstMRel = frozenset(['datafileParameters', 'datasetParameters', 
                          'sampleParameters', 'investigationParameters', 
                          'permissibleStringValues'])


class ParameterType43(ParameterType):
    """A parameter type with unique name and units."""
    InstAttr = frozenset(['id', 'name', 'description', 'valueType', 'units', 
                          'unitsFullName', 'minimumNumericValue', 
                          'maximumNumericValue', 'enforced', 'verified', 
                          'applicableToDatafile', 'applicableToDataset', 
                          'applicableToSample', 'applicableToInvestigation', 
                          'applicableToDataCollection'])
    InstMRel = frozenset(['datafileParameters', 'datasetParameters', 
                          'sampleParameters', 'investigationParameters', 
                          'dataCollectionParameters', 
                          'permissibleStringValues'])


class PermissibleStringValue(Entity):
    """Permissible value for string parameter types."""
    BeanName = 'PermissibleStringValue'
    Constraint = ('value', 'type')
    InstAttr = frozenset(['id', 'value'])
    InstRel = frozenset(['type'])


class PublicStep(Entity):
    """An allowed step for an INCLUDE identifed by the origin entity
    and the field name for navigation.  Including an entry here is
    much more efficient than having to use the authorization rules."""
    BeanName = 'PublicStep'
    Constraint = ('origin', 'field')
    InstAttr = frozenset(['id', 'origin', 'field'])


class Publication(Entity):
    """A publication."""
    BeanName = 'Publication'
    InstAttr = frozenset(['id', 'fullReference', 'url', 'doi', 'repository', 
                          'repositoryId'])
    InstRel = frozenset(['investigation'])
    SortAttrs = ['investigation', 'fullReference']


class RelatedDatafile(Entity):
    """Used to represent an arbitrary relationship between data files."""
    BeanName = 'RelatedDatafile'
    Constraint = ('sourceDatafile', 'destDatafile')
    InstAttr = frozenset(['id', 'relation'])
    InstRel = frozenset(['sourceDatafile', 'destDatafile'])


class Rule(Entity):
    """An authorization rule."""
    BeanName = 'Rule'
    InstAttr = frozenset(['id', 'what', 'crudFlags'])
    InstRel = frozenset(['group'])
    AttrAlias = {'grouping':'group'}
    SortAttrs = ['group', 'what']


class Rule43(Rule):
    """An authorization rule."""
    InstRel = frozenset(['grouping'])
    AttrAlias = {'group':'grouping'}
    SortAttrs = ['grouping', 'what']


class Sample(Entity):
    """A sample to be used in an investigation."""
    BeanName = 'Sample'
    Constraint = ('name', 'type', 'investigation')
    InstAttr = frozenset(['id', 'name'])
    InstRel = frozenset(['type', 'investigation'])
    InstMRel = frozenset(['parameters', 'datasets'])


class Sample43(Sample):
    """A sample to be used in an investigation."""
    Constraint = ('investigation', 'name')


class SampleParameter(Parameter):
    """A parameter associated with a sample."""
    BeanName = 'SampleParameter'
    Constraint = ('sample', 'type')
    InstRel = frozenset(['sample', 'type'])


class SampleType(Entity):
    """A sample to be used in an investigation."""
    BeanName = 'SampleType'
    Constraint = ('name', 'facility')
    InstAttr = frozenset(['id', 'name', 'molecularFormula', 
                          'safetyInformation'])
    InstRel = frozenset(['facility'])
    InstMRel = frozenset(['samples'])


class SampleType43(SampleType):
    """A sample to be used in an investigation."""
    Constraint = ('facility', 'name', 'molecularFormula')


class Shift(Entity):
    """A period of time related to an investigation."""
    BeanName = 'Shift'
    Constraint = ('investigation', 'startDate', 'endDate')
    InstAttr = frozenset(['id', 'comment', 'startDate', 'endDate'])
    InstRel = frozenset(['investigation'])


class Study(Entity):
    """A study which may be related to an investigation."""
    BeanName = 'Study'
    InstAttr = frozenset(['id', 'name', 'description', 'status', 'startDate'])
    InstRel = frozenset(['user'])
    InstMRel = frozenset(['studyInvestigations'])
    SortAttrs = ['name']


class StudyInvestigation(Entity):
    """Many to many relationship between study and investigation."""
    BeanName = 'StudyInvestigation'
    Constraint = ('study', 'investigation')
    InstRel = frozenset(['study', 'investigation'])


class User(Entity):
    """A user of the facility."""
    BeanName = 'User'
    Constraint = ('name',)
    InstAttr = frozenset(['id', 'name', 'fullName'])
    InstMRel = frozenset(['investigationUsers', 'instrumentScientists', 
                          'userGroups', 'studies'])


class UserGroup(Entity):
    """Many to many relationship between user and group."""
    BeanName = 'UserGroup'
    Constraint = ('user', 'group')
    InstRel = frozenset(['user', 'group'])
    AttrAlias = {'grouping':'group'}


class UserGroup43(UserGroup):
    """Many to many relationship between user and group."""
    Constraint = ('user', 'grouping')
    InstRel = frozenset(['user', 'grouping'])
    AttrAlias = {'group':'grouping'}


