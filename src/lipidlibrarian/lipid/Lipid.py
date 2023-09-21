import logging
from typing import Iterable

import json2html
import jsons

from .Mass import Mass
from .DatabaseIdentifier import DatabaseIdentifier
from .Ontology import Ontology
from .Adduct import Adduct
from .Nomenclature import Nomenclature
from .Reaction import Reaction
from .Source import Source


class Lipid():

    def __init__(self):
        self._query: str | None = None  # query_string for output formatting
        self._log_messages: list[tuple[int, str, str]] = []  # timestamp, action, value
        self.nomenclature: Nomenclature = Nomenclature()
        self.database_identifiers: list[DatabaseIdentifier] = []
        self.masses: list[Mass] = []
        self.ontology: Ontology = Ontology()
        self.reactions: list[Reaction] = []
        self.adducts: list[Adduct] = []

    @property
    def sources(self) -> set[Source]:
        sources: set[Source] = set()
        for database_identifier in self.database_identifiers:
            sources.update(database_identifier.sources)
        for mass in self.masses:
            sources.update(mass.sources)
        for reaction in self.reactions:
            sources.update(reaction.sources)
        for adduct in self.adducts:
            sources.update(adduct.sources)
        sources.update(self.nomenclature.sources)
        sources.update(self.ontology.sources)
        return sources

    def get_database_identifiers(self, database: str) -> list[DatabaseIdentifier]:
        results = []
        for database_identifier in self.database_identifiers:
            if database_identifier.database == database:
                results.append(database_identifier)
        return results

    def add_reaction(self, reaction: Reaction) -> None:
        for existing_reaction in self.reactions:
            if existing_reaction.merge(reaction):
                return
        self.reactions.append(reaction)

    def add_reactions(self, reactions: Iterable[Reaction]) -> None:
        for reaction in reactions:
            self.add_reaction(reaction)
    
    def add_adduct(self, adduct: Adduct) -> None:
        for existing_adduct in self.adducts:
            if existing_adduct.merge(adduct):
                return
        self.adducts.append(adduct)

    def add_adducts(self, adducts: Iterable[Adduct]) -> None:
        for adduct in adducts:
            self.add_adduct(adduct)

    def add_log_message(self, log_message: tuple[int, str, str]) -> None:
        self._log_messages.append(log_message)

    def add_log_messages(self, log_messages: Iterable[tuple[int, str, str]]) -> None:
        for log_message in log_messages:
            self.add_log_message(log_message)

    def add_database_identifier(self, database_identifier: DatabaseIdentifier) -> None:
        for existing_database_identifier in self.database_identifiers:
            if existing_database_identifier.merge(database_identifier):
                return
        self.database_identifiers.append(database_identifier)

    def add_database_identifiers(self, database_identifiers: Iterable[DatabaseIdentifier]) -> None:
        for database_identifier in database_identifiers:
            self.add_database_identifier(database_identifier)

    def add_mass(self, mass: Mass) -> None:
        for existing_mass in self.masses:
            if existing_mass.merge(mass):
                return
        self.masses.append(mass)

    def add_masses(self, masses: Iterable[Mass]) -> None:
        for mass in masses:
            self.add_mass(mass)

    def merge(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise ValueError((
                f"Source and target cannot be merged, since they do not inherit from the same instance: "
                f"{type(self)} and {type(other)}."
            ))

        if not self.nomenclature.merge(other.nomenclature):
            return False
        
        logging.info(f"Lipid: Merging Lipids {self.nomenclature.get_name()} and {other.nomenclature.get_name()}.")

        self.ontology.merge(other.ontology)

        self.add_log_messages(other._log_messages)
        self.add_database_identifiers(other.database_identifiers)
        self.add_masses(other.masses)
        self.add_reactions(other.reactions)
        self.add_adducts(other.adducts)

        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return self.nomenclature.get_name()

    def __format__(self, format_spec):
        name = self.nomenclature.get_name()
        if name is None or name == "":
            name = self._query
        if format_spec == 'json':
            return jsons.dumps(self, indent="\t")
        if format_spec == 'html':
            return "<h1>" + "Lipid: " + name + "</h1>" + json2html.json2html.convert(json=format(self, 'json'))
        else:
            return str(self.__dict__)
