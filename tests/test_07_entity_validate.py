"""Test adding a validation hook for entity objects.
"""

import pytest
import icat
import icat.config
from conftest import getConfig


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(confSection="nbour")
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="function")
def dataset(client, cleanup_objs):
    """Create a temporary Dataset for the tests.
    """
    inv = client.assertedSearch("Investigation [name='08100122-EF']")[0]
    dstype = client.assertedSearch("DatasetType [name='raw']")[0]
    dataset = client.new("Dataset",
                         name="test_07_entity_validate", complete=False,
                         investigation=inv, type=dstype)
    dataset.create()
    cleanup_objs.append(dataset)
    return dataset


def validate_param(self):
    """Validate parameter objects.

    Check that NUMERIC parameters have numericValue set and do not
    have stringValue or dateTimeValue set.
    """
    if self.type.valueType == "NUMERIC":
        if self.stringValue is not None:
            raise ValueError("NUMERIC parameter cannot set stringValue")
        if self.dateTimeValue is not None:
            raise ValueError("NUMERIC parameter cannot set dateTimeValue")
        if self.numericValue is None:
            raise ValueError("NUMERIC parameter must set numericValue")
    elif self.type.valueType == "STRING":
        if self.dateTimeValue is not None:
            raise ValueError("STRING parameter cannot set dateTimeValue")
        if self.numericValue is not None:
            raise ValueError("STRING parameter cannot set numericValue")
        if self.stringValue is None:
            raise ValueError("STRING parameter must set stringValue")
        query = ("PermissibleStringValue.value <-> ParameterType [id=%d]"
                 % self.type.id)
        permissibleValues = self.client.search(query)
        if permissibleValues and self.stringValue not in permissibleValues:
            raise ValueError("Invalid string value")
    elif self.type.valueType == "DATE_AND_TIME":
        if self.numericValue is not None:
            raise ValueError("DATE_AND_TIME parameter cannot set numericValue")
        if self.stringValue is not None:
            raise ValueError("DATE_AND_TIME parameter cannot set stringValue")
        if self.dateTimeValue is None:
            raise ValueError("DATE_AND_TIME parameter must set dateTimeValue")
    else:
        raise ValueError("Invalid valueType '%s'" % self.type.valueType)


def test_invalid_numeric_with_string_value(client, dataset):
    """Try setting stringValue on a NUMERIC parameter.
    """
    client.typemap['parameter'].validate = validate_param
    ptype = client.assertedSearch("ParameterType [name='Magnetic field']")[0]
    assert ptype.valueType == "NUMERIC"
    param = client.new("DatasetParameter", dataset=dataset, type=ptype)
    param.numericValue = 7
    param.stringValue = "seven"
    with pytest.raises(ValueError) as err:
        param.create()
    assert 'NUMERIC parameter cannot set stringValue' in str(err.value)
    assert param.id is None

def test_invalid_numeric_missing_value(client, dataset):
    """Try creating a NUMERIC parameter without setting any value.
    """
    client.typemap['parameter'].validate = validate_param
    ptype = client.assertedSearch("ParameterType [name='Magnetic field']")[0]
    assert ptype.valueType == "NUMERIC"
    param = client.new("DatasetParameter", dataset=dataset, type=ptype)
    with pytest.raises(ValueError) as err:
        param.create()
    assert 'NUMERIC parameter must set numericValue' in str(err.value)
    assert param.id is None

def test_valid_numeric_value(client, dataset):
    """Create a valid NUMERIC parameter.
    """
    client.typemap['parameter'].validate = validate_param
    ptype = client.assertedSearch("ParameterType [name='Magnetic field']")[0]
    assert ptype.valueType == "NUMERIC"
    param = client.new("DatasetParameter", dataset=dataset, type=ptype)
    param.numericValue = 7
    param.create()
    assert param.id is not None

def test_valid_string_simple_value(client, dataset):
    """Create a simple STRING parameter.
    """
    client.typemap['parameter'].validate = validate_param
    ptype = client.assertedSearch("ParameterType [name='Comment']")[0]
    assert ptype.valueType == "STRING"
    param = client.new("DatasetParameter", dataset=dataset, type=ptype)
    param.stringValue = "Beam me up Scotty!"
    param.create()
    assert param.id is not None

def test_invalid_string_permissible_value(client, dataset):
    """Try creating a STRING parameter violating permissible values.
    """
    client.typemap['parameter'].validate = validate_param
    ptype = client.assertedSearch("ParameterType [name='Probe']")[0]
    assert ptype.valueType == "STRING"
    param = client.new("DatasetParameter", dataset=dataset, type=ptype)
    param.stringValue = "peanut"
    with pytest.raises(ValueError) as err:
        param.create()
    assert 'Invalid string value' in str(err.value)
    assert param.id is None

def test_valid_string_permissible_value(client, dataset):
    """Create a valid STRING parameter, picking a permissible value.
    """
    client.typemap['parameter'].validate = validate_param
    ptype = client.assertedSearch("ParameterType [name='Probe']")[0]
    assert ptype.valueType == "STRING"
    param = client.new("DatasetParameter", dataset=dataset, type=ptype)
    param.stringValue = "photon"
    param.create()
    assert param.id is not None
