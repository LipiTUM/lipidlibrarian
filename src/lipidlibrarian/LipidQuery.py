import copy
import logging

from .api.LipidAPI import LipidAPI
from .lipid.Adduct import Adduct
from .lipid.Lipid import DatabaseIdentifier
from .lipid.Lipid import Lipid
from .lipid.Nomenclature import Level
from .lipid.Source import Source
from .api import init_APIs
from .api import supported_APIs
from .lipid import get_adducts
from .lipid import get_all_adducts


class LipidQuery:

    def __init__(self, input_string: str, requeries: int = 0, selected_APIs: set[str] = supported_APIs,
                 method: str = "all", cutoff: int = 0, sql_args: dict = None):
        self.input_string: str = input_string
        self.lipids: list[Lipid] = []
        self.query_parameters: Lipid | tuple[float, float, list[Adduct]] | None = None
        self.sql_args: dict | None = sql_args
        self.selected_APIs: set[str] = set()
        self.APIs: dict[str, LipidAPI] = {}
        self.requeries: int | None = None
        self.cutoff: int | None = None

        for selected_API in selected_APIs:
            if selected_API not in supported_APIs:
                logging.warning((f"LipidQuery: API {str(selected_API)} was not found in list "
                                 f"of all available apis: {supported_APIs}."))
        self.selected_APIs = selected_APIs

        self.requeries = int(requeries)
        if cutoff < 0:
            raise ValueError((f"The requeries = {requeries} parameter does not contain a number that represents a "
                              f"valid requery amount. Please choose a positive integer or 0."))

        self.cutoff = int(cutoff)
        if cutoff < 0:
            raise ValueError((f"The cutoff = {cutoff} parameter does not contain a number that represents a "
                              f"valid cutoff. Please choose a positive integer."))

        query_input = input_string.strip()

        if method == "id":
            self.query_parameters = self._detect_identifier_query(query_input)
            if self.query_parameters is None:
                logging.warning(("LipidQuery: The method specified was id, but the input was not recognized "
                                "as a valid database identifier query."))
        elif method == "mz":
            self.query_parameters = self._detect_mz_query(query_input)
            if self.query_parameters is None:
                logging.warning(("LipidQuery: The method specified was mz, but the input "
                                 "was not recognized as a valid mz query."))
        elif method == "name":
            self.query_parameters = self._detect_name_query(query_input)
            if self.query_parameters is None:
                logging.warning(("LipidQuery: The method specified was name, but the input could not "
                                 "be recognized as a valid name query."))
        else:
            # assume the input is a database identifier
            self.query_parameters = self._detect_identifier_query(query_input)
            if self.query_parameters is None:
                # in case the input is not parseable as database identifier, assume it's an m/z tuple
                self.query_parameters = self._detect_mz_query(query_input)
                if self.query_parameters is None:
                    # in case the input is not parseable as an m/z tuple, assume it's a lipid name
                    self.query_parameters = self._detect_name_query(query_input)
                    if self.query_parameters is None:
                        # in case the input is not parseable as a lipid name, exit
                        logging.warning("LipidQuery: The input could not be parsed.")
                    else:
                        logging.info("LipidQuery: Detected valid name query.")
                else:
                    logging.info("LipidQuery: Detected valid mz query.")
            else:
                logging.info("LipidQuery: Detected valid identifier query.")

    def query(self) -> list[Lipid]:
        if self.query_parameters is None:
            return []

        logging.info("Initializing APIs...")
        self.APIs = init_APIs(self.selected_APIs, self.sql_args)
        logging.info("Initializing APIs done.")

        logging.info(f"Querying {self.input_string}...")

        logging.info("Querying SwissLipids...")
        self.add_lipids(self.APIs['swisslipids'].query(self.query_parameters, cutoff=self.cutoff))
        logging.info("Querying LipidMaps...")
        self.add_lipids(self.APIs['lipidmaps'].query(self.query_parameters, cutoff=self.cutoff))
        logging.info("Querying ALEX123...")
        self.add_lipids(self.APIs['alex123'].query(self.query_parameters, cutoff=self.cutoff))

        for i in range(self.requeries):
            logging.info(f'Executing requery {i}.')
            current_lipids = copy.deepcopy(self.lipids)
            for lipid in current_lipids:
                logging.info("Requerying SwissLipids...")
                self.add_lipids(self.APIs['swisslipids'].query(lipid, cutoff=self.cutoff))
                logging.info("Requerying LipidMaps...")
                self.add_lipids(self.APIs['lipidmaps'].query(lipid, cutoff=self.cutoff))
                logging.info("Requerying ALEX123...")
                self.add_lipids(self.APIs['alex123'].query(lipid, cutoff=self.cutoff))

        # final lipid merge
        self.merge_lipids()

        for lipid in self.lipids:
            logging.info("Querying LINEX...")
            self.add_lipids(self.APIs['linex'].query(lipid, cutoff=self.cutoff))
            logging.info("Querying LION...")
            self.add_lipids(self.APIs['lion'].query(lipid, cutoff=self.cutoff))
            lipid._query = self.input_string

        logging.info(f"Querying {self.input_string} done.")
        return self.lipids

    @staticmethod
    def _detect_identifier_query(query_input: str) -> Lipid | None:
        if len(query_input.split(' ')) != 1:
            return None

        query_parameter = Lipid()
        source = Source('', Level.level_unknown, 'query_parameter')
        if query_input[0:2] == "LM" and 11 < len(query_input) < 15:
            query_parameter.add_database_identifier(DatabaseIdentifier.from_data(
                'lipidmaps',
                query_input,
                source
            ))
        elif query_input[0:4] == "SLM:":
            query_parameter.add_database_identifier(DatabaseIdentifier.from_data(
                'swisslipids',
                query_input,
                source
            ))
        elif query_input[0:6] == "CHEBI:":
            query_parameter.add_database_identifier(DatabaseIdentifier.from_data(
                'chebi',
                query_input,
                source
            ))
        else:
            return None
        return query_parameter

    @staticmethod
    def _detect_mz_query(query_input: str) -> tuple[float, float, list[Adduct]] | None:
        try:
            query_mz, query_tolerance, query_adducts, *_ = query_input.split(';') + [""] * 4

            mz: float = float(query_mz)
            tolerance: float = float(query_tolerance)
            adducts: list[Adduct] = []

            if query_adducts != "":
                query_adducts = query_adducts.lower()
                if query_adducts in {'positive', 'pos', '+', 'p', 'plus', '1'}:
                    adducts = [adduct for adduct in get_all_adducts() if adduct.charge > 0]
                elif query_adducts in {'negative', 'neg', '-', 'n', 'minus', '-1'}:
                    adducts = [adduct for adduct in get_all_adducts() if adduct.charge < 0]
                else:
                    adducts = get_adducts(set([x.strip() for x in query_adducts.split(',')]))
            else:
                adducts = get_all_adducts()
        except (ValueError, AttributeError):
            return None
        return mz, tolerance, adducts

    @staticmethod
    def _detect_name_query(query_input: str) -> Lipid | None:
        query_parameter = Lipid()
        query_parameter.nomenclature.name = query_input

        if query_parameter.nomenclature.level == Level.level_unknown:
            return None
        return query_parameter

    def add_lipid(self, lipid: Lipid) -> None:
        for existing_lipid in self.lipids:
            existing_lipid: Lipid
            if existing_lipid.merge(lipid):
                return
        self.lipids.append(lipid)

    def add_lipids(self, lipids: list[Lipid]) -> None:
        for lipid in lipids:
            self.add_lipid(lipid)

    def merge_lipids(self) -> None:
        temp_lipids = self.lipids
        self.lipids = []
        for lipid in temp_lipids:
            self.add_lipid(lipid)

    def __repr__(self):
        return f"Lipid Query for '{self.input_string}' with {len(self.lipids)} results."
