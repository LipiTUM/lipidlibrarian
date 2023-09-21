from dataclasses import dataclass

from .Level import Level


@dataclass(frozen=True)
class Source():

    lipid_name: str
    lipid_level: Level
    source: str
