from typing import Iterable

from liputils import Lipid as LiputilsLipid
from pygoslin.domain.LipidLevel import LipidLevel

from . import goslin_convert
from . import lynx_convert
from . import lipid_name_conversion_methods
from .Level import Level
from .Source import Source
from .StructureIdentifier import StructureIdentifier
from .Synonym import Synonym


def _convert_level(s: str, level: Level) -> str | None:
    if 'goslin' in lipid_name_conversion_methods:
        return _goslin_convert_level(s, level)
    elif 'lipidlynxx' in lipid_name_conversion_methods:
        return _lynx_convert_level(s, level)
    else:
        raise ModuleNotFoundError((
            f"Neither goslin nor lipidlynxx are available. Lipid Level Conversion and thus the operation of "
            f"LipidLibrarian is not possible under these circumstances."
        ))


def _lynx_convert_level(s: str, level: Level) -> str | None:
    lynx_level = ""
    if level == Level.isomeric_lipid_species:
        lynx_level = 'S0.1'
    elif level == Level.structural_lipid_species:
        lynx_level = 'S0'
    elif level == Level.molecular_lipid_species:
        lynx_level = 'M0'
    elif level == Level.sum_lipid_species:
        lynx_level = 'B0'

    result = lynx_convert(s, level=lynx_level)
    return result


def _goslin_convert_level(s: str, level: Level) -> str | None:
    goslin_level = LipidLevel.UNDEFINED
    if level == Level.isomeric_lipid_species:
        goslin_level = LipidLevel.FULL_STRUCTURE
    elif level == Level.structural_lipid_species:
        goslin_level = LipidLevel.SN_POSITION
    elif level == Level.molecular_lipid_species:
        goslin_level = LipidLevel.MOLECULAR_SPECIES
    elif level == Level.sum_lipid_species:
        goslin_level = LipidLevel.SPECIES
    elif level == Level.lipid_class:
        goslin_level = LipidLevel.CLASS
    elif level == Level.lipid_category:
        goslin_level = LipidLevel.CATEGORY

    result = goslin_convert(s, level=goslin_level)
    return result


class Nomenclature():

    def __init__(self):
        self._query_name: str | None = None
        self._sum_lipid_species_name: str | None = None
        self._structural_lipid_species_name: str | None = None
        self._molecular_lipid_species_name: str | None = None
        self._isomeric_lipid_species_name: str | None = None
        self.lipid_category: str | None = None
        self.lipid_class: str | None = None
        self.sum_formula: str | None = None
        self.synonyms: list[Synonym] = []
        self.structure_identifiers: list[StructureIdentifier] = []

    @property
    def level(self) -> Level:
        if self._isomeric_lipid_species_name is not None:
            return Level.isomeric_lipid_species
        elif self._structural_lipid_species_name is not None:
            return Level.structural_lipid_species
        elif self._molecular_lipid_species_name is not None:
            return Level.molecular_lipid_species
        elif self._sum_lipid_species_name is not None:
            return Level.sum_lipid_species
        else:
            return Level.level_unknown

    @property
    def lipid_class_abbreviation(self) -> str | None:
        if self.get_name() is None:
            return None

        if 'goslin' in lipid_name_conversion_methods:
            return _goslin_convert_level(self.get_name(), level=Level.lipid_class)
        else:
            return LiputilsLipid(self.get_name()).refmet_class()

    @property
    def residues(self) -> list[str]:
        if self.get_name() is None:
            return []

        try:
            return LiputilsLipid(self.get_name()).refmet_residues()[0]
        except IndexError as _:
            pass
        return []

    @property
    def name(self) -> str | None:
        return self.get_name()

    def get_name(self, level: Level = None, nomenclature_flavor: str = 'swisslipids') -> str | None:
        if nomenclature_flavor not in ['alex123', 'lipidmaps', 'swisslipids']:
            raise ValueError((f"Unsupported nomenclature_flavor {nomenclature_flavor}. "
                              "Must be either 'alex123', 'lipidmaps', or 'swisslipids'."))

        result = None
        if level is None:
            if self.level == Level.isomeric_lipid_species:
                result = self._isomeric_lipid_species_name
            elif self.level == Level.structural_lipid_species:
                result = self._structural_lipid_species_name
            elif self.level == Level.molecular_lipid_species:
                result = self._molecular_lipid_species_name
            elif self.level == Level.sum_lipid_species:
                result = self._sum_lipid_species_name
            elif self.level == Level.level_unknown:
                result = self._query_name
        elif level == Level.isomeric_lipid_species and self.level >= Level.isomeric_lipid_species:
            result = self._isomeric_lipid_species_name
        elif level == Level.structural_lipid_species and self.level >= Level.structural_lipid_species:
            result = self._structural_lipid_species_name
        elif level == Level.molecular_lipid_species and self.level >= Level.molecular_lipid_species:
            result = self._molecular_lipid_species_name
        elif level == Level.sum_lipid_species and self.level >= Level.sum_lipid_species:
            result = self._sum_lipid_species_name
        elif level == Level.level_unknown:
            result = self._query_name

        if result is None:
            return ''

        if nomenclature_flavor == 'lipidmaps':
            if (lynx_result := lynx_convert(result)) is not None:
                result = lynx_result

        if nomenclature_flavor == 'alex123':
            result = result.replace('_', '-')

        return result

    @name.setter
    def name(self, s: str) -> None:
        self._query_name = s
        if (sum_lipid_species_name := _convert_level(s, level=Level.sum_lipid_species)) is not None:
            self._sum_lipid_species_name = sum_lipid_species_name
            self._molecular_lipid_species_name = _convert_level(s, level=Level.molecular_lipid_species)
            self._structural_lipid_species_name = _convert_level(s, level=Level.structural_lipid_species)
            self._isomeric_lipid_species_name = _convert_level(s, level=Level.isomeric_lipid_species)
        else:
            if (s_alternative := goslin_convert(s)) is not None:
                s = s_alternative
                self._sum_lipid_species_name = _convert_level(s, level=Level.sum_lipid_species)
                self._molecular_lipid_species_name = _convert_level(s, level=Level.molecular_lipid_species)
                self._structural_lipid_species_name = _convert_level(s, level=Level.structural_lipid_species)
                self._isomeric_lipid_species_name = _convert_level(s, level=Level.isomeric_lipid_species)

    @property
    def sources(self) -> set[Source]:
        sources: set[Source] = set()
        for synonym in self.synonyms:
            sources.update(synonym.sources)
        for structure_identifier in self.structure_identifiers:
            sources.update(structure_identifier.sources)
        return sources

    def add_synonym(self, synonym: Synonym) -> None:
        for existing_synonym in self.synonyms:
            if existing_synonym.merge(synonym):
                return
        self.synonyms.append(synonym)

    def add_synonyms(self, synonyms: Iterable[Synonym]) -> None:
        for synonym in synonyms:
            self.add_synonym(synonym)

    def add_structure_identifier(self, structure_identifier: StructureIdentifier) -> None:
        for existing_structure_identifier in self.structure_identifiers:
            if existing_structure_identifier.merge(structure_identifier):
                return
        self.structure_identifiers.append(structure_identifier)

    def add_structure_identifiers(self, structure_identifiers: Iterable[StructureIdentifier]) -> None:
        for structure_identifier in structure_identifiers:
            self.add_structure_identifier(structure_identifier)

    def merge(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise ValueError((
                f"Source and target cannot be merged, since they do not inherit from the same instance: "
                f"{type(self)} and {type(other)}."
            ))
        
        name_self = self.get_name()
        name_other = other.get_name()

        if name_self != name_other:
            return False
        
        # merge all non-calculated values
        self.lipid_category = other.lipid_category if self.lipid_category is None else self.lipid_category
        self.sum_formula = other.sum_formula if self.sum_formula is None else self.sum_formula
        self.add_synonyms(other.synonyms)
        self.add_structure_identifiers(other.structure_identifiers)
        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return self.name
