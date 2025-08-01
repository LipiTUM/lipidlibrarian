import pytest
from unittest.mock import patch
from lipidlibrarian.api.SwissLipidsAPI import SwissLipidsAPI
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid import get_adducts
from lipidlibrarian.lipid.Nomenclature import Level
from .mock_http_helper import load_or_record_response


test_development = True  # This flag enables request downloads. Toggle this to False in CI.


@pytest.fixture(params=["SLM:000487065"])
def sample_ids(request):
    return request.param


@pytest.fixture(params=[("PC(18:1/20:0)", Level.structural_lipid_species), ("PC(18:1_20:0)", Level.molecular_lipid_species)])
def sample_names(request):
    return request.param


def test_query_id(sample_ids):
    api = SwissLipidsAPI()
    real_method = LipidAPI.execute_http_query.__get__(api, LipidAPI)

    with patch.object(LipidAPI, "execute_http_query") as mock_exec:
        mock_exec.side_effect = lambda url: load_or_record_response(
            url, real_method, test_development
        )
        result = api.query_id(sample_ids)
        assert result


def test_query_name(sample_names):
    api = SwissLipidsAPI()
    real_method = LipidAPI.execute_http_query.__get__(api, LipidAPI)

    with patch.object(LipidAPI, "execute_http_query") as mock_exec:
        mock_exec.side_effect = lambda url: load_or_record_response(
            url, real_method, test_development
        )
        result = api.query_name(sample_names[0], level=sample_names[1])
        assert result
