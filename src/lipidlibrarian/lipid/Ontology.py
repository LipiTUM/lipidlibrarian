from collections.abc import Iterable

from .Source import Source


class Ontology():

    def __init__(self) -> None:
        self.ontology_terms: set[str] = set()
        self.sources: set[Source] = set()

    @property
    def ontology_subgraph(self) -> list[tuple[str, str]]:
        try:
            # circular dependency: lazy import
            from ..api import lion_API
            return lion_API.get_lion_subgraph_edgelist(self.ontology_terms)
        except AttributeError:
            return []

    @property
    def ontology_subgraph_node_data(self) -> dict[str, any]:
        try:
            # circular dependency: lazy import
            from ..api import lion_API
            return lion_API.get_lion_node_data(self.ontology_terms)
        except AttributeError:
            return {}

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
    
        self.ontology_terms.update(other.ontology_terms)
        self.add_sources(other.sources)
        return True

    def __repr__(self) -> str:
        return self.ontology_terms
