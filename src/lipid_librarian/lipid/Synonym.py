from typing import Iterable

from .Source import Source


class Synonym():

    def __init__(self) -> None:
        self.value: str | None = None
        self.synonym_type: str | None = None
        self.sources: set[Source] = set()

    @classmethod
    def from_data(cls, value: str, synonym_type: str, source: Source):
        obj = cls()
        obj.value = value
        obj.synonym_type = synonym_type
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

        if self.value != other.value and self.synonym_type != other.synonym_type:
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
        return f"{self.value}"
