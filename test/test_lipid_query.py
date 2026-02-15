import pytest
from unittest.mock import patch
from lipidlibrarian.LipidQuery import LipidQuery
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid import get_adducts
from lipidlibrarian.lipid.Lipid import Lipid
from lipidlibrarian.lipid.Nomenclature import Level
from .mock_http_helper import load_or_record_response


test_development = True  # This flag enables request downloads. Toggle this to False in CI.


@pytest.fixture(params=["SLM:000487065", "LMGP01010902"])
def sample_ids(request):
    return request.param


def test_lipidquery_id(sample_ids):
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

        q = LipidQuery(
            input_string=sample_ids,
            requeries=1,
        )
        result = q.query()
        assert result


def test_lipid_merge_raises_on_wrong_type():
    a = Lipid()
    with pytest.raises(ValueError):
        a.merge(object())


def test_merge_keeps_exact_level_only():
    """
    If lipids exist at the query level -> keep only those.
    """
    q = LipidQuery("PC 18:0_20:1", method="name")

    lipid_1 = Lipid()
    lipid_1.nomenclature.name = 'PC 18:0_20:1'
    lipid_2 = Lipid()
    lipid_2.nomenclature.name = 'PC 18:1(9Z)/20:0'
    lipid_3 = Lipid()
    lipid_3.nomenclature.name = 'PC 38:1'

    q.lipids = [lipid_1, lipid_2, lipid_3]
    q.merge_lipids()

    assert len(q.lipids) == 1
    assert q.lipids[0].nomenclature.level == Level.molecular_lipid_species
    assert q.lipids[0].nomenclature.get_name() == "PC 18:0_20:1"


def test_merge_keeps_all_higher_if_no_exact():
    """
    If no lipids at the query level, but there are higher -> keep all higher level lipids and merge lower ones into them.
    """
    q = LipidQuery('PC 18:0_20:0', method="name")

    lipid_1 = Lipid()
    lipid_1.nomenclature.name = 'PC 18:0/20:1'
    lipid_2 = Lipid()
    lipid_2.nomenclature.name = 'PC 18:1(9Z)/20:0'
    lipid_3 = Lipid()
    lipid_3.nomenclature.name = 'PC 38:1'

    q.lipids = [lipid_1, lipid_2, lipid_3]
    q.merge_lipids()

    assert {l.nomenclature.level for l in q.lipids} == {Level.structural_lipid_species, Level.isomeric_lipid_species}
    assert {l.nomenclature.get_name() for l in q.lipids} == {"PC 18:0/20:1", "PC 18:1(9Z)/20:0"}


def test_merge_keeps_all_if_no_exact_or_higher():
    """
    If no lipids at the query level and no higher level lipids exist -> keep all lipids.
    """
    q = LipidQuery("PC 18:0/20:0", method="name")

    lipid_1 = Lipid()
    lipid_1.nomenclature.name = "PC 34:1"
    lipid_2 = Lipid()
    lipid_2.nomenclature.name = "PC 18:1_20:0"

    q.lipids = [lipid_1, lipid_2]
    q.merge_lipids()

    assert len(q.lipids) == 2
    assert {l.nomenclature.level for l in q.lipids} == {Level.sum_lipid_species, Level.molecular_lipid_species}


def test_merge_deduplicates_within_kept_level():
    """
    Within the kept set, identical lipids are merged/deduplicated using Lipid.merge (same level + same nomenclature name).
    """
    q = LipidQuery("PC 18:1_20:0", method="name")

    lipid_1 = Lipid()
    lipid_1.nomenclature.name = "PC 18:1_20:0"
    lipid_2 = Lipid()
    lipid_2.nomenclature.name = "PC 18:1_20:0"

    q.lipids = [lipid_1, lipid_2]
    q.merge_lipids()

    assert len(q.lipids) == 1
    assert q.lipids[0].nomenclature.level == Level.molecular_lipid_species
    assert q.lipids[0].nomenclature.get_name() == "PC 18:1_20:0"
