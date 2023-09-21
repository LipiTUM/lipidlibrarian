import copy
import logging
from collections.abc import Iterable
from importlib.resources import files

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine

from .LipidAPI import LipidAPI
from ..lipid import get_adduct
from ..lipid.Adduct import Adduct
from ..lipid.Adduct import Fragment
from ..lipid.Lipid import DatabaseIdentifier
from ..lipid.Lipid import Lipid
from ..lipid.Lipid import Mass
from ..lipid.Nomenclature import Level
from ..lipid.Nomenclature import Synonym
from ..lipid.Source import Source


class Alex123DBConnector():
    def __init__(self):
        pass

    def get_sum_lipid_species_by_name(self, names: set[str]) -> pd.DataFrame:
        raise NotImplementedError((
            "Alex123DBConnector is not intended to be used directly. Pleas instantiate Alex123DBConnectorSQL "
            "or Alex123DBConnectorHDF instead."
        ))

    def get_molecular_lipid_species_by_name(self, names: set[str]) -> pd.DataFrame:
        raise NotImplementedError((
            "Alex123DBConnector is not intended to be used directly. Pleas instantiate Alex123DBConnectorSQL "
            "or Alex123DBConnectorHDF instead."
        ))

    def get_fragment_by_molecular_lipid_species(self, ids: set[str]) -> pd.DataFrame:
        raise NotImplementedError((
            "Alex123DBConnector is not intended to be used directly. Pleas instantiate Alex123DBConnectorSQL "
            "or Alex123DBConnectorHDF instead."
        ))

    def get_molecular_lipid_species_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        raise NotImplementedError((
            "Alex123DBConnector is not intended to be used directly. Pleas instantiate Alex123DBConnectorSQL "
            "or Alex123DBConnectorHDF instead."
        ))

    def get_sum_lipid_species_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        raise NotImplementedError((
            "Alex123DBConnector is not intended to be used directly. Pleas instantiate Alex123DBConnectorSQL "
            "or Alex123DBConnectorHDF instead."
        ))

    def get_fragment_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        raise NotImplementedError((
            "Alex123DBConnector is not intended to be used directly. Pleas instantiate Alex123DBConnectorSQL "
            "or Alex123DBConnectorHDF instead."
        ))


class Alex123DBConnectorSQL(Alex123DBConnector):
    def __init__(self, sql_args: dict = None):
        super().__init__()
        logging.info(f"Alex123API: Connecting to ALEX123 SQL database...")
        self.db_connector = None
        # self.paramstyle can either be 'pyformat' for pymysql and psycopg2, or qmark for sqlite;
        # see PEP 249: paramstyle
        self.paramstyle = None

        if sql_args is None:
            return

        try:
            url = (
                f"mysql+pymysql://"
                f"{sql_args['user']}:{sql_args['password']}@{sql_args['host']}:{sql_args['port']}/"
                f"{sql_args['database']}"
            )
            engine = create_engine(url, echo=False)
            self.db_connector = engine.connect()
            self.db_type = 'pyformat'
            logging.info("Alex123API: Connection to MySQL DB successful.")
        except SQLAlchemyError as e:
            logging.error(f"Alex123API: Could not connect to ALEX123 SQL Database. The error '{e}' occurred.")
            logging.info("Alex123API: ALEX123 API disabled.")

    def get_sum_lipid_species_by_name(self, names: set[str]) -> pd.DataFrame:
        # get all sum species where name in names
        # merge with class
        # merge with category

        query = (
            "SELECT "
            "    sls.sum_lipid_species_id, "
            "    sls.sum_lipid_species_name, "
            "    sls.sum_lipid_species_mass, "
            "    lcl.lipid_class_id, "
            "    lcl.lipid_class_name, "
            "    lca.lipid_category_id, "
            "    lca.lipid_category_name "
            "FROM sum_lipid_species AS sls "
            "JOIN lipid_class AS lcl "
            "    ON sls.lipid_class_id = lcl.lipid_class_id "
            "JOIN lipid_category AS lca "
            "    ON lcl.lipid_category_id = lca.lipid_category_id "
            "WHERE sum_lipid_species_name {0} "  # param: list of sum lipid species names
            "; "
        )
        # Prepare query string for parameter insertion
        # Parameters:
        #     list(names)
        params = []
        if self.paramstyle == 'qmark':
            query = query.format('IN (' + ','.join('?' * len(names)) + ')')
            params.extend(names)
            params = tuple(params)
        else:
            query = query.format('IN %(sum_lipid_species_names)s')
            params = {'sum_lipid_species_names': tuple(names)}

        result = pd.read_sql(query, self.db_connector,  params=params)
        return result

    def get_molecular_lipid_species_by_name(self, names: set[str]) -> pd.DataFrame:
        # get all molecular species where name in names
        # merge with sum species
        # merge with class
        # merge with category

        query = (
            "SELECT "
            "    mls.molecular_lipid_species_id, "
            "    mls.molecular_lipid_species_name, "
            "    sls.sum_lipid_species_id, "
            "    sls.sum_lipid_species_name, "
            "    sls.sum_lipid_species_mass, "
            "    lcl.lipid_class_id, "
            "    lcl.lipid_class_name, "
            "    lca.lipid_category_id, "
            "    lca.lipid_category_name "
            "FROM molecular_lipid_species AS mls "
            "JOIN sum_lipid_species AS sls "
            "    ON mls.sum_lipid_species_id = sls.sum_lipid_species_id "
            "JOIN lipid_class AS lcl "
            "    ON sls.lipid_class_id = lcl.lipid_class_id "
            "JOIN lipid_category AS lca "
            "    ON lcl.lipid_category_id = lca.lipid_category_id "
            "WHERE molecular_lipid_species_name {0} "  # param: list of molecular lipid species names
            "; "
        )
        # Prepare query string for parameter insertion
        # Parameters:
        #     list(names)
        params = []
        if self.paramstyle == 'qmark':
            query = query.format('IN (' + ','.join('?' * len(names)) + ')')
            params.extend(names)
            params = tuple(params)
        else:
            query = query.format('IN %(molecular_lipid_species_names)s')
            params = {'molecular_lipid_species_names': tuple(names)}

        result = pd.read_sql(query, self.db_connector,  params=params)
        return result

    def get_fragment_by_molecular_lipid_species(self, ids: set[str]) -> pd.DataFrame:
        # get all fragments where molecular species id in ids
        # merge with adducts

        query = (
            "SELECT "
            "    frg.fragment_id, "
            "    frg.fragment_name, "
            "    frg.fragment_mass, "
            "    frg.fragment_polarity, "
            "    frg.fragment_sum_formula, "
            "    frg.molecular_lipid_species_id, "
            "    adt.adduct_id, "
            "    adt.adduct_name, "
            "    adt.adduct_mass, "
            "    adt.adduct_charge "
            "FROM "
            "    fragment AS frg "
            "JOIN adduct AS adt "
            "    ON adt.adduct_id = frg.adduct_id "
            "WHERE "
            "    frg.molecular_lipid_species_id {0} "  # param: list of molecular lipid species ids
            "; "
        )
        # Prepare query string for parameter insertion
        # Parameters:
        #     list(ids)
        params = []
        if self.paramstyle == 'qmark':
            query = query.format('IN (' + ','.join('?' * len(ids)) + ')')
            params.extend(ids)
            params = tuple(params)
        else:
            query = query.format('IN %(molecular_lipid_species_ids)s')
            params = {'molecular_lipid_species_ids': tuple(ids)}

        result = pd.read_sql(query, self.db_connector,  params=params)
        return result

    def get_molecular_lipid_species_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        # get max adduct mass
        #     => max_adduct_mass
        #
        # get all sum species where mz between mz - tolerance and mz + max_adduct_mass + tolerance
        # merge with molecular species
        #     => condition1
        #
        # get all fragments where adduct id in adduct_ids and molecular species id in molecular_lipid_species_ids
        #     => condition2
        #
        # get all molecular species where id in molecular_lipid_species_id
        # apply condition 1
        # apply condition 2
        # merge with sum species
        # merge with class
        # merge with category

        query = (
            "SET @mz = {0}; "  # param: mz
            "SET @tolerance = {1}; "  # param: tolerance
            "SELECT "
            "    @max_adduct_mass := max(adduct_mass) "
            "FROM adduct "
            "WHERE adduct_name {2}; "  # param: list of adducts
            "SELECT "
            "    mls.molecular_lipid_species_id, "
            "    mls.molecular_lipid_species_name, "
            "    sls.sum_lipid_species_id, "
            "    sls.sum_lipid_species_name, "
            "    sls.sum_lipid_species_mass, "
            "    lcl.lipid_class_id, "
            "    lcl.lipid_class_name, "
            "    lca.lipid_category_id, "
            "    lca.lipid_category_name "
            "FROM molecular_lipid_species as mls "
            "INNER JOIN ( "
            "    SELECT unique molecular_lipid_species_id "
            "    FROM molecular_lipid_species AS mls_inner "
            "    JOIN ( "
            "        SELECT sum_lipid_species_id "
            "        FROM sum_lipid_species "
            "        WHERE sum_lipid_species_mass BETWEEN @mz - @tolerance AND @mz + @max_adduct_mass + @tolerance "
            "    ) AS sls_inner "
            "        ON mls_inner.sum_lipid_species_id = sls_inner.sum_lipid_species_id "
            ") AS mls_condition1 "
            "    ON mls_condition1.molecular_lipid_species_id = mls.molecular_lipid_species_id "
            "INNER JOIN ( "
            "    SELECT unique "
            "        molecular_lipid_species_id "
            "    FROM "
            "        fragment as frg_inner "
            "    INNER JOIN ( "
            "        SELECT adduct_id "
            "        FROM adduct "
            "        WHERE adduct_name {3} "  # param: list of adducts
            "    ) as add_inner "
            "        ON add_inner.adduct_id = frg_inner.adduct_id "
            ") as mls_condition2 "
            "    ON mls_condition2.molecular_lipid_species_id = mls.molecular_lipid_species_id "
            "JOIN sum_lipid_species as sls "
            "    ON mls.sum_lipid_species_id = sls.sum_lipid_species_id "
            "JOIN lipid_class as lcl "
            "    ON sls.lipid_class_id = lcl.lipid_class_id "
            "JOIN lipid_category as lca "
            "    ON lcl.lipid_category_id = lca.lipid_category_id "
            "; "
        )
        # Prepare query string for parameter insertion
        # Parameters:
        #     mz, tolerance, list(adducts), list(adducts)
        params = []
        if self.paramstyle == 'qmark':
            query = query.format(
                '?',
                '?',
                'IN (' + ','.join('?' * len(adducts)) + ')',
                'IN (' + ','.join('?' * len(adducts)) + ')'
            )
            params.append(str(mz))
            params.append(str(tolerance))
            params.extend(adducts)
            params.extend(adducts)
            params = tuple(params)
        else:
            query = query.format(
                '%(mz)f',
                '%(tolerance)f',
                'IN %(adducts)s',
                'IN %(adducts)s'
            )
            params = {'mz': mz,
                      'tolerance': tolerance,
                      'adducts': tuple(adducts)
            }

        result = pd.read_sql(query, self.db_connector,  params=params)
        return result

    def get_sum_lipid_species_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        # get max adduct mass
        #     => max_adduct_mass
        #
        # get all sum species where mz between mz - tolerance and mz + max_adduct_mass + tolerance
        # merge with molecular species
        #     => condition1
        #
        # get all fragments where adduct id in adduct_ids and molecular species id in molecular_lipid_species_ids
        #     => condition2
        #
        # get all sum species which have a molecular species where id in molecular_lipid_species_id
        # apply condition 1
        # apply condition 2
        # merge with sum species
        # merge with class
        # merge with category

        query = (
            "SET @mz = {0}; "  # param: mz
            "SET @tolerance = {1}; "  # param: tolerance
            "SELECT "
            "    @max_adduct_mass := max(adduct_mass) "
            "FROM adduct "
            "WHERE adduct_name {2}; "  # param: list of adducts
            "SELECT "
            "    sls.sum_lipid_species_id, "
            "    sls.sum_lipid_species_name, "
            "    sls.sum_lipid_species_mass, "
            "    lcl.lipid_class_id, "
            "    lcl.lipid_class_name, "
            "    lca.lipid_category_id, "
            "    lca.lipid_category_name "
            "FROM molecular_lipid_species as mls "
            "INNER JOIN ( "
            "    SELECT unique molecular_lipid_species_id "
            "    FROM molecular_lipid_species AS mls_inner "
            "    JOIN ( "
            "        SELECT sum_lipid_species_id "
            "        FROM sum_lipid_species "
            "        WHERE sum_lipid_species_mass BETWEEN @mz - @tolerance AND @mz + @max_adduct_mass + @tolerance "
            "    ) AS sls_inner "
            "        ON mls_inner.sum_lipid_species_id = sls_inner.sum_lipid_species_id "
            ") AS mls_condition1 "
            "    ON mls_condition1.molecular_lipid_species_id = mls.molecular_lipid_species_id "
            "INNER JOIN ( "
            "    SELECT unique "
            "        molecular_lipid_species_id "
            "    FROM "
            "        fragment as frg_inner "
            "    INNER JOIN ( "
            "        SELECT adduct_id "
            "        FROM adduct "
            "        WHERE adduct_name {3} "  # param: list of adducts
            "    ) as add_inner "
            "        ON add_inner.adduct_id = frg_inner.adduct_id "
            ") as mls_condition2 "
            "    ON mls_condition2.molecular_lipid_species_id = mls.molecular_lipid_species_id "
            "JOIN sum_lipid_species as sls "
            "    ON mls.sum_lipid_species_id = sls.sum_lipid_species_id "
            "JOIN lipid_class as lcl "
            "    ON sls.lipid_class_id = lcl.lipid_class_id "
            "JOIN lipid_category as lca "
            "    ON lcl.lipid_category_id = lca.lipid_category_id "
            "; "
        )
        # Prepare query string for parameter insertion
        # Parameters:
        #     mz, tolerance, list(adducts), list(adducts)
        params = []
        if self.paramstyle == 'qmark':
            query = query.format(
                '?',
                '?',
                'IN (' + ','.join('?' * len(adducts)) + ')',
                'IN (' + ','.join('?' * len(adducts)) + ')'
            )
            params.append(str(mz))
            params.append(str(tolerance))
            params.extend(adducts)
            params.extend(adducts)
            params = tuple(params)
        else:
            query = query.format(
                '%(mz)f',
                '%(tolerance)f',
                'IN %(adducts)s',
                'IN %(adducts)s'
            )
            params = {'mz': mz,
                      'tolerance': tolerance,
                      'adducts': tuple(adducts)
            }

        result = pd.read_sql(query, self.db_connector,  params=params)
        return result

    def get_fragment_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        # get all adducts where adduct name in adducts
        #     => condition1
        # get all fragments where mass is between mz - tolerance and mz + tolerance
        # apply condition1
        # merge with adduct

        query = (
            "SET @mz = {0}; "  # param: mz
            "SET @tolerance = {1}; "  # param: tolerance
            "SELECT "
            "    frg.fragment_id, "
            "    frg.fragment_name, "
            "    frg.fragment_mass, "
            "    frg.fragment_sum_formula, "
            "    frg.fragment_polarity, "
            "    frg.molecular_lipid_species_id, "
            "    adt.adduct_id, "
            "    adt.adduct_name, "
            "    adt.adduct_mass, "
            "    adt.adduct_charge "
            "FROM "
            "    fragment AS frg "
            "INNER JOIN ( "
            "    SELECT "
            "        adduct_id "
            "    FROM "
            "        adduct "
            "    WHERE adduct_name {2} "  # param: list of adducts
            ") AS adt_condition1 "
            "    ON adt_condition1.adduct_id = frg.adduct_id "
            "JOIN adduct AS adt "
            "    ON frg.adduct_id = adt.adduct_id "
            "WHERE fragment_mass BETWEEN @mz - @tolerance AND @mz + @tolerance "
            "; "
        )
        # Prepare query string for parameter insertion
        # Parameters:
        #     mz, tolerance, list(adducts), list(adducts)
        params = []
        if self.paramstyle == 'qmark':
            query = query.format(
                '?',
                '?',
                'IN (' + ','.join('?' * len(adducts)) + ')'
            )
            params.append(str(mz))
            params.append(str(tolerance))
            params.extend(adducts)
            params = tuple(params)
        else:
            query = query.format(
                '%(mz)f',
                '%(tolerance)f',
                'IN %(adducts)s'
            )
            params = {'mz': mz,
                      'tolerance': tolerance,
                      'adducts': tuple(adducts)
            }

        result = pd.read_sql(query, self.db_connector,  params=params)
        return result


class Alex123DBConnectorHDF(Alex123DBConnector):
    def __init__(self, hdf_path: str):
        super().__init__()
        logging.info(f"Alex123API: Loading ALEX123 database from a HDF file...")
        try:
            with pd.HDFStore(str(hdf_path), 'r') as hdf5_store:
                self.alex123db = {
                    'adduct': hdf5_store['adduct'],
                    'lipid_category': hdf5_store['lipid_category'],
                    'lipid_class': hdf5_store['lipid_class'],
                    'sum_lipid_species': hdf5_store['sum_lipid_species'],
                    'molecular_lipid_species': hdf5_store['molecular_lipid_species'],
                    'fragment': hdf5_store['fragment']
                }
            logging.info(f"Alex123API: Loading ALEX123 database from a HDF file done.")
        except FileNotFoundError as e:
            logging.error(f"Alex123API: Could not find the ALEX123 HDF5 Database. The error '{e}' occurred.")
            logging.info("Alex123API: ALEX123 API disabled.")

    def get_database_table(self, table_name: str) -> pd.DataFrame:
        return self.alex123db[table_name]

    def get_sum_lipid_species_by_name(self, names: set[str]) -> pd.DataFrame:
        results = self.get_database_table('sum_lipid_species')[
            self.get_database_table('sum_lipid_species').sum_lipid_species_name.isin(names)
        ]
        results = pd.merge(results, self.get_database_table('lipid_class'), on='lipid_class_id')
        results = pd.merge(results, self.get_database_table('lipid_category'), on='lipid_category_id')
        return results
    
    def get_molecular_lipid_species_by_name(self, names: set[str]) -> pd.DataFrame:
        results = self.get_database_table('molecular_lipid_species')[
            self.get_database_table('molecular_lipid_species').molecular_lipid_species_name.isin(names)
        ]
        results = pd.merge(results, self.get_database_table('sum_lipid_species'), on='sum_lipid_species_id')
        results = pd.merge(results, self.get_database_table('lipid_class'), on='lipid_class_id')
        results = pd.merge(results, self.get_database_table('lipid_category'), on='lipid_category_id')
        return results
    
    def get_fragment_by_molecular_lipid_species(self, ids: set[str]) -> pd.DataFrame:
        results = self.get_database_table('fragment')[
            self.get_database_table('fragment').molecular_lipid_species_id.isin(ids)
        ]
        results = pd.merge(results, self.get_database_table('adduct'), on='adduct_id')
        return results
    
    def get_molecular_lipid_species_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        # get max adduct mass
        max_adduct_mass = 0
        for adduct in adducts:
            max_adduct_mass = max(adduct.adduct_mass, max_adduct_mass)

        # get possible adduct <-> molecular species combinations
        results_adducts = self.get_database_table('adduct')[
            self.get_database_table('adduct').adduct_name.isin([adduct.name for adduct in adducts])
        ]
        results_molecular_lipid_species = self.get_database_table('sum_lipid_species')[
            self.get_database_table('sum_lipid_species').sum_lipid_species_mass.between(
                mz - tolerance,
                mz + max_adduct_mass + tolerance
            )
        ]
        results_molecular_lipid_species = pd.merge(
            results_molecular_lipid_species,
            self.get_database_table('molecular_lipid_species'),
            on='sum_lipid_species_id'
        )
        results_molecular_lipid_species = self.get_database_table('fragment')[
            self.get_database_table('fragment').adduct_id.isin(results_adducts.adduct_id) &
            self.get_database_table('fragment').molecular_lipid_species_id.isin(
                results_molecular_lipid_species.molecular_lipid_species_id
            )
        ]
        
        results = self.get_database_table('molecular_lipid_species')[
            self.get_database_table('molecular_lipid_species').molecular_lipid_species_id.isin(
                results_molecular_lipid_species.molecular_lipid_species_id
            )
        ]
        results = pd.merge(results, self.get_database_table('sum_lipid_species'), on='sum_lipid_species_id')
        results = pd.merge(results, self.get_database_table('lipid_class'), on='lipid_class_id')
        results = pd.merge(results, self.get_database_table('lipid_category'), on='lipid_category_id')

        return results

    def get_sum_lipid_species_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        # get max adduct mass
        max_adduct_mass = 0
        for adduct in adducts:
            max_adduct_mass = max(adduct.adduct_mass, max_adduct_mass)

        # get possible adduct <-> molecular species combinations
        results_adducts = self.get_database_table('adduct')[
            self.get_database_table('adduct').adduct_name.isin([adduct.name for adduct in adducts])
        ]
        results_molecular_lipid_species = self.get_database_table('sum_lipid_species')[
            self.get_database_table('sum_lipid_species').sum_lipid_species_mass.between(
                mz - max_adduct_mass - tolerance,
                mz + max_adduct_mass + tolerance
            )
        ]
        results_molecular_lipid_species = pd.merge(
            results_molecular_lipid_species,
            self.get_database_table('molecular_lipid_species'),
            on='sum_lipid_species_id'
        )
        results_molecular_lipid_species = self.get_database_table('fragment')[
            self.get_database_table('fragment').adduct_id.isin(results_adducts.adduct_id) &
            self.get_database_table('fragment').molecular_lipid_species_id.isin(
                results_molecular_lipid_species.molecular_lipid_species_id
            )
        ]
        results_molecular_lipid_species = self.get_database_table('molecular_lipid_species')[
            self.get_database_table('molecular_lipid_species').molecular_lipid_species_id.isin(
                results_molecular_lipid_species.molecular_lipid_species_id
            )
        ]
        results_sum_lipid_species = pd.merge(
            results_molecular_lipid_species,
            self.get_database_table('molecular_lipid_species'),
            on='sum_lipid_species_id'
        )

        results = self.get_database_table('sum_lipid_species')[
            self.get_database_table('sum_lipid_species').sum_lipid_species_id.isin(
                results_sum_lipid_species.sum_lipid_species_id
            )
        ]
        results = pd.merge(results, self.get_database_table('lipid_class'), on='lipid_class_id')
        results = pd.merge(results, self.get_database_table('lipid_category'), on='lipid_category_id')

        return results

    def get_fragment_by_mz(self, mz: float, tolerance: float, adducts: list[Adduct]) -> pd.DataFrame:
        results_adducts = self.get_database_table('adduct')[
            self.get_database_table('adduct').adduct_name.isin([adduct.name for adduct in adducts])
        ]
        results = self.get_database_table('fragment')[
            self.get_database_table('fragment').adduct_id.isin(results_adducts.adduct_id) &
            self.get_database_table('fragment').fragment_mass.between(mz - tolerance, mz + tolerance)
        ]
        return results


class Alex123API(LipidAPI):
    """A class used to handle the connection to
    the lipitum.db file and extract lipid species
    information.
    """

    def __init__(self, sql_args: dict = None):
        logging.info(f"Alex123API: Initializing ALEX123 API...")
        super().__init__()
        self.database_connector: Alex123DBConnector = Alex123DBConnector()

        if sql_args:
            self.database_connector = Alex123DBConnectorSQL(sql_args)
        else:
            hdf_path = str(files('lipidlibrarian')) + '/data/alex123/alex123_db.h5'
            self.database_connector = Alex123DBConnectorHDF(hdf_path)

        logging.info(f"Alex123API: Initializing ALEX123 API done.")

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        results = []
        if lipid.nomenclature.level >= Level.molecular_lipid_species:
            results = self.query_name(
                lipid.nomenclature.get_name(
                    level=Level.molecular_lipid_species,
                    nomenclature_flavor='alex123'
                ),
                Level.molecular_lipid_species
            )
        elif lipid.nomenclature.level >= Level.sum_lipid_species:
            results = self.query_name(
                lipid.nomenclature.get_name(
                    level=Level.sum_lipid_species,
                    nomenclature_flavor='alex123'
                ),
                Level.sum_lipid_species
            )
        logging.debug(f"Alex123API: Found {len(results)} lipids.")
        return results

    def query_mz(self, mz: float, tolerance: float, adducts: list[Adduct], cutoff: int = 0) -> list[Lipid]:
        lipids = []

        results = self.database_connector.get_molecular_lipid_species_by_mz(mz, tolerance, adducts)

        if cutoff > 0:
            results = results.sample(min(cutoff, len(results.index)), replace=False)

        results_fragments = self.database_connector.get_fragment_by_molecular_lipid_species(
            results.molecular_lipid_species_id
        )

        for _, result in results.iterrows():
            lipid = Lipid()
            name = result.molecular_lipid_species_name
            lipid.nomenclature.name = name.replace('-', '_')
            source = Source(
                lipid.nomenclature.get_name(nomenclature_flavor='alex123'),
                lipid.nomenclature.level,
                'alex123'
            )

            lipid.nomenclature.add_synonym(Synonym.from_data(
                result.molecular_lipid_species_name,
                'result',
                source
            ))
            lipid.nomenclature.lipid_category = result.lipid_category_name
            lipid.nomenclature.lipid_class = result.lipid_class_name
            lipid.add_database_identifier(DatabaseIdentifier.from_data(
                'alex123',
                result.molecular_lipid_species_name,
                source
            ))
            lipid.add_mass(Mass.from_data(
                'neutral',
                float(result.sum_lipid_species_mass),
                source
            ))

            result_fragments = results_fragments[
                results_fragments.molecular_lipid_species_id == result.molecular_lipid_species_id
            ]
            for _, result_fragment in result_fragments.iterrows():
                adduct = copy.deepcopy(get_adduct(result_fragment.adduct_name))
                adduct.add_mass(Mass.from_data(
                    'exact',
                    round(float(result.sum_lipid_species_mass) + float(adduct.adduct_mass), 6),
                    source
                ))
                fragment = Fragment()
                fragment.name = result_fragment.fragment_name
                fragment.sum_formula = result_fragment.fragment_sum_formula
                fragment.add_mass(Mass.from_data(
                    'exact',
                    round(float(result_fragment.fragment_mass), 6),
                    source
                ))
                adduct.add_fragment(fragment)
                lipid.add_adduct(adduct)

            lipids.append(lipid)

        logging.debug(f"Alex123API: Found {len(results)} lipids.")
        return lipids

    def query_name(self, name: str, level: Level = Level.level_unknown, cutoff: int = 0) -> list[Lipid]:
        lipids = []

        if level == Level.structural_lipid_species:
            results = self.database_connector.get_sum_lipid_species_by_name({name})

            for _, result in results.iterrows():
                lipid = Lipid()
                lipid.nomenclature.name = result.sum_lipid_species_name
                source = Source(
                    lipid.nomenclature.get_name(nomenclature_flavor='alex123'),
                    lipid.nomenclature.level,
                    'alex123'
                )

                lipid.nomenclature.add_synonym(Synonym.from_data(
                    result.sum_lipid_species_name,
                    'result',
                    source
                ))
                lipid.nomenclature.lipid_category = result.lipid_category_name
                lipid.nomenclature.lipid_class = result.lipid_class_name
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'alex123',
                    result.sum_lipid_species_name,
                    source
                ))
                lipid.add_mass(Mass.from_data(
                    'neutral',
                    float(result.sum_lipid_species_mass),
                    source
                ))
                lipids.append(lipid)

        elif level == Level.molecular_lipid_species:
            results = self.database_connector.get_molecular_lipid_species_by_name({name})

            for _, result in results.iterrows():
                lipid = Lipid()
                lipid.nomenclature.name = result.molecular_lipid_species_name.replace('-', '_')
                source = Source(
                    lipid.nomenclature.get_name(nomenclature_flavor='alex123'),
                    lipid.nomenclature.level,
                    'alex123'
                )

                lipid.nomenclature.add_synonym(Synonym.from_data(
                    result.molecular_lipid_species_name,
                    'result',
                    source
                ))
                lipid.nomenclature.lipid_category = result.lipid_category_name
                lipid.nomenclature.lipid_class = result.lipid_class_name
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'alex123',
                    result.molecular_lipid_species_name,
                    source
                ))
                lipid.add_mass(Mass.from_data(
                    'neutral',
                    float(result.sum_lipid_species_mass),
                    source
                ))

                results_fragments = self.database_connector.get_fragment_by_molecular_lipid_species(
                    set(result.molecular_lipid_species_id)
                    if isinstance(result.molecular_lipid_species_id, Iterable)
                    else {result.molecular_lipid_species_id}
                )
                for _, result_fragment in results_fragments.iterrows():
                    adduct = copy.deepcopy(get_adduct(result_fragment.adduct_name))
                    adduct.add_mass(Mass.from_data(
                        'mass',
                        round(float(result.sum_lipid_species_mass) + float(adduct.adduct_mass), 6),
                        source
                    ))
                    fragment = Fragment()
                    fragment.name = result_fragment.fragment_name
                    fragment.sum_formula = result_fragment.fragment_sum_formula
                    fragment.add_mass(Mass.from_data(
                        'mass',
                        round(float(result_fragment.fragment_mass), 6),
                        source
                    ))
                    adduct.add_fragment(fragment)
                    lipid.add_adduct(adduct)

                lipids.append(lipid)

        return lipids
