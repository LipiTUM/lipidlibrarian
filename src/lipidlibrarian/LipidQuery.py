import copy
import logging

from lipidlibrarian.lipid.Synonym import Synonym

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

    def __init__(self, input_string: str, requeries: int = 0, selected_APIs: set[str] = None,
                 method: str = "all", cutoff: int = 0, sql_args: dict = None):
        self.input_string: str = input_string
        self.lipids: list[Lipid] = []
        self.query_parameters: Lipid | tuple[float, float, list[Adduct]] | None = None
        self.sql_args: dict | None = sql_args
        self.selected_APIs: set[str] = set()
        self.APIs: dict[str, LipidAPI] = {}
        self.requeries: int | None = None
        self.cutoff: int | None = None

        if selected_APIs is None:
            self.selected_APIs = set()
            self.selected_APIs.update(supported_APIs)
            self.selected_APIs.add('lipidlibrarian')
        else:
            self.selected_APIs = selected_APIs
            for selected_API in selected_APIs:
                if selected_API not in supported_APIs:
                    logging.warning((f"LipidQuery: API {str(selected_API)} was not found in list "
                                     f"of all available apis: {supported_APIs}. Removing it..."))
                    self.selected_APIs.remove(selected_API)

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
        
        if isinstance(self.query_parameters, Lipid) and self.query_parameters.nomenclature.name != "":
            self.add_lipid(self.query_parameters)

        logging.info("Initializing APIs...")
        self.APIs = init_APIs(self.selected_APIs, self.sql_args)
        logging.info("Initializing APIs done.")

        logging.info(f"Querying {self.input_string}...")

        if 'swisslipids' in self.selected_APIs:
            logging.info("Querying SwissLipids...")
            self.add_lipids(self.APIs['swisslipids'].query(self.query_parameters, cutoff=self.cutoff))
        if 'lipidmaps' in self.selected_APIs:
            logging.info("Querying LipidMaps...")
            self.add_lipids(self.APIs['lipidmaps'].query(self.query_parameters, cutoff=self.cutoff))
        if 'alex123' in self.selected_APIs:
            logging.info("Querying ALEX123...")
            self.add_lipids(self.APIs['alex123'].query(self.query_parameters, cutoff=self.cutoff))

        for i in range(self.requeries):
            logging.info(f'Executing requery {i}.')
            current_lipids = copy.deepcopy(self.lipids)
            for lipid in current_lipids:
                if 'swisslipids' in self.selected_APIs:
                    logging.info("Requerying SwissLipids...")
                    self.add_lipids(self.APIs['swisslipids'].query(lipid, cutoff=self.cutoff))
                if 'lipidmaps' in self.selected_APIs:
                    logging.info("Requerying LipidMaps...")
                    self.add_lipids(self.APIs['lipidmaps'].query(lipid, cutoff=self.cutoff))
                if 'alex123' in self.selected_APIs:
                    logging.info("Requerying ALEX123...")
                    self.add_lipids(self.APIs['alex123'].query(lipid, cutoff=self.cutoff))

        # final lipid merge
        logging.info("Pre-merge lipid summary: " +
                     ", ".join([f"'{l.nomenclature.get_name()}' lvl={l.nomenclature.level} ids={len(l.database_identifiers)}"
                                for l in self.lipids[:10]]))
        self.merge_lipids()
        logging.info("Post-merge lipid summary: " +
                     ", ".join([f"'{l.nomenclature.get_name()}' lvl={l.nomenclature.level} ids={len(l.database_identifiers)}"
                                for l in self.lipids[:10]]))

        for lipid in self.lipids:
            if 'lipidlibrarian' in self.selected_APIs:
                pass
                #logging.info("Querying LipidLibrarian...")
                #self.add_lipids(self.APIs['lipidlibrarian'].query(lipid, cutoff=self.cutoff))
            if 'linex' in self.selected_APIs:
                logging.info("Querying LINEX...")
                self.add_lipids(self.APIs['linex'].query(lipid, cutoff=self.cutoff))
            if 'lion' in self.selected_APIs:
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
        source = Source('', Level.level_unknown, 'lipidlibrarian')
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

        query_parameter.nomenclature.add_synonym(
            Synonym.from_data(
                query_input,
                "query_input",
                Source(
                    query_input,
                    query_parameter.nomenclature.level,
                    'lipidlibrarian'
                )
            )
        )

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
        if not self.lipids:
            return

        # Determine the "query level" if this is a name/id query Lipid
        target_level: Level | None = None
        if isinstance(self.query_parameters, Lipid):
            target_level = self.query_parameters.nomenclature.level

        # If we can't infer a target level (e.g., mz query), do a safe dedupe merge only
        if target_level is None or target_level == Level.level_unknown:
            temp = self.lipids
            self.lipids = []
            for l in temp:
                self.add_lipid(l)
            return

        levels_present = sorted({l.nomenclature.level for l in self.lipids})

        # Choose what to keep based on wether we have lipids with the target level or not
        exact = [l for l in self.lipids if l.nomenclature.level == target_level]
        higher = [l for l in self.lipids if l.nomenclature.level > target_level]

        if exact:
            kept = exact
            dropped = [l for l in self.lipids if l.nomenclature.level != target_level]
            keep_desc = f"exact level {target_level}"
        elif higher:
            kept = higher
            dropped = [l for l in self.lipids if l.nomenclature.level <= target_level]
            keep_desc = f"all higher than {target_level}"
        else:
            kept = list(self.lipids)
            dropped = []
            keep_desc = "all (no exact/higher)"

        logging.info(
            f"merge_lipids: target_level={target_level}, levels_present={levels_present}, "
            f"keep={keep_desc}, kept={len(kept)}, dropped={len(dropped)}"
        )

        # Deduplicate/merge within kept
        new_list: list[Lipid] = []
        for l in kept:
            merged = False
            for k in new_list:
                if k.hierarchical_merge(l):
                    merged = True
                    break
            if not merged:
                new_list.append(l)

        # Merge dropped into kept when possible
        for l in dropped:
            for k in new_list:
                if k.hierarchical_merge(l):
                    break

        self.lipids = new_list


    def __repr__(self):
        return f"Lipid Query for '{self.input_string}' with {len(self.lipids)} results."
