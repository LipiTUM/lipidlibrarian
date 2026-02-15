import pytest
from lipidlibrarian.api.Alex123API import Alex123API
from lipidlibrarian.api.Alex123API import is_sql_reachable
from lipidlibrarian.api.LipidAPI import LipidAPI
from lipidlibrarian.lipid import get_adducts
from lipidlibrarian.lipid.Nomenclature import Level


from .lipid_name_test_matrix import LIPID_NAME_TEST_MATRIX


@pytest.fixture(scope="session")
def alex123_api(pytestconfig):
    backend = pytestconfig.getoption("--alex123-backend")

    sql_args = {
        "host": pytestconfig.getoption("--alex123-sql-host"),
        "port": pytestconfig.getoption("--alex123-sql-port"),
        "user": pytestconfig.getoption("--alex123-sql-user"),
        "password": pytestconfig.getoption("--alex123-sql-password"),
        "database": pytestconfig.getoption("--alex123-sql-database"),
    }

    print("Creating Alex123API with backend:", backend, "SQL args:", sql_args)

    if backend == "auto":
        if is_sql_reachable(sql_args):
            return Alex123API(sql_args)
        return Alex123API()
    elif backend == "sql":
        if not is_sql_reachable(sql_args):
            pytest.exit(
                "Alex123 backend set to 'sql' but SQL database is not reachable",
                returncode=1,
            )
        return Alex123API(sql_args)
    elif backend == "file":
        return Alex123API()
    else:
        raise RuntimeError(f"Unknown backend mode: {backend}")

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

@pytest.mark.parametrize("lipid_class,lipid_level,lipid_name,expects", list(lipid_name_test_cases()))
def test_query_name(alex123_api, lipid_class, lipid_level, lipid_name, expects):
    results = alex123_api.query_name(lipid_name, level=lipid_level)

    found_alex123_results = False
    found_alex123_fragments = False

    for result in results:
        if result.nomenclature.level <= lipid_level:
            found_alex123_results = True
            for adduct in result.adducts:
                for fragment in adduct.fragments:
                    for source in fragment.sources:
                        if source.source == 'alex123':
                            found_alex123_fragments = True
                            break

    if expects['has_alex123_results']:
        assert found_alex123_results
    else:
        assert not found_alex123_results

    if expects['has_alex123_fragments']:
        assert found_alex123_fragments
    else:
        assert not found_alex123_fragments
