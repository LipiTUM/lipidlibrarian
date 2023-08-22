from typing import Iterable

from .Source import Source


class Mass():

    def __init__(self) -> None:
        self.mass_type: str | None = None  # (monisotopic, neutral, average)
        self.value: float | None = None
        self.sources: set[Source] = set()

    @classmethod
    def from_data(cls, mass_type: str, value: float, source: Source):
        obj = cls()
        obj.mass_type = mass_type
        obj.value = value
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
    
        if self.mass_type != other.mass_type or self.value != other.value:
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
