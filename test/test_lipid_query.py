import pytest
from unittest.mock import patch
from lipidlibrarian.LipidQuery import LipidQuery
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid import get_adducts
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
        )
        result = q.query()
        assert result
