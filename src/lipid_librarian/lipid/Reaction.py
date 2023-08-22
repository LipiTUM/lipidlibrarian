import logging
from typing import Iterable

from .Lipid import DatabaseIdentifier
from .Source import Source


class Reaction():

    def __init__(self):
        self.database_identifiers: list[DatabaseIdentifier] = []

        # Reaction description
        self.direction: str | None = None
        self.substrates: set[str] = set()
        self.products: set[str] = set()
        # One gene can be mapped to one or multiple reactions
        self.gene_names: set[tuple[str, frozenset[str]]] = set()

        # Linex only
        self.linex_reaction_type: str | None = None
        self.linex_nl_participants: set[str] = set()

    @property
    def description(self) -> str | None:
        if not self.substrates or not self.products:
            return None

        return (
            f"{' + '.join(self.substrates)} "
            f"{self.direction if self.direction is not None else '='} "
            f"{' + '.join(self.products)}"
        )

    @property
    def sources(self) -> set[Source]:
        sources: set[Source] = set()
        for database_identifier in self.database_identifiers:
            sources.update(database_identifier.sources)
        return sources

    def get_database_identifiers(self, database: str) -> list[DatabaseIdentifier]:
        results = []
        for database_identifier in self.database_identifiers:
            if database_identifier.database == database:
                results.append(database_identifier)
        return results

    def add_database_identifier(self, database_identifier: DatabaseIdentifier) -> None:
        for existing_database_identifier in self.database_identifiers:
            if existing_database_identifier.merge(database_identifier):
                return
        self.database_identifiers.append(database_identifier)

    def add_database_identifiers(self, database_identifiers: Iterable[DatabaseIdentifier]) -> None:
        for database_identifier in database_identifiers:
            self.add_database_identifier(database_identifier)

    def merge(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise ValueError((
                f"Source and target cannot be merged, since they do not inherit from the same instance: "
                f"{type(self)} and {type(other)}."
            ))

        if 'swisslipids' in self.sources and 'linex' in other.sources or 'linex' in self.sources and 'swisslipids' in other.sources:
            logging.warning('Reaction: Merging of swisslipids and linex reactions is not supported yet.')
            return False

        if self.linex_reaction_type is not None:
            if self.linex_reaction_type != other.linex_reaction_type or self.substrates != other.substrates or self.products != other.products:
                return False
        else:
            if self.description != other.description:
                return False

        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return self.description
