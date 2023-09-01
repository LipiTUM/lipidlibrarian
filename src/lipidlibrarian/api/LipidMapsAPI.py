import copy
import json
import logging
from io import StringIO
from typing import Any

import pandas as pd
from requests import Response

from .LipidAPI import LipidAPI
from ..lipid import get_adduct
from ..lipid.Adduct import Adduct
from ..lipid.DatabaseIdentifier import DatabaseIdentifier
from ..lipid.Lipid import Lipid
from ..lipid.Mass import Mass
from ..lipid.Nomenclature import Level
from ..lipid.Synonym import Synonym
from ..lipid.StructureIdentifier import StructureIdentifier
from ..lipid.Source import Source


class LipidMapsAPI(LipidAPI):

    def __init__(self):
        logging.info(f"LipidMapsAPI: Initializing LipidMaps API...")
        super().__init__()
        logging.info(f"LipidMapsAPI: Initializing LipidMaps API done.")

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        results = []
        for lipidmaps_identifier in lipid.get_database_identifiers('lipidmaps'):
            results.extend(self.query_id(lipidmaps_identifier.identifier))
        results.extend(self.query_name(
            lipid.nomenclature.get_name(nomenclature_flavor='lipidmaps'),
            lipid.nomenclature.level
        ))
        logging.debug(f"LipidMapsAPI: Found {len(results)} lipid(s).")
        return results

    def query_mz(self, mz: float, tolerance: float, adducts: list[Adduct], cutoff: int = 0) -> list[Lipid]:
        logging.debug(f"LipidMapsAPI: Querying mz '{mz}' with tolerance '{tolerance}'.")
        if mz <= 0:
            return []
        if tolerance < 0:
            return []

        results = self._query_moverz_rest_api(mz, tolerance, adducts, cutoff)

        logging.debug(f"LipidMapsAPI: Found {len(results)} lipid(s).")
        return results

    def query_id(self, identifier: str) -> list[Lipid]:
        logging.debug(f"LipidMapsAPI: Querying ID '{identifier}'.")
        if identifier is None or identifier == '' or not isinstance(identifier, str):
            return []

        results = []
        results.extend(self._query_compound_rest_api(identifier, 'lm_id'))
        results.extend(self._query_lmsd_record_api(identifier))

        logging.debug(f"LipidMapsAPI: Found {len(results)} lipid(s).")
        return results

    def query_name(self, name: str, level: Level = None) -> list[Lipid]:
        logging.debug(f"LipidMapsAPI: Querying lipid name '{name}'.")
        if name is None or name == '' or not isinstance(name, str):
            return []

        results: list[Lipid] = []
        if level == Level.level_unknown or level == Level.structural_lipid_species:
            results.extend(self._query_compound_rest_api(name, 'abbrev_chains'))
        if level == Level.level_unknown or level == Level.isomeric_lipid_species:
            results.extend(self._query_lmsd_search_api([('Name', name)]))

        return results

    def _query_lmsd_search_api(self, input_items: list[tuple[str, str]]) -> list[Lipid]:
        query_parameters = []
        for input_item in input_items:
            query_parameters.append(f"{input_item[0]}={input_item[1]}")

        query_url = (
            f"http://www.lipidmaps.org/data/structure/LMSDSearch.php?"
            f"Mode=ProcessStrSearch&OutputMode=File&OutputType=CSV&OutputColumnHeader=Yes&"
            f"{'&'.join(query_parameters)}"
        )

        response = self.execute_http_query(query_url)
        if response.status_code != 200:
            return []

        try:
            if '</style>' in response.text:
                query_result_raw = StringIO(response.text.split('</style>\n\n')[1])
            else:
                query_result_raw = StringIO(response.text)
            query_results: list[dict[str, str]] = list(pd.read_csv(query_result_raw).to_dict(orient='index').values())
        except ValueError as _:
            return []

        results: list[Lipid] = []
        for query_result in query_results:
            results.extend(self._query_compound_rest_api(query_result['LM_ID'], 'lm_id'))

        return results

    def _query_lmsd_record_api(self, lipidmaps_identifier: str) -> list[Lipid]:
        url = f"https://www.lipidmaps.org/databases/lmsd/{lipidmaps_identifier}?format=csv"
        response = self.execute_http_query(url)
        if response.status_code != 200:
            return []
        try:
            result: dict[str, str] = pd.read_csv(StringIO(response.text)).to_dict(orient='index')[0]
        except ValueError as _:
            return []
        return self._convert_lmsd_record_lipid(result)

    @staticmethod
    def _convert_lmsd_record_lipid(data: dict[str, str]) -> list[Lipid]:
        lipid_name = data.get('COMMON_NAME')

        lipid = Lipid()
        lipid.nomenclature.name = lipid_name
        source = Source(lipid_name, lipid.nomenclature.level, 'lipidmaps')

        if (common_name := data.get('COMMON_NAME')) is not None:
            lipid.nomenclature.add_synonym(Synonym.from_data(
                common_name,
                'common_name',
                source
            ))
        if (systematic_name := data.get('SYSTEMATIC_NAME')) is not None:
            lipid.nomenclature.add_synonym(Synonym.from_data(
                systematic_name,
                'systematic_name',
                source
            ))
        for synonym in data.get('SYNONYMS').split('; '):
            lipid.nomenclature.add_synonym(Synonym.from_data(
                synonym,
                'synonym',
                source
            ))

        if (lipid_category := data.get('CATEGORY')) is not None:
            lipid_category = lipid_category.split(' ')[0]
            lipid.nomenclature.lipid_category = lipid_category
        if (lipid_class := data.get('MAIN_CLASS')) is not None:
            lipid_class = lipid_class.split(' ')[0]
            lipid.nomenclature.lipid_class = lipid_class
        if (sum_formula := data.get('FORMULA')) is not None:
            lipid.nomenclature.sum_formula = sum_formula

        try:
            if (monoisotopic_mass := data.get('MASS')) is not None:
                lipid.add_mass(Mass.from_data(
                    'monoisotopic',
                    float(monoisotopic_mass),
                    source
                ))
        except ValueError as _:
            pass

        if (lipidmaps_id := data.get('LM_ID')) is not None and lipidmaps_id != '-':
            lipid.add_database_identifier(DatabaseIdentifier.from_data(
                'lipidmaps',
                lipidmaps_id,
                source
            ))
        if (swisslipids_id := data.get('SWISSLIPIDS_ID')) is not None and swisslipids_id != '-':
            lipid.add_database_identifier(DatabaseIdentifier.from_data(
                'swisslipids',
                swisslipids_id,
                source
            ))
        if (hmdb_id := data.get('HMDBID')) is not None and hmdb_id != '-':
            lipid.add_database_identifier(DatabaseIdentifier.from_data(
                'hmdb',
                hmdb_id,
                source
            ))
        if (chebi_id := data.get('CHEBI_ID')) is not None and chebi_id != '-':
            lipid.add_database_identifier(DatabaseIdentifier.from_data(
                'chebi',
                chebi_id,
                source
            ))
        if (pubchem_id := data.get('PUBCHEM_COMPOUND_ID')) is not None and pubchem_id != '-':
            lipid.add_database_identifier(DatabaseIdentifier.from_data(
                'pubchem',
                pubchem_id,
                source
            ))

        return [lipid]

    def _query_compound_rest_api(self, search_term: str, input_item: str) -> list[Lipid]:
        if input_item not in ['lm_id', 'formula', 'inchi_key', 'pubchem_cid', 'hmdb_id', 'kegg_id', 'chebi_id',
                              'smiles', 'abbrev', 'abbrev_chains']:
            raise ValueError((
                f"Input item {input_item} is not known. Please use 'lm_id', 'formula', 'inchi_key', "
                f"'pubchem_cid', 'hmdb_id', 'kegg_id', 'chebi_id', 'smiles', 'abbrev' or 'abbrev_chains' "
                f"as you are using the context 'compound'"
            ))

        url = f"https://www.lipidmaps.org/rest/compound/{input_item}/{search_term}/all/json"
        response = self.execute_http_query(url)
        if response.status_code != 200:
            return []

        # convert the http response to a python dictionary
        if response.text == '[]':
            return []
        try:
            result = json.loads(response.text)
        except json.decoder.JSONDecodeError as _:
            return []
        if result.get('Row1') is not None:
            result = list(result.values())
        else:
            result = [result]
        return self._convert_compound_rest_api_lipids(result)

    @staticmethod
    def _convert_compound_rest_api_lipids(data: list[dict[str, Any]]) -> list[Lipid]:
        results: list[Lipid] = []
        for lipid_data in data:
            lipid = Lipid()

            if (lipid_name := lipid_data.get('name')) is not None:
                lipid.nomenclature.name = lipid_name
                source = Source(lipid_name, lipid.nomenclature.level, 'lipidmaps')
                lipid.nomenclature.add_synonym(Synonym.from_data(
                    lipid_name,
                    'name',
                    source
                ))
            if (lipid_name := lipid_data.get('sys_name')) is not None:
                if lipid.nomenclature.level is Level.level_unknown:
                    lipid.nomenclature.name = lipid_name
                    source = Source(lipid_name, lipid.nomenclature.level, 'lipidmaps')
                lipid.nomenclature.add_synonym(Synonym.from_data(
                    lipid_name,
                    'sys_name',
                    source
                ))
            if (lipid_name := lipid_data.get('abbrev_chains')) is not None:
                if lipid.nomenclature.level is Level.level_unknown:
                    lipid.nomenclature.name = lipid_name
                    source = Source(lipid_name, lipid.nomenclature.level, 'lipidmaps')
                lipid.nomenclature.add_synonym(Synonym.from_data(
                    lipid_name,
                    'abbrev_chains',
                    source
                ))
            if (lipid_name := lipid_data.get('abbrev')) is not None:
                if lipid.nomenclature.level is Level.level_unknown:
                    lipid.nomenclature.name = lipid_name
                    source = Source(lipid_name, lipid.nomenclature.level, 'lipidmaps')
                lipid.nomenclature.add_synonym(Synonym.from_data(
                    lipid_name,
                    'abbrev',
                    source
                ))

            if (lipid_category := lipid_data.get('core')) is not None:
                lipid_category = lipid_category.split(' ')[0]
                lipid.nomenclature.lipid_category = lipid_category
            if (lipid_class := lipid_data.get('main_class')) is not None:
                lipid_class = lipid_class.split(' ')[0]
                lipid.nomenclature.lipid_class = lipid_class
            if (sum_formula := lipid_data.get('formula')) is not None:
                lipid.nomenclature.sum_formula = sum_formula

            if (synonyms := lipid_data.get('synonyms')) is not None:
                synonyms = synonyms.split('; ')
                for synonym in synonyms:
                    lipid.nomenclature.add_synonym(Synonym.from_data(
                        synonym,
                        'synonym',
                        source
                    ))

            if (mass := lipid_data.get('exactmass')) is not None:
                lipid.add_mass(Mass.from_data(
                    'monoisotopic',
                    float(mass),
                    source
                ))

            if (lipidmaps_identifier := lipid_data.get('lm_id')) is not None:
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'lipidmaps',
                    lipidmaps_identifier,
                    source
                ))
            if (hmdb_identifier := lipid_data.get('hmdb_id')) is not None:
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'hmdb',
                    hmdb_identifier,
                    source
                ))
            if (chebi_identifier := lipid_data.get('chebi_id')) is not None:
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'chebi',
                    chebi_identifier,
                    source
                ))
            if (pubchem_identifier := lipid_data.get('pubchem_cid')) is not None:
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'pubchem',
                    pubchem_identifier,
                    source
                ))
            if (kegg_identifier := lipid_data.get('kegg_id')) is not None:
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'kegg',
                    kegg_identifier,
                    source
                ))

            if (smiles := lipid_data.get('smiles')) is not None:
                lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                    smiles,
                    'smiles',
                    source
                ))
            if (inchi := lipid_data.get('inchi')) is not None:
                lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                    inchi,
                    'inchi',
                    source
                ))
            if (inchikey := lipid_data.get('inchi_key')) is not None:
                lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                    inchikey,
                    'inchikey',
                    source
                ))

            results.append(lipid)
        return results

    def _query_moverz_rest_api(self, mz: float, tolerance: float, adducts: list[Adduct],
                               cutoff: int = 0) -> list[Lipid]:
        base_url = 'https://www.lipidmaps.org/rest/moverz/LIPIDS'

        query_result = pd.DataFrame()
        for adduct in adducts:
            if (adduct_name := adduct.lipidmaps_name) is not None:
                query_url = f"{base_url}/{mz}/{adduct_name}/{tolerance}/txt"
                response = self.execute_http_query(query_url)
                if response.status_code != 200 or response.text.startswith('Internal error:'):
                    continue
                query_result = pd.concat([
                    query_result,
                    self._parse_moverz_rest_api_result(response)
                ], ignore_index=True)

        if cutoff > 0:
            query_result = query_result.sample(min(cutoff, len(query_result.index)), replace=False)

        return self._convert_moverz_rest_api_lipids(query_result)

    @staticmethod
    def _parse_moverz_rest_api_result(response: Response) -> pd.DataFrame:
        first = True
        header = []
        content = []
        for line in response.text.split("\n"):
            if line == "" or line.__contains__("pre>"):
                continue
            temp = []
            linesplit = line.strip().split("\t")
            for elem in linesplit:
                if first:
                    header.append(elem.strip())
                else:
                    temp.append(elem.strip())

            if temp:
                content.append(temp)
            first = False
        if not content:
            return pd.DataFrame()
        response_df = pd.DataFrame(content, columns=header)
        if len(response_df.index) > 0:
            response_df[['Class', 'Bond info']] = response_df.Name.str.split(" ", n=1, expand=True)
        return response_df

    @staticmethod
    def _convert_moverz_rest_api_lipids(data: pd.DataFrame) -> list[Lipid]:
        results: list[Lipid] = []
        for entry in data.iterrows():
            lipid = Lipid()

            if entry[1].get('Name') == 'UNDEFINED':
                continue

            lipid.nomenclature.name = entry[1].get('Name')
            source = Source(
                lipid.nomenclature.get_name(nomenclature_flavor='lipidmaps'),
                lipid.nomenclature.level,
                'lipidmaps'
            )

            lipid.nomenclature.sum_formula = entry[1].get('Formula')

            adduct_name = entry[1].get('Ion')
            if adduct_name.lower() == 'neutral':
                lipid.add_mass(Mass.from_data(
                    'monoisotopic',
                    float(entry[1].get('Matched m/z')),
                    source
                ))
            else:
                adduct_name = adduct_name[adduct_name.find('[') + 1:adduct_name.find(']')]
                adduct = copy.deepcopy(get_adduct(adduct_name))
                if adduct is not None:
                    adduct.add_mass(Mass.from_data(
                        'mass',
                        float(entry[1].get('Matched m/z')),
                        source
                    ))
                    lipid.add_adduct(adduct)

            results.append(lipid)
        return results
