import copy
import json
import logging
import random
import re
from contextlib import suppress

from .LipidAPI import LipidAPI
from ..lipid.Adduct import Adduct
from ..lipid.Lipid import DatabaseIdentifier
from ..lipid.Lipid import Lipid
from ..lipid.Lipid import Mass
from ..lipid.Nomenclature import Level
from ..lipid.Nomenclature import StructureIdentifier
from ..lipid.Nomenclature import Synonym
from ..lipid.Reaction import Reaction
from ..lipid.Source import Source
from ..lipid import get_adduct


class SwissLipidsAPI(LipidAPI):
    lipid_to_swisslipids_level_map: dict[Level, str] = {
        Level.level_unknown: 'Species',
        Level.sum_lipid_species: 'Species',
        Level.molecular_lipid_species: 'Molecular subspecies',
        Level.structural_lipid_species: 'Structural subspecies',
        Level.isomeric_lipid_species: 'Isomeric subspecies'
    }

    def __init__(self):
        logging.info(f"SwissLipidsAPI: Initializing SwissLipids API...")
        super().__init__()
        logging.info(f"SwissLipidsAPI: Initializing SwissLipids API done.")

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        results = []
        for swisslipids_identifier in lipid.get_database_identifiers('swisslipids'):
            results.extend(self.query_id(swisslipids_identifier.identifier))
        for lipidmaps_identifier in lipid.get_database_identifiers('lipidmaps'):
            results.extend(self.query_id(lipidmaps_identifier.identifier))
        results.extend(
            self.query_name(
                lipid.nomenclature.get_name(nomenclature_flavor='swisslipids'),
                lipid.nomenclature.level
            )
        )
        logging.debug(f"SwissLipidsAPI: Found {len(results)} lipid(s).")
        return results

    def query_mz(self, mz: float, tolerance: float, adducts: list[Adduct], cutoff: int = 0) -> list[Lipid]:
        logging.debug(f"SwissLipidsAPI: Querying mz '{mz}' with tolerance '{tolerance}'.")
        if mz <= 0:
            logging.error("SwissLipidsAPI: MZ value is smaller or equal to 0 which is not possible")
            return []
        if tolerance < 0:
            logging.error("SwissLipidsAPI: Tolerance is smaller than 0 which is not possible")
            return []
        
        adduct_names = set()
        for adduct in adducts:
            if (adduct_name := adduct.swisslipids_abbrev) is not None:
                adduct_names.add(adduct_name)

        results = []

        entries = self.get_entry(
            self._search_by_mz(
                mz,
                tolerance,
                output_level='Species',
                adducts=adduct_names,
                children=True,
                cutoff=cutoff
            )
        )
        results.extend(entries)

        logging.debug(f"SwissLipidsAPI: Found {len(results)} lipid(s).")
        return results

    def query_id(self, identifier: str) -> list[Lipid]:
        logging.debug(f"SwissLipidsAPI: Querying ID '{identifier}'.")
        results = []

        # If search id is not valid, do not query but return an empty list
        if identifier is None or identifier == "" or not isinstance(identifier, str):
            return []

        with suppress(json.decoder.JSONDecodeError):
            if identifier.startswith("SLM:"):
                entity_identifiers = [identifier]
            else:
                entity_identifiers = self._search_by_id(identifier)
            entries = self.get_entry(entity_identifiers)

            for entry in entries:
                results.append(entry)

        logging.debug(f"SwissLipidsAPI: Found {len(results)} lipid(s).")
        return results

    def query_name(self, name: str, level: Level = None) -> list[Lipid]:
        logging.debug(f"SwissLipidsAPI: Querying lipid name '{name}'.")
        results = []
        # If name or level is not valid, do not query but return an empty list
        if name is None or name == "" or not isinstance(name, str) or level not in self.lipid_to_swisslipids_level_map:
            return []

        # convert level to swisslipids level for the query
        swiss_lipids_level = self.lipid_to_swisslipids_level_map[level]

        with suppress(json.decoder.JSONDecodeError):
            entries = self.get_entry(self._search_by_name(name, swiss_lipids_level, children=False))
            for entry in entries:
                results.append(entry)
        return results

    def get_entry(self, identifiers: set[str]) -> list[Lipid]:
        """
        Given a list of entity_ids extract all information needed for lipid librarian

        :entity_ids: set of ids to query for

        :returns: dictionaries containing the data for the provided entity ids
        """
        results = []

        # for all identifiers get the entry
        for identifier in identifiers:
            if identifier == "-":
                continue
            # use swisslipids entity_id to get even more information for the specific entity
            response = self.execute_http_query(f"https://www.swisslipids.org/api/entity/{identifier}")
            if response.status_code != 200:
                continue

            # deserialize response to a python object
            try:
                lipid = self._convert_lipid(json.loads(response.text))
            except json.decoder.JSONDecodeError as _:
                continue

            results.append(lipid)

        return results

    def _search_by_name(self, name, output_level, children=False) -> set[str]:
        """
        Perform a query using lipid name

        :name: lipid name which can be either  Sum Species, Molecular Subspecies, Structural Subspecies or
        an Isomeric Subspecies
        :output_level: parameter specifying up to which classification level the entries are to be extracted
        :children: if true all entries for the provides output level and children levels are returned, if false only
        entries for the provided output level are returned

        :returns: swisslipids entity_ids
        """
        response = self.execute_http_query(f"https://www.swisslipids.org/api/search?term={name}")
        if response.status_code != 200:
            return set()

        # deserialize response to a python object
        try:
            response_data = json.loads(response.text)
        except json.decoder.JSONDecodeError as _:
            return set()

        hierarchy = ["Species", "Molecular subspecies",
                     "Structural subspecies", "Isomeric subspecies"]

        if children:
            hierarchy = hierarchy[hierarchy.index(output_level):]
        else:
            hierarchy = [output_level]

        # get ids for all results with a classification level equal to species
        identifiers: set[str] = set()
        for entry in response_data:
            if entry["classification_level"] in hierarchy:
                identifiers.add(entry["entity_id"])

        return identifiers

    def _search_by_id(self, identifier: str) -> set[str]:
        """
        Perform a querry using a database id

        :id: database id of the lipid

        :returns: swisslipids entity_ids
        """
        response = self.execute_http_query(f"https://www.swisslipids.org/api/search?term={identifier}")
        if response.status_code != 200:
            return set()

        # deserialize response to a python object
        try:
            response_data = json.loads(response.text)
        except json.decoder.JSONDecodeError as _:
            return set()

        # get the ids of all results
        identifiers: set[str] = set()
        for entry in response_data:
            identifiers.add(entry["entity_id"])

        return identifiers

    def _search_by_mz(self, mz: float, tolerance: float, output_level: str, adducts: set[str],
                      children: bool = False, cutoff: int = 0) -> set[str]:
        """
        Perform a query using mass to charge ratio adduct and a mass-error-rate (tolerance)

        :mz: m/z value of a metabolite adduct or its exact mass
        :mass_error_rate: the error tolerance of the m/z value
        :adduct: Possible values are:
            MassExact => exact mass
            MassM => [M.]+
            MassMH => [M+H]+
            MassMK => [M+K]+
            MassMNa => [M+Na]+
            MassMLi => [M+Li]+
            MassMNH4 => [M+NH4]+
            MassMmH => [M-H]-
            MassMCl => [M+Cl]-
            MassMOAc => [M+OAc]-
        :classification_level: parameter specifying up to which classification level the entries are to be extracted

        :returns: ids matching to the mass and tolerance and the provided classification level
        """
        identifiers: set[str] = set()

        for adduct in adducts:
            q_http = "https://www.swisslipids.org/api/"
            api_term = f"advancedSearch?mz={mz}&adduct={adduct}&massErrorRate={tolerance}"

            response = self.execute_http_query(q_http + api_term)
            if response.status_code != 200:
                continue

            # deserialize response to a python object
            try:
                resp_object = json.loads(response.text)
            except json.decoder.JSONDecodeError as _:
                continue

            hierarchy = ["Species", "Molecular subspecies",
                         "Structural subspecies", "Isomeric subspecies"]

            if children:
                hierarchy = hierarchy[hierarchy.index(output_level):]
            else:
                hierarchy = [output_level]

            # get identifiers for all results with the classification level equal to species
            for entry in resp_object:
                if entry["classification_level"] in hierarchy:
                    identifiers.add(entry["entity_id"])

        if cutoff > 0:
            identifiers = set(random.sample(identifiers, min(cutoff, len(identifiers))))

        return identifiers

    @staticmethod
    def _convert_lipid(entry: dict):
        lipid = Lipid()

        # parse name and level
        if (synonyms := entry.get('synonyms')) is not None:
            synonym: dict
            for synonym in synonyms:
                if synonym.get('type') == 'abbreviation' and synonym.get('source') == 'SwissLipids':
                    lipid.nomenclature.name = synonym.get('name')
                    break
        if lipid.nomenclature.level == Level.level_unknown:
            if (entity_name := entry.get('entity_name')) is not None:
                entity_name: str
                lipid.nomenclature.name = entity_name

        source = Source(
            lipid.nomenclature.get_name(nomenclature_flavor='swisslipids'),
            lipid.nomenclature.level,
            'swisslipids'
        )

        # Fill synonym information
        if (entity_name := entry.get('entity_name')) is not None:
            entity_name: str
            lipid.nomenclature.add_synonym(Synonym.from_data(
                entity_name,
                'entity_name',
                source
            ))
        if (synonyms := entry.get('synonyms')) is not None:
            synonyms: dict
            for synonym in synonyms:
                lipid.nomenclature.add_synonym(Synonym.from_data(
                    synonym.get('name'),
                    synonym.get('type'),
                    source
                ))

        if (chemical_data := entry.get('chemical_data')) is not None:
            chemical_data: dict
            if (sum_formula := chemical_data.get('formula')) is not None:
                lipid.nomenclature.sum_formula = sum_formula

        if (structures := entry.get('structures')) is not None:
            structures: dict
            if (smiles := structures.get('smiles')) is not None:
                lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                    smiles,
                    'smiles',
                    source
                ))
            if (inchi := structures.get('inchi')) is not None:
                if inchi != '' and inchi != 'InChI=none':
                    lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                        inchi,
                        'inchi',
                        source
                    ))
            if (inchikey := structures.get('inchikey')) is not None:
                if inchikey != '' and inchikey != 'InChIKey=none':
                    if inchikey.startswith('InChIKey='):
                        inchikey = inchikey[9:]
                    lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                        inchikey,
                        'inchikey',
                        source
                    ))

        # Fill swisslipids id
        if (identifier := entry.get('entity_id')) is not None:
            identifier: str
            lipid.add_database_identifier(DatabaseIdentifier.from_data(
                'swisslipids',
                identifier,
                source
            ))
        # Fill database cross reference attributes
        for reference in entry.get('xrefs'):
            if not isinstance(reference, dict):
                continue
            if reference.get('source') == 'ChEBI':
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'chebi',
                    reference.get('id'),
                    source
                ))
            elif reference.get('source') == 'LipidMaps':
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'lipidmaps',
                    reference.get('id'),
                    source
                ))
            elif reference.get('source') == "HMDB":
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'hmdb',
                    reference.get('id'),
                    source
                ))
            elif reference.get('source') == "MetaNetX":
                lipid.add_database_identifier(DatabaseIdentifier.from_data(
                    'metanetx',
                    reference.get('id'),
                    source
                ))

        # Fill mass values
        if (chemical_data := entry.get('chemical_data')) is not None:
            chemical_data: dict

            # Fill lipid mass values
            if (mass := chemical_data.get('mass')) is not None:
                lipid.add_mass(Mass.from_data(
                    'mass',
                    mass,
                    source
                ))

            if (mz_data := chemical_data.get('mz')) is not None and mz_data:
                mz_data: dict

                if (mass := mz_data.get('[M.]+')) is not None:
                    lipid.add_mass(Mass.from_data(
                        'mass_without_adduct',
                        mass,
                        source
                    ))

                if (mass := mz_data.get('exact mass')) is not None:
                    lipid.add_mass(Mass.from_data(
                        'exact_mass',
                        mass,
                        source
                    ))

                # Fill adduct mass values
                for adduct_name, mass in mz_data.items():
                    if adduct_name != '[M.]+' and adduct_name != 'exact mass':
                        adduct = copy.deepcopy(get_adduct(adduct_name))
                        if adduct is not None:
                            adduct.add_mass(Mass.from_data(
                                'mass',
                                float(mass),
                                source
                            ))
                            lipid.add_adduct(adduct)

        # Fill reactions
        if (reactions := entry.get('reactions')) is not None:
            reactions: dict
            for reaction_id in reactions:
                reaction = Reaction()
                reaction.add_database_identifier(DatabaseIdentifier.from_data(
                    'swisslipids',
                    reaction_id,
                    source
                ))

                if (reaction_info := reactions.get(reaction_id).get('reaction')) is not None:
                    if (rhea_info := reaction_info.get('rhea')) is not None:
                        reaction.add_database_identifier(DatabaseIdentifier.from_data(
                            'rhea',
                            rhea_info.get('rhea_id'),
                            source
                        ))
                        if (rhea_direction := rhea_info.get('rhea_direction')) is not None:
                            reaction.direction = rhea_direction
                        else:
                            reaction.direction = '='
                        substrates = rhea_info.get('rhea_reactants')
                        for substrate in substrates.values():
                            reaction.substrates.add(re.sub(r"<.*>", '', substrate.get('name')))
                        products = rhea_info.get('rhea_products')
                        for product in products.values():
                            reaction.products.add(re.sub(r"<[A-Za-z]*>", '', product.get('name')))

                if (enzyme_info := reactions.get(reaction_id).get('enzymes')) is not None:
                    for enzyme in enzyme_info:
                        reaction.add_database_identifier(DatabaseIdentifier.from_data(
                            'uniprotkb',
                            enzyme.get('enzyme_uniprotkb_id'),
                            source
                        ))

                lipid.add_reaction(reaction)

        return lipid
