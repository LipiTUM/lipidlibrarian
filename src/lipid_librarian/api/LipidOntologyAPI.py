import itertools
import logging
from importlib.resources import files

import networkx as nx
import pandas as pd

from .LipidAPI import LipidAPI
from ..lipid.Lipid import DatabaseIdentifier
from ..lipid.Lipid import Lipid
from ..lipid.Lipid import OntologyTerm
from ..lipid.Nomenclature import Level
from ..lipid.Source import Source


class LipidOntologyAPI(LipidAPI):

    def __init__(self):
        logging.info(f"LipidOntologyAPI: Initializing LipidOntology API...")
        super().__init__()

        self.lion_graph: nx.DiGraph | None = None
        self.lion_association: pd.DataFrame | None = None

        lion_edgelist_path = str(files('lipid_librarian')) + '/data/lipid_ontology/lion_graph.tsv'
        lion_association_path = str(files('lipid_librarian')) + '/data/lipid_ontology/lion_association.tsv'

        try:
            graph_edgelist = pd.read_csv(
                lion_edgelist_path,
                sep='\t',
                header=None
            )
            self.lion_association = pd.read_csv(
                lion_association_path,
                sep='\t',
                header=None,
                names=['lipid', 'term']
            )
        except FileNotFoundError as _:
            logging.error((
                f"LipidOntologyAPI: LipidOntology association and graph data not found. "
                f"Ontology annotation deactivated."
            ))
            graph_edgelist = None

        if graph_edgelist is not None:
            self.lion_graph = nx.DiGraph()
            self.lion_graph.add_edges_from(list(graph_edgelist.to_records(index=False)))
            logging.info(f"LipidOntologyAPI: Initializing LipidOntology API done.")

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        results = []

        # Check for structural_lipid_species
        if (structural_lipid_species_name := lipid.nomenclature.get_name(
                level=Level.structural_lipid_species,
                nomenclature_flavor='lipidmaps')
        ) is not None:
            ontology_terms = self.get_lipid_ontology_terms(structural_lipid_species_name)
            for ontology_term in ontology_terms:
                results.append(OntologyTerm.from_data(
                    ontology_term,
                    self.get_lipid_ontology_subgraph({ontology_term}),
                    Source(
                        structural_lipid_species_name,
                        Level.structural_lipid_species,
                        'lion'
                    )
                ))

        # Check for sum_lipid_species
        if (sum_lipid_species_name := lipid.nomenclature.get_name(
                level=Level.sum_lipid_species,
                nomenclature_flavor='lipidmaps')
        ) is not None:
            ontology_terms = self.get_lipid_ontology_terms(sum_lipid_species_name)
            for ontology_term in ontology_terms:
                results.append(OntologyTerm.from_data(
                    ontology_term,
                    self.get_lipid_ontology_subgraph({ontology_term}),
                    Source(
                        sum_lipid_species_name,
                        Level.sum_lipid_species,
                        'lion'
                    )
                ))

        # Check for lipidmaps identifiers
        for lipidmaps_identifier in lipid.get_database_identifiers('lipidmaps'):
            lipidmaps_identifier: DatabaseIdentifier
            ontology_terms = self.get_lipid_ontology_terms(lipidmaps_identifier.identifier)
            for ontology_term in ontology_terms:
                results.append(OntologyTerm.from_data(
                    ontology_term,
                    self.get_lipid_ontology_subgraph({ontology_term}),
                    Source(
                        list(lipidmaps_identifier.sources)[0].lipid_name,
                        list(lipidmaps_identifier.sources)[0].lipid_level,
                        'lion'
                    )
                ))

        # Check for swisslipids identifiers
        for swisslipids_identifier in lipid.get_database_identifiers('swisslipids'):
            swisslipids_identifier: DatabaseIdentifier
            ontology_terms = self.get_lipid_ontology_terms(swisslipids_identifier.identifier)
            for ontology_term in ontology_terms:
                results.append(OntologyTerm.from_data(
                    ontology_term,
                    self.get_lipid_ontology_subgraph({ontology_term}),
                    Source(
                        list(swisslipids_identifier.sources)[0].lipid_name,
                        list(swisslipids_identifier.sources)[0].lipid_level,
                        'lion'
                    )
                ))

        lipid.add_ontology_terms(results)
        return [lipid]

    def get_lipid_ontology_terms(self, lipid_name: str) -> list[str]:
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

    def get_lipid_ontology_subgraph(self, ontology_terms: set[str]) -> list[tuple[str, str]]:
        """
        Return the subgraph of the lipid ontology graph containing all paths leading
        from the root node to the specified terms.

        Parameters
        ----------
        ontology_terms : set[str]
            The ontology terms as strings of which the subgraph should be calculated of.

        Returns
        -------
        nx.DiGraph
            The desired subgraph as networkx directed graph object.
        """
        nodes: set[str] = set()
        for term in ontology_terms:
            nodes.update(set(itertools.chain(*nx.all_simple_paths(self.lion_graph, source='root', target=term))))
        return nx.to_edgelist(self.lion_graph, nodelist=nodes)
