import pytest
from unittest.mock import patch
from lipidlibrarian.api.SwissLipidsAPI import SwissLipidsAPI
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid.Nomenclature import Level
from test.mock_http_helper import load_or_record_response

from .lipid_name_test_matrix import LIPID_NAME_TEST_MATRIX


test_development = True  # This flag enables request downloads. Toggle this to False in CI.


@pytest.fixture(scope="session")
def swisslipids_api(pytestconfig):
    return SwissLipidsAPI()


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


@pytest.mark.parametrize("lipid_class,lipid_level,lipid_name,expects", list(lipid_name_test_cases()))
def test_query_name(swisslipids_api, lipid_class, lipid_level, lipid_name, expects):
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

        results = swisslipids_api.query_name(lipid_name, level=lipid_level)

        found_swisslipids_results = False
        found_swisslipids_mass = False
        found_swisslipids_adducts = False
        found_swisslipids_reactions = False

        for result in results:
            if result.nomenclature.level <= lipid_level:
                found_swisslipids_results = True
                for mass in result.masses:
                    for source in mass.sources:
                        if source.source == 'swisslipids':
                            found_swisslipids_mass = True
                for adduct in result.adducts:
                    for source in adduct.sources:
                        if source.source == 'swisslipids':
                            found_swisslipids_adducts = True
                for reaction in result.reactions:
                    for source in reaction.sources:
                        if source.source == 'swisslipids':
                            found_swisslipids_smiles = True

        if expects['has_swisslipids_results']:
            assert found_swisslipids_results
        else:
            assert not found_swisslipids_results

        if expects['has_swisslipids_mass']:
            assert found_swisslipids_mass
        else:
            assert not found_swisslipids_mass

        if expects['has_swisslipids_adducts']:
            assert found_swisslipids_adducts
        else:
            assert not found_swisslipids_adducts

        if expects['has_swisslipids_reactions']:
            assert found_swisslipids_reactions
        else:
            assert not found_swisslipids_reactions
