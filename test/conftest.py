import pytest


def pytest_addoption(parser):
    group = parser.getgroup("alex123")

    group.addoption(
        "--alex123-backend",
        action="store",
        default="auto",
        choices=["auto", "sql", "file"],
        help="Backend selection for Alex123API: auto | sql | file",
    )

    group.addoption("--alex123-sql-host", type=str, default="localhost")
    group.addoption("--alex123-sql-port", type=int, default=3306)
    group.addoption("--alex123-sql-user", type=str, default="alex123")
    group.addoption("--alex123-sql-password", type=str, default="alex123")
    group.addoption("--alex123-sql-database", type=str, default="alex123")
