import pytest
from unittest.mock import patch
from lipidlibrarian.api.LipidMapsAPI import LipidMapsAPI
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid import get_adducts
from lipidlibrarian.lipid.Nomenclature import Level
from test.mock_http_helper import load_or_record_response

from .lipid_name_test_matrix import LIPID_NAME_TEST_MATRIX


test_development = True  # This flag enables request downloads. Toggle this to False in CI.


@pytest.fixture(scope="session")
def lipidmaps_api(pytestconfig):
    return LipidMapsAPI()


def lipid_name_test_cases():
    for lipid_class, levels in LIPID_NAME_TEST_MATRIX.items():
        for level, spec in levels.items():
            yield pytest.param(
                lipid_class,
                level,
                spec["name"],
                spec["expects"],
                id=f"{lipid_class}-{level.name}",
            )


@pytest.fixture(params=["LMGP01010902"])
def sample_ids(request):
    return request.param


@pytest.fixture(params=[(816.6477, 0.01, get_adducts(['+H+']))])
def sample_mz(request):
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


@pytest.mark.parametrize("lipid_class,lipid_level,lipid_name,expects", list(lipid_name_test_cases()))
def test_query_name(lipidmaps_api, lipid_class, lipid_level, lipid_name, expects):
    # Keep a reference to the unpatched function
    real_execute_http_query = LipidAPI.execute_http_query

    def side_effect(self, url: str):
        # Call the real method through a closure so load_or_record_response
        # can execute it when needed.
        return load_or_record_response(
            url=url,
            real_execute_http_query=lambda u: real_execute_http_query(self, u),
            test_development=test_development
        )

    with patch.object(LipidAPI, "execute_http_query", autospec=True) as mock_exec:
        mock_exec.side_effect = side_effect

        results = lipidmaps_api.query_name(lipid_name, level=lipid_level)

        found_lipidmaps_results = False
        found_lipidmaps_mass = False
        found_lipidmaps_adducts = False
        found_lipidmaps_smiles = False
        found_lipidmaps_inchi = False

        for result in results:
            if result.nomenclature.level <= lipid_level:
                found_lipidmaps_results = True
                for mass in result.masses:
                    for source in mass.sources:
                        if source.source == 'lipidmaps':
                            found_lipidmaps_mass = True
                for adduct in result.adducts:
                    for source in adduct.sources:
                        if source.source == 'lipidmaps':
                            found_lipidmaps_adducts = True
                for database_identifier in result.database_identifiers:
                    for source in database_identifier.sources:
                        if source.source == 'lipidmaps':
                            if database_identifier.identifier == 'smiles':
                                found_lipidmaps_smiles = True
                            if database_identifier.identifier == 'inchi':
                                found_lipidmaps_inchi = True

        if expects['has_lipidmaps_results']:
            assert found_lipidmaps_results
        else:
            assert not found_lipidmaps_results

        if expects['has_lipidmaps_mass']:
            assert found_lipidmaps_mass
        else:
            assert not found_lipidmaps_mass

        if expects['has_lipidmaps_adducts']:
            assert found_lipidmaps_adducts
        else:
            assert not found_lipidmaps_adducts

        if expects['has_lipidmaps_smiles']:
            assert found_lipidmaps_smiles
        else:
            assert not found_lipidmaps_smiles

        if expects['has_lipidmaps_inchi']:
            assert found_lipidmaps_inchi
        else:
            assert not found_lipidmaps_inchi
