import pytest
from lipidlibrarian.api.Alex123API import Alex123API
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid import get_adducts
from lipidlibrarian.lipid.Nomenclature import Level


@pytest.fixture(params=[("PC 18:1-20:0", Level.molecular_lipid_species)])
def sample_names(request):
    return request.param


def test_query_name(sample_names):
    api = Alex123API()

    result = api.query_name(sample_names[0], level=sample_names[1])
    assert result
