import bz2
import logging
import pickle
from importlib.metadata import version
from importlib.resources import files
from typing import Any

from .LipidAPI import LipidAPI
from ..lipid.Lipid import Lipid
from ..lipid.Nomenclature import Level
from ..lipid.Reaction import Reaction
from ..lipid.DatabaseIdentifier import DatabaseIdentifier
from ..lipid.Source import Source


def _load_reactions() -> tuple[dict[str, Any], list[Any]]:
    from linex2 import load_data
    from linex2 import utils
    from linex2 import make_all_reaction_list_from_reactome
    from linex2 import make_all_reaction_list_from_rhea
    from linex2 import parse_lipid_reference_table_dict

    # First the reference lipid classes are generated.
    # This is a dictionary with lipid classes as keys, and a "Reference class" reactionect as value
    # We only have reactions available for lipids of these classes.
    reference_lipids = parse_lipid_reference_table_dict(load_data.STANDARD_LIPID_CLASSES)

    # Then we read the reactions we curated from the Rhea database
    # and the reactions from the Reactome database
    # (loading this takes a few seconds)
    rhea_reactions = make_all_reaction_list_from_rhea(
        load_data.RHEA_OTHERS_UNIQUE,
        load_data.RHEA_REACTION_CURATION,
        load_data.RHEA_REACTION_TO_MOLECULE,
        reference_lipids,
        load_data.RHEA_MAPPING,
        verbose=False
    )
    reactome_reactions = make_all_reaction_list_from_reactome(
        load_data.REACTOME_OTHERS_UNIQUE,
        load_data.REACTOME_REACTION_CURATION,
        load_data.REACTOME_REACTION_TO_MOLECULE,
        reference_lipids,
        load_data.REACTOME_REACTION_DETAILS,
        verbose=False
    )

    # Then we combine both reaction lists
    # This is the list (together with the reference lipids you will be working with)
    combined_reactions = utils.combine_reactions(reactome_reactions[0], rhea_reactions[0])

    return reference_lipids, combined_reactions


class LinexAPI(LipidAPI):

    def __init__(self):
        logging.info(f"LinexAPI: Initializing LINEX API...")
        super().__init__()

        self.reference_lipids: dict[str, Any] = {}
        self.combined_reactions: list[Any] = []

        # search installation path of lipidlibrarian and add /data/linex/linex_data.pbz2
        linex_data_path = str(files('lipidlibrarian')) + '/data/linex/linex_data.pbz2'

        linex_data: tuple[str, dict[str, Any], list[Any]] = ("", {}, [])
        try:
            linex_data = pickle.load(bz2.BZ2File(linex_data_path, "rb"))
            logging.info(f"LinexAPI: Cached LINEX reaction data found.")
        except FileNotFoundError as _:
            pass

        current_linex_version = version("linex2")
        if linex_data[0] != current_linex_version:
            logging.info(f"LinexAPI: Generating LINEX reaction data...")
            reference_lipids, combined_reactions = _load_reactions()
            linex_data = (current_linex_version, reference_lipids, combined_reactions)
            with bz2.BZ2File(linex_data_path, "w") as f:
                pickle.dump(linex_data, f)
            logging.info(f"LinexAPI: Generating LINEX reaction data done.")
        self.reference_lipids, self.combined_reactions = linex_data[1], linex_data[2]
        logging.info(f"LinexAPI: Initializing LINEX API done.")

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        lipid_class_name = lipid.nomenclature.lipid_class_abbreviation
        linex_reactions = self.query_lipid_class(lipid_class_name)
        for linex_reaction in linex_reactions:
            lipid.add_reaction(self._convert_reaction(
                linex_reaction,
                lipid.nomenclature.lipid_class_abbreviation,
                Level.lipid_class)
            )
        return [lipid]

    def query_lipid_class(self, lipid_class_name: str) -> list[Any]:
        logging.info(f"LinexAPI: Querying for reactions with lipid class {lipid_class_name}.")

        if lipid_class_name not in self.reference_lipids:
            logging.info(f"LinexAPI: Lipid class name not found: {lipid_class_name}.")
            return []

        results = []
        for linex_reaction in self.combined_reactions:
            if self.reference_lipids[lipid_class_name] in linex_reaction.get_substrates() or \
                    self.reference_lipids[lipid_class_name] in linex_reaction.get_products():
                results.append(linex_reaction)

        logging.info(f"LinexAPI: Found {len(results)} reactions for lipid class {lipid_class_name}.")
        return results

    @staticmethod
    def _convert_reaction(linex_reaction: Any, lipid_name: str, lipid_level: Level) -> Reaction:
        reaction = Reaction()
        source = Source(lipid_name, lipid_level, 'linex')

        reaction.direction = "="
        for product in linex_reaction.get_products():
            reaction.products.add(product.get_abbr())
        for substrate in linex_reaction.get_substrates():
            reaction.substrates.add(substrate.get_abbr())

        reaction.linex_reaction_type = linex_reaction.get_reaction_type()

        enzyme_identifiers = set(linex_reaction.get_enzyme_id().split(';'))
        for s in ('', 'nan', 'NaN', 'NAN'):
            try:
                enzyme_identifiers.remove(s)
            except KeyError as _:
                pass

        for enzyme_identifier in enzyme_identifiers:
            if enzyme_identifier.startswith('RHEA'):
                database = 'rhea'
            else:
                database = 'reactome'

            reaction.add_database_identifier(DatabaseIdentifier.from_data(
                database,
                enzyme_identifier,
                source
            ))

        gene_names = set(linex_reaction.get_gene_name().split(', '))
        for s in ('', 'nan', 'NaN', 'NAN'):
            try:
                gene_names.remove(s)
            except KeyError as _:
                pass

        uniprot_identifiers = set(linex_reaction.get_uniprot().split(', '))
        for s in ('', 'nan', 'NaN', 'NAN'):
            try:
                uniprot_identifiers.remove(s)
            except KeyError as _:
                pass
        for uniprot_identifier in uniprot_identifiers:
            reaction.add_database_identifier(DatabaseIdentifier.from_data(
                'uniprotkb',
                uniprot_identifier,
                source
            ))

        for gene_name in gene_names:
            reaction.gene_names.add((gene_name, frozenset()))

        linex_nl_participants = set(linex_reaction.get_nl_participants())
        for s in ('', 'nan', 'NaN', 'NAN'):
            try:
                linex_nl_participants.remove(s)
            except KeyError as _:
                pass

        reaction.linex_nl_participants = linex_nl_participants
        return reaction
