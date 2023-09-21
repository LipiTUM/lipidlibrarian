import logging
import os
from importlib.resources import files
from typing import Any

import numpy as np
import pandas as pd
from func_timeout import FunctionTimedOut
from func_timeout import func_timeout

from .Adduct import Adduct


adducts = None
lynx_converter = None
goslin_converter = None
lipid_name_conversion_methods = {'lipidlynxx', 'goslin'}
TIMEOUT_SECONDS = 30


def parse_adducts():
    logging.info("Lipid: Parsing adducts...")
    adducts = []
    adduct_df = pd.read_csv(str(files('lipidlibrarian.data').joinpath('adducts.csv')))
    adduct_array = np.array(
        list(zip(
            adduct_df.adduct_name,
            adduct_df.adduct_mass,
            adduct_df.adduct_charge,
            adduct_df.adduct_swisslipids_name,
            adduct_df.adduct_swisslipids_abbrev,
            adduct_df.adduct_lipidmaps_name
        )), dtype=[
            ('adduct_name', 'U16'),
            ('adduct_mass', 'f16'),
            ('adduct_charge', 'i1'),
            ('adduct_swisslipids_name', 'U16'),
            ('adduct_swisslipids_abbrev', 'U16'),
            ('adduct_lipidmaps_name', 'U16')
        ]
    )
    adduct_df = pd.DataFrame(adduct_array)

    for adduct_row in adduct_df.itertuples():
        adduct = Adduct()
        adduct.name = adduct_row.adduct_name
        adduct.adduct_mass = float(adduct_row.adduct_mass)
        adduct.charge = adduct_row.adduct_charge
        if not str(swisslipids_name := adduct_row.adduct_swisslipids_name) == 'nan':
            adduct.swisslipids_name = swisslipids_name
        if not str(swisslipids_abbrev := adduct_row.adduct_swisslipids_abbrev) == 'nan':
            adduct.swisslipids_abbrev = swisslipids_abbrev
        if not str(lipidmaps_name := adduct_row.adduct_lipidmaps_name) == 'nan':
            adduct.lipidmaps_name = lipidmaps_name
        adducts.append(adduct)
    logging.info("Lipid: Parsing adducts done.")
    return adducts


def get_adduct(adduct_name: str) -> Adduct:
    global adducts

    if adducts is None:
        adducts = parse_adducts()

    for adduct in adducts:
        if adduct_name.lower() == adduct.name.lower():
            return adduct
        if adduct.swisslipids_name is not None and adduct_name.lower() == adduct.swisslipids_name.lower():
            return adduct
        if adduct.swisslipids_abbrev is not None and adduct_name.lower() == adduct.swisslipids_abbrev.lower():
            return adduct
        if adduct.lipidmaps_name is not None and adduct_name.lower() == adduct.lipidmaps_name.lower():
            return adduct


def get_adducts(adduct_names: set[str]) -> list[Adduct]:
    global adducts

    if adducts is None:
        adducts = parse_adducts()

    results = []
    for adduct_name in adduct_names:
        results.append(get_adduct(adduct_name))
    return results


def get_all_adducts() -> list[Adduct]:
    global adducts

    if adducts is None:
        adducts = parse_adducts()

    return adducts


def lynx_init() -> Any | None:
    logging.info("LipidLynxX: Initializing LipidLynxX...")
    current_working_directory = os.getcwd()
    if 'lipidlynxx' in lipid_name_conversion_methods:
        try:
            from lynx import Converter  # changes the working directory
            from lynx.utils.log import create_log
            logger = create_log(log_level="ERROR")
            converter = Converter(logger=logger)  # changes the working directory
            logging.info("LipidLynxX: Initializing LipidLynxX done.")
        except ModuleNotFoundError as _:
            converter = None
            lipid_name_conversion_methods.remove('lipidlynxx')
            logging.error("LipidLynxX: Initializing LipidLynxX failed. Disabling LipidLynxX support.")
    else:
        return None
    os.chdir(current_working_directory)
    return converter


def lynx_convert(lipid_name: str, level: str = 'MAX') -> str | None:
    global lynx_converter

    if 'lipidlynxx' not in lipid_name_conversion_methods:
        return None

    if 'lipidlynxx' in lipid_name_conversion_methods and lynx_converter is None:
        lynx_converter = lynx_init()

    if lynx_converter is None:
        return None
    
    if lipid_name is None:
        return None

    current_working_directory = os.getcwd()
    # changes the working directory
    try:
        result = func_timeout(TIMEOUT_SECONDS, lynx_converter.convert, args=(lipid_name, level,))
        result = result.output
    except FunctionTimedOut:
        error = ("LipidLynxX for name " + lipid_name + " and level " + level + " timed out after " +
                 str(TIMEOUT_SECONDS) + " seconds.")
        logging.error(error)
        result = None
    finally:
        os.chdir(current_working_directory)

    if result == "":
        result = None

    logging.info(f"LipidLynxX: Converted '{lipid_name}' with level '{level}' to '{result}'")
    return result


def goslin_init() -> Any | None:
    logging.info("Goslin: Initializing Goslin...")
    if 'goslin' in lipid_name_conversion_methods:
        try:
            from pygoslin.parser.Parser import LipidParser
            converter = LipidParser()
        except ModuleNotFoundError as _:
            converter = None
            lipid_name_conversion_methods.remove('goslin')
    else:
        return None
    logging.info("Goslin: Initializing Goslin done.")
    return converter


def goslin_convert(lipid_name: str, level: Any = None) -> str | None:
    global goslin_converter

    if 'goslin' not in lipid_name_conversion_methods:
        return None

    if 'goslin' in lipid_name_conversion_methods and goslin_converter is None:
        goslin_converter = goslin_init()

    if goslin_converter is None:
        return None

    from pygoslin.domain.LipidExceptions import LipidException
    from pygoslin.domain.LipidExceptions import LipidParsingException
    from pygoslin.domain.LipidLevel import LipidLevel

    if lipid_name is None:
        return None

    try:
        result = func_timeout(TIMEOUT_SECONDS, goslin_converter.parse, args=(lipid_name,))
        if level is not None and level is not LipidLevel.UNDEFINED:
            result = result.get_lipid_string(level=level)
        else:
            result = result.get_lipid_string()
    except FunctionTimedOut:
        error = ("Goslin: Conversion for name " + lipid_name + " timed out after " + str(TIMEOUT_SECONDS) + " seconds.")
        logging.error(error)
        result = None
    except Exception or LipidException or LipidParsingException as _:
        # Conversions with level raise generic Exceptions in Goslin currently.
        result = None

    if result == "":
        result = None

    if level is not LipidLevel.UNDEFINED:
        logging.info(f"Goslin: Converted '{lipid_name}' with level '{level}' to '{result}'")
    else:
        logging.info(f"Goslin: Converted '{lipid_name}' to '{result}'")
    return result
