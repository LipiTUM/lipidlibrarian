import logging
from importlib.resources import files

import networkx
import pandas as pd
import obonet

from .LipidAPI import LipidAPI
from ..lipid.Lipid import DatabaseIdentifier
from ..lipid.Lipid import Lipid
from ..lipid.Nomenclature import Level
from ..lipid.Source import Source


class LionAPI(LipidAPI):

    def __init__(self):
        logging.info(f"LionAPI: Initializing LION API...")
        super().__init__()

        self.lion_graph: networkx.MultiDiGraph | None = None
        self.lion_association: pd.DataFrame | None = None

        lion_graph_path = str(files('lipidlibrarian')) + '/data/lion/lion_ontology_graph.obo'
        lion_association_path = str(files('lipidlibrarian')) + '/data/lion/lion_association_table.tsv'

        try:
            self.lion_graph = obonet.read_obo(
                lion_graph_path,
            )
            logging.info(f"LionAPI: Ontology Graph contains {self.lion_graph.number_of_nodes()} nodes and {self.lion_graph.number_of_edges()} edges.")
            self.lion_association = pd.read_csv(
                lion_association_path,
                sep='\t',
                header=None,
                names=['lipid', 'term']
            )
            logging.info(f"LionAPI: Ontology Association contains {len(self.lion_association)} associations.")
            logging.info(f"LionAPI: Initializing LION API done.")
        except FileNotFoundError as _:
            self.lion_graph = None
            self.lion_association = None
            logging.error((
                f"LionAPI: LION association and/or graph data not found. "
                f"LION annotation deactivated."
            ))

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        if self.lion_graph is None or self.lion_association is None:
            return [lipid]

        # Check for structural_lipid_species
        if (structural_lipid_species_name := lipid.nomenclature.get_name(
                level=Level.structural_lipid_species,
                nomenclature_flavor='lipidmaps')
        ) is not None:
            ontology_terms = self.get_lion_terms(structural_lipid_species_name)
            lipid.ontology.ontology_terms.update(ontology_terms)
            lipid.ontology.add_source(Source(
                structural_lipid_species_name,
                Level.structural_lipid_species,
                'lion'
            ))

        # Check for sum_lipid_species
        if (sum_lipid_species_name := lipid.nomenclature.get_name(
                level=Level.sum_lipid_species,
                nomenclature_flavor='lipidmaps')
        ) is not None:
            ontology_terms = self.get_lion_terms(sum_lipid_species_name)
            lipid.ontology.ontology_terms.update(ontology_terms)
            lipid.ontology.add_source(Source(
                sum_lipid_species_name,
                Level.sum_lipid_species,
                'lion'
            ))

        # Check for lipidmaps identifiers
        for lipidmaps_identifier in lipid.get_database_identifiers('lipidmaps'):
            lipidmaps_identifier: DatabaseIdentifier
            ontology_terms = self.get_lion_terms(lipidmaps_identifier.identifier)
            lipid.ontology.ontology_terms.update(ontology_terms)
            lipid.ontology.add_source(Source(
                list(lipidmaps_identifier.sources)[0].lipid_name,
                list(lipidmaps_identifier.sources)[0].lipid_level,
                'lion'
            ))

        # Check for swisslipids identifiers
        for swisslipids_identifier in lipid.get_database_identifiers('swisslipids'):
            swisslipids_identifier: DatabaseIdentifier
            ontology_terms = self.get_lion_terms(swisslipids_identifier.identifier)
            lipid.ontology.ontology_terms.update(ontology_terms)
            lipid.ontology.add_source(Source(
                list(swisslipids_identifier.sources)[0].lipid_name,
                list(swisslipids_identifier.sources)[0].lipid_level,
                'lion'
            ))

        return [lipid]

    def get_lion_terms(self, lipid_name: str) -> list[str]:
        """
        Return the lipid ontology terms associated with a lipid.

        Parameters
        ----------
        lipid_name : str
            The lipid name with which the lipid ontology association table is queried.

        Returns
        -------
        list[str]
            All the lipid ontology terms the ``lipid_name`` is associated with.
        """
        terms = self.lion_association[self.lion_association['lipid'] == lipid_name]
        return terms['term'].to_list()

    def get_lion_ancestor_nodes(self, ontology_terms: set[str]) -> set[str]:
        """
        Return the subgraph of the lipid ontology graph containing all paths leading
        from the root node to the specified terms.

        Parameters
        ----------
        ontology_terms : set[str]
            The ontology terms as strings of which the subgraph should be calculated of.

        Returns
        -------
        list[str, str]
            The desired subgraph as edgelist.
        """
        if self.lion_graph is None:
            return set()

        nodes: set[str] = set()
        for term in ontology_terms:
            nodes.update(networkx.descendants(self.lion_graph, term) | {'root'})
        return set(self.lion_graph.subgraph(nodes).nodes)
    
    def get_lion_subgraph_edgelist(self, ontology_terms: set[str]) -> list[tuple[str, str]]:
        """
        Return the subgraph of the lipid ontology graph containing all paths leading
        from the root node to the specified terms.

        Parameters
        ----------
        ontology_terms : set[str]
            The ontology terms as strings of which the subgraph should be calculated of.

        Returns
        -------
        list[str, str]
            The desired subgraph as edgelist.
        """
        if self.lion_graph is None:
            return []

        return networkx.to_edgelist(self.lion_graph.subgraph(self.get_lion_ancestor_nodes(ontology_terms)))

    def get_lion_node_data(self, ontology_terms: set[str]) -> dict[str, any]:
        """
        Return the data contained in nodes from the ontology graph.

        Parameters
        ----------
        ontology_terms : set[str]
            The ids, which are the ontology terms as strings ,of the desired nodes.

        Returns
        -------
        dict[str, any]
            The data of all selected nodes.
        """
        if self.lion_graph is None:
            return []

        return {name: data for name, data in self.lion_graph.subgraph(self.get_lion_ancestor_nodes(ontology_terms)).nodes.data()}