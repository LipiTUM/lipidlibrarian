from collections.abc import Iterable

from .Source import Source


class OntologyTerm():

    def __init__(self) -> None:
        self.ontology_term: str | None = None
        self.ontology_subgraph: list[tuple[str, str]] = []
        self.sources: set[Source] = set()

    @classmethod
    def from_data(cls, ontology_term: str, ontology_subgraph: list[tuple[str, str]], source: Source):
        obj = cls()
        obj.ontology_term = ontology_term
        obj.ontology_subgraph = ontology_subgraph
        obj.add_source(source)
        return obj

    def add_source(self, source: Source) -> None:
        self.sources.add(source)

    def add_sources(self, sources: Iterable[Source]) -> None:
        for source in sources:
            self.add_source(source)

    def merge(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise ValueError((
                f"Source and target cannot be merged, since they do not inherit from the same instance: "
                f"{type(self)} and {type(other)}."
            ))
    
        if self.ontology_term != other.ontology_term:
            return False
        
        self.add_sources(other.sources)
        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return self.ontology_term
