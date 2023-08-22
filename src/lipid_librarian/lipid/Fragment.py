from typing import Iterable

from .Mass import Mass
from .Source import Source


class Fragment():

    def __init__(self):
        self.name: str | None = None
        self.masses: list[Mass] = []
        self.sum_formula: str | None = None

    @property
    def sources(self) -> set[Source]:
        sources: set[Source] = set()
        for mass in self.masses:
            sources.update(mass.sources)
        return sources

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
    
        if self.sum_formula != other.sum_formula:
            return False

        self.add_masses(other.masses)
        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f"{self.name}"
