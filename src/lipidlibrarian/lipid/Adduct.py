from typing import Iterable

from .Fragment import Fragment
from .Mass import Mass
from .Source import Source


class Adduct():

    def __init__(self):
        self.name: str | None = None
        self.swisslipids_name: str | None = None
        self.swisslipids_abbrev: str | None = None
        self.lipidmaps_name: str | None = None
        self.adduct_mass: float | None = None
        self.charge: int | None = None
        self.masses: list[Mass] = []
        self.fragments: list[Fragment] = []

    @property
    def sources(self) -> set[Source]:
        sources: set[Source] = set()
        for fragment in self.fragments:
            sources.update(fragment.sources)
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

    def add_fragment(self, fragment: Fragment) -> None:
        for existing_fragment in self.fragments:
            if existing_fragment.merge(fragment):
                return
        self.fragments.append(fragment)

    def add_fragments(self, fragments: list[Fragment]) -> None:
        for fragment in fragments:
            self.add_fragment(fragment)

    def merge(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise ValueError((
                f"Source and target cannot be merged, since they do not inherit from the same instance: "
                f"{type(self)} and {type(other)}."
            ))

        if self.name != other.name:
            return False

        self.add_fragments(other.fragments)
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
