import argparse
import sqlalchemy
from sqlalchemy import text
from importlib.resources import files
from lipidlibrarian.api.Alex123API import Alex123DBConnectorHDF


PRIMARY_KEYS = {
    "adduct":                   "adduct_id",
    "lipid_category":           "lipid_category_id",
    "lipid_class":              "lipid_class_id",
    "sum_lipid_species":        "sum_lipid_species_id",
    "molecular_lipid_species":  "molecular_lipid_species_id",
    "fragment":                 "fragment_id",
}

# Secondary indexes: (table, index_name, column(s))
SECONDARY_INDEXES = [
    ("fragment", "idx_frg_mls",  "molecular_lipid_species_id"),
    ("fragment", "idx_frg_adt",  "adduct_id"),
    ("fragment", "idx_frg_mass", "fragment_mass"),

    ("molecular_lipid_species", "idx_mls_sls",  "sum_lipid_species_id"),
    ("molecular_lipid_species", "idx_mls_name", "molecular_lipid_species_name"),

    ("sum_lipid_species", "idx_sls_mass", "sum_lipid_species_mass"),
    ("sum_lipid_species", "idx_sls_name", "sum_lipid_species_name"),
    ("sum_lipid_species", "idx_sls_cls",  "lipid_class_id"),

    ("lipid_class", "idx_cls_cat", "lipid_category_id"),

    ("adduct", "idx_adt_name", "adduct_name"),
]


def is_sql_db_empty(engine) -> bool:
    inspector = sqlalchemy.inspect(engine)
    tables = inspector.get_table_names()
    return len(tables) == 0


def add_primary_keys(engine) -> None:
    with engine.begin() as conn:
        for table, pk_col in PRIMARY_KEYS.items():
            print(f"  Adding primary key on {table}({pk_col})...")
            conn.execute(text(
                f"ALTER TABLE `{table}` ADD PRIMARY KEY (`{pk_col}`)"
            ))


def add_secondary_indexes(engine) -> None:
    with engine.begin() as conn:
        for table, index_name, column in SECONDARY_INDEXES:
            print(f"  Creating index {index_name} on {table}({column})...")
            conn.execute(text(
                f"CREATE INDEX `{index_name}` ON `{table}` (`{column}`)"
            ))


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
    
    print("Adding primary keys...")
    add_primary_keys(engine)

    print("Creating secondary indexes...")
    add_secondary_indexes(engine)

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
