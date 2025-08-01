import pytest
from unittest.mock import patch
from lipidlibrarian.api.LipidMapsAPI import LipidMapsAPI
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid import get_adducts
from lipidlibrarian.lipid.Nomenclature import Level
from .mock_http_helper import load_or_record_response


test_development = True  # This flag enables request downloads. Toggle this to False in CI.


@pytest.fixture(params=["LMGP01010902"])
def sample_ids(request):
    return request.param


@pytest.fixture(params=[(816.6477, 0.01, get_adducts(['+H+']))])
def sample_mz(request):
    return request.param


@pytest.fixture(params=[("PC(18:1/20:0)", Level.structural_lipid_species)])
def sample_names(request):
    return request.param


def test_query_id(sample_ids):
    api = LipidMapsAPI()
    real_method = LipidAPI.execute_http_query.__get__(api, LipidAPI)

    with patch.object(LipidAPI, "execute_http_query") as mock_exec:
        mock_exec.side_effect = lambda url: load_or_record_response(
            url, real_method, test_development
        )
        result = api.query_id(sample_ids)
        assert result


def test_query_mz(sample_mz):
    api = LipidMapsAPI()
    real_method = LipidAPI.execute_http_query.__get__(api, LipidAPI)

    with patch.object(LipidAPI, "execute_http_query") as mock_exec:
        mock_exec.side_effect = lambda url: load_or_record_response(
            url, real_method, test_development
        )
        result = api.query_mz(sample_mz[0], sample_mz[1], sample_mz[2])
        assert result


def test_query_name(sample_names):
    api = LipidMapsAPI()
    real_method = LipidAPI.execute_http_query.__get__(api, LipidAPI)

    with patch.object(LipidAPI, "execute_http_query") as mock_exec:
        mock_exec.side_effect = lambda url: load_or_record_response(
            url, real_method, test_development
        )
        result = api.query_name(sample_names[0], level=sample_names[1])
        assert result
