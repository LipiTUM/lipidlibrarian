import argparse
import pandas as pd
import sqlalchemy
from importlib.resources import files
from lipidlibrarian.api.Alex123API import Alex123DBConnectorHDF


def is_sql_db_empty(engine) -> bool:
    inspector = sqlalchemy.inspect(engine)
    tables = inspector.get_table_names()
    return len(tables) == 0


def sync_hdf5_to_sql(sql_url: str):
    """Populates SQL DB with tables from HDF5 if DB is empty."""
    hdf5_path = str(files('lipidlibrarian')) + '/data/alex123/alex123_db.h5'
    engine = sqlalchemy.create_engine(sql_url)
    chunksize = 10000

    if not is_sql_db_empty(engine):
        print("SQL database is not empty. Aborting.")
        return

    hdf5_adapter = Alex123DBConnectorHDF(hdf5_path)

    for table_name in hdf5_adapter.get_table_names():
        print(f"Writing table '{table_name}'...")
        first = True

        for chunk in hdf5_adapter.iterate_over_table(table_name, chunksize):
            chunk.to_sql(
                table_name,
                con=engine,
                index=False,
                if_exists="replace" if first else "append",
                method="multi",
                chunksize=chunksize,
            )
            first = False

    print("Successfully populated SQL database.")


def main():
    parser = argparse.ArgumentParser(
        description="Populate SQL database from HDF5 file if it's empty."
    )
    parser.add_argument(
        "--sql", required=True, help="SQLAlchemy URL to the target database"
    )
    args = parser.parse_args()

    sync_hdf5_to_sql(args.sql)


if __name__ == "__main__":
    main()
